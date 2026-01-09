#!/bin/bash
# 前端依赖管理脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查Node和npm版本
check_versions() {
    print_info "检查Node和npm版本..."

    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    NPM_VERSION=$(npm -v | cut -d'.' -f1)

    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node版本过低: v$NODE_VERSION (需要 >= 18.0.0)"
        exit 1
    fi

    if [ "$NPM_VERSION" -lt 9 ]; then
        print_error "npm版本过低: v$NPM_VERSION (需要 >= 9.0.0)"
        exit 1
    fi

    print_success "Node版本: $(node -v)"
    print_success "npm版本: $(npm -v)"
}

# 检查过时的依赖
check_outdated() {
    print_info "检查过时的依赖..."
    npm outdated --long=false || true
}

# 运行安全审计
audit_deps() {
    print_info "运行安全审计..."

    # 先尝试自动修复
    print_info "尝试自动修复安全漏洞..."
    npm audit fix || true

    # 检查是否还有高危漏洞
    print_info "检查剩余的安全漏洞..."
    audit_output=$(npm audit --audit-level=high --json 2>/dev/null || echo "{}")

    # 使用jq解析JSON，如果没有jq则跳过
    if command -v jq &> /dev/null; then
        vuln_count=$(echo "$audit_output" | jq '.metadata.vulnerabilities.high // 0')

        if [ "$vuln_count" -gt 0 ]; then
            print_warning "发现 $vuln_count 个高危漏洞"
            print_info "请手动运行 'npm audit' 查看详情"
        else
            print_success "未发现高危漏洞"
        fi
    else
        print_info "安装jq以获取详细分析: apt-get install jq / brew install jq"
    fi
}

# 更新依赖
update_deps() {
    print_info "更新依赖..."

    # 检查是否有可用更新
    print_info "检查可用的依赖更新..."
    if command -v npx &> /dev/null; then
        npx npm-check-updates -u || print_warning "npm-check-updates检查失败，继续使用常规更新..."
    fi

    # 更新依赖
    print_info "执行npm update..."
    npm update

    # 再次尝试修复安全漏洞
    npm audit fix || true

    print_success "依赖更新完成"
    print_info "请检查package.json的变化并测试应用"
}

# 清理依赖
clean_deps() {
    print_info "清理node_modules和package-lock.json..."

    read -p "确定要删除node_modules和package-lock.json吗？(y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf node_modules package-lock.json
        print_success "清理完成"
        print_info "运行 'npm install' 重新安装依赖"
    else
        print_info "取消清理"
    fi
}

# 主菜单
show_menu() {
    echo ""
    echo "=================================="
    echo "   前端依赖管理工具"
    echo "=================================="
    echo "1. 检查Node和npm版本"
    echo "2. 检查过时的依赖"
    echo "3. 运行安全审计"
    echo "4. 更新依赖"
    echo "5. 清理依赖"
    echo "6. 全部检查（版本+过时+审计）"
    echo "0. 退出"
    echo "=================================="
    read -p "请选择操作 [0-6]: " choice

    case $choice in
        1) check_versions ;;
        2) check_outdated ;;
        3) audit_deps ;;
        4) update_deps ;;
        5) clean_deps ;;
        6)
            check_versions
            echo ""
            check_outdated
            echo ""
            audit_deps
            ;;
        0) exit 0 ;;
        *) print_error "无效选择" ;;
    esac
}

# 如果提供了命令行参数，执行对应的操作
if [ $# -gt 0 ]; then
    case $1 in
        check-versions) check_versions ;;
        check-outdated) check_outdated ;;
        audit) audit_deps ;;
        update) update_deps ;;
        clean) clean_deps ;;
        all)
            check_versions
            echo ""
            check_outdated
            echo ""
            audit_deps
            ;;
        *)
            echo "用法: $0 [check-versions|check-outdated|audit|update|clean|all]"
            exit 1
            ;;
    esac
else
    # 否则显示交互式菜单
    while true; do
        show_menu
        echo ""
        read -p "按Enter键继续..." dummy
        clear
    done
fi
