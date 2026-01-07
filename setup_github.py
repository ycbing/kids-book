#!/usr/bin/env python3
"""
GitHub 推向导
在 GitHub 上创建新仓库后，使用此脚本推送代码
"""
import subprocess
import sys

def run_command(cmd, description=""):
    """执行命令并显示输出"""
    if description:
        print(f"\n{description}")
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0

def main():
    print("=" * 60)
    print("AI Picture Book - GitHub 推送向导")
    print("=" * 60)

    print("\n请按以下步骤操作:")
    print("1. 访问 https://github.com/new")
    print("2. 创建新仓库（Repository name: ai-picture-book）")
    print("3. ⚠️  不要勾选 'Add a README file'")
    print("4. 点击 'Create repository'")
    print("5. 复制仓库的 HTTPS 或 SSH URL")

    repo_url = input("\n请粘贴您的 GitHub 仓库 URL: ").strip()

    if not repo_url:
        print("\n错误: 仓库 URL 不能为空")
        sys.exit(1)

    print(f"\n仓库 URL: {repo_url}")
    confirm = input("确认推送到此仓库? (y/n): ").strip().lower()

    if confirm != 'y':
        print("已取消")
        sys.exit(0)

    # 添加远程仓库
    print("\n" + "=" * 60)
    print("步骤 1/2: 添加远程仓库")
    print("=" * 60)

    # 检查是否已存在 origin
    result = subprocess.run(
        "git remote get-url origin",
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"远程仓库 'origin' 已存在: {result.stdout.strip()}")
        cmd = f"git remote set-url origin {repo_url}"
    else:
        cmd = f"git remote add origin {repo_url}"

    if not run_command(cmd, "正在设置远程仓库..."):
        print("\n错误: 无法设置远程仓库")
        sys.exit(1)

    print("✓ 远程仓库设置成功")

    # 推送到 GitHub
    print("\n" + "=" * 60)
    print("步骤 2/2: 推送代码到 GitHub")
    print("=" * 60)

    cmd = f"git push -u origin master"
    print(f"正在推送... (这可能需要一些时间)")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=False,
        text=True
    )

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ 成功推送到 GitHub!")
        print("=" * 60)
        print(f"\n仓库地址: {repo_url}")
        print("\n下一步:")
        print("1. 访问仓库查看代码")
        print("2. 在 GitHub 上编辑仓库描述和主题")
        print("3. 添加 README.md 的徽章和截图")
        print("4. 设置 GitHub Pages (如果需要)")
    else:
        print("\n" + "=" * 60)
        print("✗ 推送失败")
        print("=" * 60)
        print("\n可能的原因:")
        print("1. 仓库 URL 不正确")
        print("2. 没有访问权限")
        print("3. 未配置 GitHub 身份验证")
        print("\n解决方案:")
        print("HTTPS: 需要使用 Personal Access Token")
        print("SSH: 需要配置 SSH 密钥")
        print("\n帮助文档:")
        print("https://docs.github.com/zh/authentication")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
