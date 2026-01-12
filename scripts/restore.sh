#!/bin/bash
# 数据库恢复脚本
# 文件: scripts/restore.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 配置
BACKUP_DIR="${BACKUP_DIR:-./backups/postgres}"
DB_CONTAINER_NAME="${DB_CONTAINER_NAME:-picturebook-db}"
DB_NAME="${DB_NAME:-picturebook}"
DB_USER="${DB_USER:-picturebook}"

# 检查参数
if [ -z "$1" ]; then
    log_error "使用方法: $0 <备份文件>"
    echo ""
    echo "示例:"
    echo "  $0 ./backups/postgres/picturebook_20240101_020000.sql.gz"
    echo ""
    echo "可用备份列表:"
    ls -lh "$BACKUP_DIR"/picturebook_*.sql.gz 2>/dev/null || log_warn "没有找到备份文件"
    exit 1
fi

BACKUP_FILE="$1"

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 显示恢复信息
log_warn "========================================="
log_warn "警告: 此操作将覆盖现有数据库！"
log_warn "========================================="
log_info "备份文件: $BACKUP_FILE"
log_info "数据库: $DB_NAME"
log_info "容器: $DB_CONTAINER_NAME"
echo ""
read -p "确认恢复? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    log_info "恢复操作已取消"
    exit 0
fi

# 检查容器是否运行
if ! docker ps | grep -q "$DB_CONTAINER_NAME"; then
    log_error "数据库容器 $DB_CONTAINER_NAME 不在运行"
    exit 1
fi

# 创建临时文件
TEMP_FILE="/tmp/restore_temp.sql"

# 解压备份文件
log_info "解压备份文件..."
gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"

if [ $? -ne 0 ]; then
    log_error "解压失败"
    rm -f "$TEMP_FILE"
    exit 1
fi

# 停止应用连接（可选）
log_info "停止应用服务..."
docker-compose stop backend celery-worker celery-beat 2>/dev/null || true

# 删除现有数据库
log_info "删除现有数据库..."
docker exec "$DB_CONTAINER_NAME" psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec "$DB_CONTAINER_NAME" psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

# 恢复数据库
log_info "恢复数据库..."
docker exec -i "$DB_CONTAINER_NAME" psql -U "$DB_USER" "$DB_NAME" < "$TEMP_FILE"

if [ $? -ne 0 ]; then
    log_error "数据库恢复失败"
    docker-compose start backend celery-worker celery-beat 2>/dev/null || true
    rm -f "$TEMP_FILE"
    exit 1
fi

# 清理临时文件
rm -f "$TEMP_FILE"

# 重启应用服务
log_info "重启应用服务..."
docker-compose start backend celery-worker celery-beat 2>/dev/null || true

# 等待服务启动
sleep 5

# 验证恢复
log_info "验证恢复结果..."
TABLE_COUNT=$(docker exec "$DB_CONTAINER_NAME" psql -U "$DB_USER" "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")

log_info "数据库恢复成功！"
log_info "表数量: $TABLE_COUNT"
log_info "恢复完成"
