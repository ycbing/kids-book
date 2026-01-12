#!/bin/bash
# 健康检查脚本
# 文件: scripts/health-check.sh

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 服务列表
SERVICES=(
    "backend:Backend API:8000:/health"
    "frontend:Frontend:3000:/"
    "postgres:PostgreSQL:5432:-"
    "redis:Redis:6379:-"
    "celery-worker:Celery Worker:-:-"
    "flower:Flower Monitor:5555:/"
)

echo "========================================="
echo "   AI绘本创作平台 - 健康检查"
echo "========================================="
echo ""

# 检查Docker服务状态
check_docker_services() {
    echo "📦 Docker服务状态:"
    echo ""

    if ! docker ps &> /dev/null; then
        echo -e "${RED}❌ Docker未运行${NC}"
        return 1
    fi

    # 获取运行中的容器
    RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}")
    ALL_CONTAINERS=$(docker-compose ps -q | xargs docker inspect --format='{{.Name}}' 2>/dev/null | sed 's/\///')

    for service_info in "${SERVICES[@]}"; do
        IFS=':' read -r name display_name port _ <<< "$service_info"

        if echo "$RUNNING_CONTAINERS" | grep -q "picturebook-$name\|ai-picture-book-$name\|$name"; then
            echo -e "  ${GREEN}✓${NC} $display_name"
        else
            echo -e "  ${RED}✗${NC} $display_name (未运行)"
        fi
    done

    echo ""
}

# 检查HTTP端点
check_http_endpoints() {
    echo "🌐 HTTP端点检查:"
    echo ""

    # 后端健康检查
    echo -n "  Backend API (/health): "
    if curl -sf http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✓ 正常${NC}"
        response=$(curl -s http://localhost:8000/health)
        status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo "    状态: $status"
    else
        echo -e "${RED}✗ 异常${NC}"
    fi

    # 前端检查
    echo -n "  Frontend (/): "
    if curl -sf http://localhost:3000 &> /dev/null; then
        echo -e "${GREEN}✓ 正常${NC}"
    else
        echo -e "${YELLOW}⚠ 未运行或无响应${NC}"
    fi

    # API文档检查
    echo -n "  API Docs (/docs): "
    if curl -sf http://localhost:8000/docs &> /dev/null; then
        echo -e "${GREEN}✓ 正常${NC}"
    else
        echo -e "${YELLOW}⚠ 未运行或无响应${NC}"
    fi

    # Flower检查
    echo -n "  Flower (/): "
    if curl -sf http://localhost:5555 &> /dev/null; then
        echo -e "${GREEN}✓ 正常${NC}"
    else
        echo -e "${YELLOW}⚠ 未运行或无响应${NC}"
    fi

    echo ""
}

# 检查数据库连接
check_database() {
    echo "💾 数据库连接:"
    echo ""

    # PostgreSQL检查
    echo -n "  PostgreSQL: "
    if docker exec picturebook-db pg_isready -U picturebook &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ 正常${NC}"

        # 检查数据库大小
        db_size=$(docker exec picturebook-db psql -U picturebook -d picturebook -t -c "SELECT pg_size_pretty(pg_database_size('picturebook'));" | xargs)
        echo "    大小: $db_size"

        # 检查表数量
        table_count=$(docker exec picturebook-db psql -U picturebook -d picturebook -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)
        echo "    表数量: $table_count"
    else
        echo -e "${RED}✗ 异常${NC}"
    fi

    # Redis检查
    echo -n "  Redis: "
    if docker exec picturebook-redis redis-cli ping &> /dev/null 2>&1; then
        echo -e "${GREEN}✓ 正常${NC}"

        # Redis内存使用
        redis_memory=$(docker exec picturebook-redis redis-cli INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
        echo "    内存: $redis_memory"
    else
        echo -e "${RED}✗ 异常${NC}"
    fi

    echo ""
}

# 检查磁盘空间
check_disk_space() {
    echo "💽 磁盘空间:"
    echo ""

    df -h | grep -E "Filesystem|/$|/var$|/home$" | while read line; do
        echo "  $line"
    done

    echo ""
}

# 检查日志中的错误
check_logs() {
    echo "📋 最近错误日志:"
    echo ""

    # 后端错误
    backend_errors=$(docker-compose logs --tail=100 backend 2>&1 | grep -i "error\|exception\|failed" | tail -5)
    if [ -n "$backend_errors" ]; then
        echo "  Backend:"
        echo "$backend_errors" | sed 's/^/    /'
    else
        echo "  Backend: 无错误"
    fi

    # Celery错误
    celery_errors=$(docker-compose logs --tail=100 celery-worker 2>&1 | grep -i "error\|exception\|failed" | tail -5)
    if [ -n "$celery_errors" ]; then
        echo "  Celery:"
        echo "$celery_errors" | sed 's/^/    /'
    else
        echo "  Celery: 无错误"
    fi

    echo ""
}

# 显示系统信息
show_system_info() {
    echo "📊 系统信息:"
    echo ""

    # CPU使用率
    if command -v top &> /dev/null; then
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
        echo "  CPU使用率: ${cpu_usage}%"
    fi

    # 内存使用率
    if command -v free &> /dev/null; then
        mem_info=$(free -h | grep Mem)
        echo "  内存使用: $mem_info"
    fi

    # Docker统计
    if docker stats --no-stream &> /dev/null; then
        echo "  Docker容器资源使用:"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10 | sed 's/^/    /'
    fi

    echo ""
}

# 执行所有检查
check_docker_services
check_http_endpoints
check_database
check_disk_space
check_logs
show_system_info

echo "========================================="
echo "   健康检查完成"
echo "========================================="
