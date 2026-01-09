#!/usr/bin/env python
"""
依赖锁定文件生成脚本

用途：
1. 生成精确版本锁定的 requirements.lock 文件
2. 检测依赖版本变化
3. 验证依赖兼容性

使用方法：
    python scripts/lock_requirements.py
    python scripts/lock_requirements.py --check  # 仅检查版本变化
    python scripts/lock_requirements.py --update  # 更新所有依赖到最新版本
"""

import subprocess
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict


def get_current_lock() -> Dict[str, str]:
    """读取当前的requirements.lock"""
    lock_file = Path(__file__).parent.parent / "requirements.lock"

    if not lock_file.exists():
        return {}

    current_lock = {}
    with open(lock_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "===" in line:
                pkg, version = line.split("===")
                current_lock[pkg] = version

    return current_lock


def freeze_requirements() -> List[str]:
    """执行pip freeze获取当前安装的包"""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True
    )

    packages = []
    for line in result.stdout.strip().split("\n"):
        if line and not line.startswith("#"):
            packages.append(line)

    return packages


def filter_packages(packages: List[str]) -> List[str]:
    """过滤掉不需要锁定的包"""
    # 读取requirements.txt中定义的包
    req_file = Path(__file__).parent.parent / "requirements.txt"
    required_packages = set()

    if req_file.exists():
        with open(req_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("#"):
                    # 提取包名（处理 >=, <, == 等运算符）
                    pkg_name = line.split(">")[0].split("<")[0].split("=")[0].strip()
                    if pkg_name:
                        required_packages.add(pkg_name.lower())

    # 过滤包：只保留requirements.txt中定义的包及其依赖
    # 这里简化处理，保留所有非开发环境的包
    filtered = []
    exclude_patterns = ["setuptools", "wheel", "pip"]

    for pkg in packages:
        pkg_name = pkg.split("==")[0].split(">")[0].split("<")[0].strip().lower()
        if not any(pattern in pkg_name for pattern in exclude_patterns):
            filtered.append(pkg)

    return filtered


def generate_lock_file(packages: List[str], output_file: Path):
    """生成requirements.lock文件"""

    header = """# ============================================
# AI绘本创作平台 - 生产环境依赖锁定
# ============================================
# 生成时间: {timestamp}
# 用途: 生产环境精确版本锁定
#
# 生成方法:
#   pip freeze > requirements.lock
#   或运行: python scripts/lock_requirements.py
#
# 更新方法:
#   pip install -r requirements.txt --upgrade
#   python scripts/lock_requirements.py --update
# ============================================

""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 排序包
    packages_sorted = sorted(packages, key=lambda x: x.lower())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(packages_sorted))
        f.write("\n")

    print(f"✅ 已生成锁定文件: {output_file}")
    print(f"   共锁定 {len(packages_sorted)} 个包")


def check_version_changes() -> bool:
    """检查版本是否有变化"""
    current_lock = get_current_lock()
    packages = freeze_requirements()
    packages = filter_packages(packages)

    has_changes = False

    print("\n📋 检查依赖版本变化:")
    print("=" * 60)

    for pkg_str in packages:
        if "==" in pkg_str:
            pkg, version = pkg_str.split("==")
            if pkg in current_lock:
                if current_lock[pkg] != version:
                    print(f"⚠️  {pkg}: {current_lock[pkg]} → {version}")
                    has_changes = True
            else:
                print(f"➕ {pkg}: {version} (新增)")
                has_changes = True

    if not has_changes:
        print("✅ 所有依赖版本未变化")
    else:
        print("\n💡 运行 'python scripts/lock_requirements.py' 更新锁定文件")

    return has_changes


def install_and_lock(upgrade: bool = False):
    """安装依赖并生成锁定文件"""
    backend_dir = Path(__file__).parent.parent
    req_file = backend_dir / "requirements.txt"
    lock_file = backend_dir / "requirements.lock"

    print("📦 安装依赖...")

    if upgrade:
        print("🔄 升级所有依赖到最新版本...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--upgrade"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]

    try:
        subprocess.run(cmd, check=True)
        print("✅ 依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        sys.exit(1)

    # 生成锁定文件
    packages = freeze_requirements()
    packages = filter_packages(packages)
    generate_lock_file(packages, lock_file)


def main():
    parser = argparse.ArgumentParser(description="依赖版本锁定工具")
    parser.add_argument(
        "--check",
        action="store_true",
        help="仅检查依赖版本变化，不生成锁定文件"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="更新所有依赖到最新版本"
    )

    args = parser.parse_args()

    if args.check:
        # 仅检查版本变化
        has_changes = check_version_changes()
        sys.exit(1 if has_changes else 0)
    else:
        # 安装依赖并生成锁定文件
        install_and_lock(upgrade=args.update)


if __name__ == "__main__":
    main()
