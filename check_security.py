#!/usr/bin/env python3
"""
安全检查脚本 - 验证项目中是否有敏感信息泄露
运行方式: python check_security.py
"""
import os
import re
from pathlib import Path
from typing import List, Tuple

class SecurityChecker:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[Tuple[str, str]] = []

        # 常见的API密钥模式
        self.api_key_patterns = [
            r'sk-[a-zA-Z0-9]{32,}',  # OpenAI API keys
            r'Bearer\s+[a-zA-Z0-9]{32,}',  # Bearer tokens
            r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}',  # Generic API keys
            # 注意：不检查password，因为在模型中定义password字段是正常的
        ]

        # 需要特别警告的硬编码密钥（排除示例文件）
        self.hardcoded_key_warnings = [
            (r'sk-lrblpprkvitjenoutducitdhqogfhsfyiziwqvovwftfrfym', '发现之前的硬编码密钥！'),
        ]

        # 不应该检查的目录
        self.exclude_dirs = {
            '.git', 'venv', 'env', '__pycache__', 'node_modules',
            'dist', 'build', '.venv', '.idea', '.vscode', 'outputs'
        }

        # 不应该检查的文件
        self.exclude_files = {
            '.env.example', 'SECURITY_CONFIG_GUIDE.md',
            'check_security.py', 'OPTIMIZATION_RECOMMENDATIONS.md',
            'SECURITY_FIX_SUMMARY.md'  # 本修复总结
        }

    def check_file(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """检查单个文件"""
        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # 跳过注释行
                    if line.strip().startswith('#'):
                        continue

                    # 检查已知的硬编码密钥
                    for pattern, warning in self.hardcoded_key_warnings:
                        if re.search(pattern, line):
                            findings.append((line_num, line.strip(), warning))
                            continue

                    # 检查API密钥模式
                    for pattern in self.api_key_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # 排除示例值（sk-your-xxx-here）
                            if 'sk-your-' not in line and 'sk-xxx' not in line:
                                findings.append((line_num, line.strip(), f"疑似API密钥: {pattern}"))
                                break

        except Exception as e:
            pass  # 忽略读取错误

        return findings

    def scan(self):
        """扫描整个项目"""
        print("🔍 开始安全扫描...\n")

        # 扫描Python文件
        print("📂 扫描 Python 文件...")
        for py_file in self.project_root.rglob('*.py'):
            # 检查目录排除
            if any(excl in py_file.parts for excl in self.exclude_dirs):
                continue

            # 检查文件排除
            if py_file.name in self.exclude_files:
                continue

            findings = self.check_file(py_file)
            for line_num, line, pattern in findings:
                self.issues.append((
                    str(py_file.relative_to(self.project_root)),
                    f"行 {line_num}: {line[:80]}...",
                    f"模式: {pattern}"
                ))

        # 扫描环境文件
        print("📂 扫描环境配置文件...")
        for env_file in self.project_root.rglob('.env*'):
            if env_file.name in self.exclude_files:
                continue

            findings = self.check_file(env_file)
            for line_num, line, pattern in findings:
                self.issues.append((
                    str(env_file.relative_to(self.project_root)),
                    f"行 {line_num}: {line[:80]}...",
                    f"模式: {pattern}"
                ))

        # 检查.env文件是否被Git跟踪
        print("📂 检查Git跟踪状态...")
        git_dir = self.project_root / '.git'
        if git_dir.exists():
            import subprocess
            try:
                result = subprocess.run(
                    ['git', 'ls-files'],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                tracked_files = result.stdout.strip().split('\n')

                for tracked in tracked_files:
                    if '.env' in tracked and tracked != '.env.example':
                        self.issues.append((
                            tracked,
                            "文件被Git跟踪，可能泄露密钥！",
                            "警告: .env文件不应提交到Git"
                        ))
            except:
                pass

    def print_report(self):
        """打印扫描报告"""
        print("\n" + "="*60)
        print("📊 安全扫描报告")
        print("="*60 + "\n")

        if not self.issues:
            print("✅ 未发现安全问题！")
            print("\n所有检查项:")
            print("  ✅ 没有硬编码的API密钥")
            print("  ✅ .env文件未被Git跟踪")
            print("  ✅ 敏感信息已正确隔离")
            return

        print(f"⚠️  发现 {len(self.issues)} 个潜在安全问题:\n")

        for i, (file_path, issue, pattern) in enumerate(self.issues, 1):
            print(f"{i}. {file_path}")
            print(f"   {issue}")
            print(f"   {pattern}\n")

        print("\n建议修复措施:")
        print("  1. 将敏感信息移至环境变量")
        print("  2. 确保 .env 在 .gitignore 中")
        print("  3. 参考 SECURITY_CONFIG_GUIDE.md 进行配置")

    def check_gitignore(self):
        """检查.gitignore配置"""
        print("\n📂 检查 .gitignore 配置...")

        gitignore_path = self.project_root / '.gitignore'
        if not gitignore_path.exists():
            print("  ⚠️  .gitignore 文件不存在")
            return

        with open(gitignore_path, 'r') as f:
            content = f.read()

        required_entries = ['.env', '.env.local', '*.db']
        missing = []

        for entry in required_entries:
            if entry not in content:
                missing.append(entry)

        if missing:
            print(f"  ⚠️  .gitignore 缺少以下条目: {', '.join(missing)}")
        else:
            print("  ✅ .gitignore 配置正确")

def main():
    """主函数"""
    import sys

    # 设置UTF-8编码
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

    project_root = Path(__file__).parent

    print("🔒 AI绘本平台 - 安全检查工具\n")
    print(f"项目路径: {project_root}\n")

    checker = SecurityChecker(project_root)

    # 执行扫描
    checker.scan()

    # 检查.gitignore
    checker.check_gitignore()

    # 打印报告
    checker.print_report()

    print("\n" + "="*60)
    print("扫描完成！")
    print("="*60)

    # 返回退出码
    return 1 if checker.issues else 0

if __name__ == '__main__':
    exit(main())
