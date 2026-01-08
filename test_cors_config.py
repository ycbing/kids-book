#!/usr/bin/env python3
"""
CORS配置测试脚本
验证CORS安全配置是否正确
"""
import sys
import os
from pathlib import Path

# 设置UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加backend到路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.config import settings

def test_cors_config():
    """测试CORS配置"""
    print("="*60)
    print("🔒 CORS配置安全检查")
    print("="*60 + "\n")

    # 获取允许的域名列表
    allowed_origins = settings.allowed_origins_list

    print("📋 当前CORS配置:")
    print(f"  环境变量 ALLOWED_ORIGINS: {settings.ALLOWED_ORIGINS}")
    print(f"  解析后的域名列表: {allowed_origins}")
    print(f"  域名数量: {len(allowed_origins)}\n")

    # 检查是否有危险配置
    issues = []

    if not allowed_origins:
        issues.append("❌ 严重: ALLOWED_ORIGINS未配置，将阻止所有跨域请求！")
    else:
        print("✅ ALLOWED_ORIGINS已配置\n")

        # 检查是否包含危险配置
        if "*" in settings.ALLOWED_ORIGINS:
            issues.append("❌ 严重: 检测到通配符 '*'，允许所有域名访问！")

        if "http://" in settings.ALLOWED_ORIGINS and not settings.DEBUG:
            issues.append("⚠️  警告: 生产环境使用HTTP协议不安全")

        # 检查开发环境配置
        if settings.DEBUG:
            localhost_count = sum(1 for origin in allowed_origins if "localhost" in origin or "127.0.0.1" in origin)
            if localhost_count > 0:
                print(f"✅ 开发环境: 包含 {localhost_count} 个本地域名")

        # 检查生产环境配置
        if not settings.DEBUG:
            https_count = sum(1 for origin in allowed_origins if origin.startswith("https://"))
            if https_count == 0:
                issues.append("❌ 严重: 生产环境未配置HTTPS域名！")
            else:
                print(f"✅ 生产环境: 包含 {https_count} 个HTTPS域名")

    # 显示配置的域名
    if allowed_origins:
        print("\n🌐 允许的域名列表:")
        for i, origin in enumerate(allowed_origins, 1):
            protocol = "🔒" if origin.startswith("https://") else "⚠️ "
            env_type = "本地" if ("localhost" in origin or "127.0.0.1" in origin) else "远程"
            print(f"  {i}. {protocol} {origin} ({env_type})")

    # 显示问题
    if issues:
        print("\n" + "="*60)
        print("⚠️  发现的问题:")
        print("="*60)
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n" + "="*60)
        print("✅ CORS配置安全检查通过！")
        print("="*60)

    # 配置建议
    print("\n📝 配置建议:")
    if settings.DEBUG:
        print("  当前: 开发环境")
        print("  建议: 允许 localhost 和 127.0.0.1 即可")
        print("  示例: ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173")
    else:
        print("  当前: 生产环境")
        print("  建议: 仅允许你拥有的HTTPS域名")
        print("  示例: ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com")

    print("\n" + "="*60)

    return len(issues)

def test_cors_behavior():
    """测试CORS行为"""
    print("\n🧪 CORS行为测试")
    print("="*60 + "\n")

    # 模拟请求来源
    test_origins = [
        ("http://localhost:5173", "开发环境前端"),
        ("http://evil.com", "恶意网站"),
        ("https://yourdomain.com", "生产环境域名"),
    ]

    allowed_origins = settings.allowed_origins_list

    print("测试不同来源的请求:")
    for origin, description in test_origins:
        is_allowed = origin in allowed_origins
        status = "✅ 允许" if is_allowed else "❌ 拒绝"
        print(f"  {status} {origin} ({description})")

    print("\n" + "="*60)

if __name__ == '__main__':
    try:
        issues_count = test_cors_config()
        test_cors_behavior()

        # 返回退出码
        sys.exit(1 if issues_count > 0 else 0)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
