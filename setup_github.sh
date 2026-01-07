#!/bin/bash

# GitHub 仓库设置脚本
# 使用方法：
# 1. 在 GitHub 上创建新仓库
# 2. 复制仓库 URL
# 3. 运行此脚本: bash setup_github.sh <YOUR_REPO_URL>

echo "=========================================="
echo "AI Picture Book - GitHub 推送脚本"
echo "=========================================="

if [ -z "$1" ]; then
    echo "错误: 请提供 GitHub 仓库 URL"
    echo ""
    echo "使用方法:"
    echo "  bash setup_github.sh <YOUR_GITHUB_REPO_URL>"
    echo ""
    echo "示例:"
    echo "  bash setup_github.sh https://github.com/username/ai-picture-book.git"
    echo ""
    echo "步骤:"
    echo "1. 访问 https://github.com/new"
    echo "2. 创建新仓库（不要初始化 README）"
    echo "3. 复制仓库 URL"
    echo "4. 运行此脚本并提供 URL"
    exit 1
fi

REPO_URL=$1

echo ""
echo "仓库 URL: $REPO_URL"
echo ""
read -p "确认推送到此仓库? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 1
fi

echo ""
echo "正在添加远程仓库..."
git remote add origin $REPO_URL

if [ $? -ne 0 ]; then
    echo "远程仓库已存在，正在更新..."
    git remote set-url origin $REPO_URL
fi

echo ""
echo "正在推送到 GitHub..."
git push -u origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "成功推送到 GitHub!"
    echo "=========================================="
    echo ""
    echo "仓库地址: $REPO_URL"
    echo ""
else
    echo ""
    echo "推送失败，请检查:"
    echo "1. 仓库 URL 是否正确"
    echo "2. 是否有 GitHub 访问权限"
    echo "3. 是否配置了 SSH 密钥或个人访问令牌"
fi
