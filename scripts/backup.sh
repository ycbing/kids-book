#!/bin/bash
# 数据库备份脚本
# 文件: scripts/backup.sh

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
RETENTION_DAYS=${RETENTION_DAYS:-30}
DB_CONTAINER_NAME="${DB_CONTAINER_NAME:-picturebook-db}"
DB_NAME="${DB_NAME:-picturebook}"
DB_USER="${DB_USER:-picturebook}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份文件名
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/picturebook_$DATE.sql.gz"
TEMP_BACKUP="/tmp/picturebook_temp_$DATE.sql"

log_info "开始备份数据库..."
log_info "备份文件: $BACKUP_FILE"

# 检查容器是否存在
if ! docker ps | grep -q "$DB_CONTAINER_NAME"; then
    log_error "数据库容器 $DB_CONTAINER_NAME 不在运行"
    exit 1
fi

# 执行备份
log_info "正在执行数据库转储..."
docker exec "$DB_CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" > "$TEMP_BACKUP"

if [ $? -ne 0 ]; then
    log_error "数据库转储失败"
    rm -f "$TEMP_BACKUP"
    exit 1
fi

# 压缩备份文件
log_info "正在压缩备份文件..."
gzip -c "$TEMP_BACKUP" > "$BACKUP_FILE"
rm -f "$TEMP_BACKUP"

# 验证备份文件
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "备份文件创建失败"
    exit 1
fi

# 获取文件大小
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log_info "备份完成: $BACKUP_FILE ($FILE_SIZE)"

# 清理旧备份
log_info "清理超过 $RETENTION_DAYS 天的旧备份..."
find "$BACKUP_DIR" -name "picturebook_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# 显示当前备份列表
log_info "当前备份列表:"
ls -lh "$BACKUP_DIR"/picturebook_*.sql.gz 2>/dev/null || log_warn "没有找到备份文件"

log_info "备份任务完成"

# 同时备份上传文件
log_info "备份上传文件..."
UPLOAD_BACKUP_DIR="$BACKUP_DIR/uploads_$DATE"
mkdir -p "$UPLOAD_BACKUP_DIR"

if [ -d "./uploads" ]; then
    rsync -av --delete ./uploads/ "$UPLOAD_BACKUP_DIR/"
    log_info "上传文件备份完成: $UPLOAD_BACKUP_DIR"
else
    log_warn "uploads目录不存在，跳过"
fi

log_info "所有备份任务完成"
