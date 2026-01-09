#!/bin/bash
# 监控服务快速启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=================================="
echo "    启动AI绘本平台监控服务栈"
echo -e "==================================${NC}"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查端口是否被占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  端口 $1 已被占用"
        read -p "是否继续? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_port 9090  # Prometheus
check_port 3001  # Grafana
check_port 9093  # Alertmanager

# 创建必要的目录
echo -e "${GREEN}📁 创建监控数据目录...${NC}"
mkdir -p monitoring/prometheus/alerts
mkdir -p monitoring/grafana/provisioning
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/alertmanager

# 启动监控服务栈
echo -e "${GREEN}🚀 启动监控服务栈...${NC}"
docker-compose -f docker-compose.monitoring.yml up -d

# 等待服务启动
echo -e "${GREEN}⏳ 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo -e "${GREEN}✅ 检查服务状态...${NC}"
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo -e "${GREEN}=================================="
echo "✅ 监控服务栈启动成功！"
echo -e "==================================${NC}"
echo ""
echo "📊 访问地址："
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana:    http://localhost:3001 (admin/admin)"
echo "  - Alertmanager: http://localhost:9093"
echo ""
echo "📖 查看文档："
echo "  - 监控指南: MONITORING_AND_ALERTING.md"
echo ""
echo "🔧 常用命令："
echo "  - 查看日志: docker-compose -f docker-compose.monitoring.yml logs -f"
echo "  - 停止服务: docker-compose -f docker-compose.monitoring.yml down"
echo "  - 重启服务: docker-compose -f docker-compose.monitoring.yml restart"
echo ""
