#!/bin/bash
# 生产环境部署脚本
# 文件: scripts/deploy.sh

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    log_info "检查Docker环境..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    log_info "Docker环境检查通过 ✓"
}

# 备份数据
backup_data() {
    log_info "备份数据..."
    BACKUP_DIR="./backups/pre-deploy-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 备份数据库
    if [ -f "./data/picturebook.db" ]; then
        cp ./data/picturebook.db "$BACKUP_DIR/"
        log_info "数据库备份完成: $BACKUP_DIR/picturebook.db"
    fi

    # 备份环境变量
    if [ -f "./.env" ]; then
        cp ./.env "$BACKUP_DIR/"
        log_info "环境变量备份完成: $BACKUP_DIR/.env"
    fi

    log_info "数据备份完成: $BACKUP_DIR"
}

# 拉取最新代码
pull_code() {
    log_info "拉取最新代码..."
    git pull origin main
    log_info "代码更新完成 ✓"
}

# 检查环境变量
check_env() {
    log_info "检查环境变量..."
    if [ ! -f "./.env" ]; then
        log_warn ".env文件不存在，从模板创建..."
        cp .env.example .env
        log_error "请编辑.env文件配置必要的环境变量后重新运行"
        exit 1
    fi
    log_info "环境变量检查通过 ✓"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    docker-compose build --no-cache
    log_info "镜像构建完成 ✓"
}

# 停止旧服务
stop_services() {
    log_info "停止旧服务..."
    docker-compose down
    log_info "服务已停止 ✓"
}

# 启动新服务
start_services() {
    log_info "启动新服务..."
    docker-compose up -d
    log_info "服务启动完成 ✓"
}

# 等待服务健康
wait_for_health() {
    log_info "等待服务健康检查..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_info "服务健康检查通过 ✓"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log_error "服务健康检查失败，请查看日志"
    docker-compose logs --tail=50
    exit 1
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose ps
}

# 显示日志
show_logs() {
    log_info "最近日志:"
    docker-compose logs --tail=20
}

# 清理旧镜像
cleanup_images() {
    log_info "清理旧的Docker镜像..."
    docker image prune -f
    log_info "清理完成 ✓"
}

# 主函数
main() {
    log_info "========================================="
    log_info "    AI绘本创作平台 - 生产环境部署"
    log_info "========================================="

    # 解析参数
    SKIP_BACKUP=false
    SKIP_BUILD=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --help)
                echo "使用方法: $0 [选项]"
                echo "选项:"
                echo "  --skip-backup  跳过数据备份"
                echo "  --skip-build   跳过镜像构建"
                echo "  --help         显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    # 执行部署步骤
    check_docker

    if [ "$SKIP_BACKUP" = false ]; then
        backup_data
    else
        log_warn "跳过数据备份"
    fi

    pull_code
    check_env

    if [ "$SKIP_BUILD" = false ]; then
        build_images
    else
        log_warn "跳过镜像构建"
    fi

    stop_services
    start_services
    wait_for_health
    show_status
    show_logs
    cleanup_images

    log_info "========================================="
    log_info "    部署完成！"
    log_info "========================================="
    log_info "访问地址:"
    log_info "  - 前端: http://localhost:3000"
    log_info "  - 后端API: http://localhost:8000"
    log_info "  - API文档: http://localhost:8000/docs"
    log_info "  - Flower监控: http://localhost:5555"
}

# 执行主函数
main "$@"
