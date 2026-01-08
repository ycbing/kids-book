#!/usr/bin/env python3
"""
用户认证功能测试脚本
测试注册、登录、token验证等功能
"""
import sys
import requests
import json
from pathlib import Path

# 设置UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def test_register():
    """测试用户注册"""
    print_section("1. 测试用户注册")

    url = f"{BASE_URL}/auth/register"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }

    print(f"URL: {url}")
    print(f"数据: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, json=data)
        print(f"\n状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        if response.status_code == 201:
            result = response.json()
            print(f"\n✅ 注册成功！")
            print(f"用户ID: {result['user']['id']}")
            print(f"用户名: {result['user']['username']}")
            print(f"Token: {result['access_token'][:50]}...")
            return result['access_token']
        else:
            print(f"\n❌ 注册失败: {response.json().get('detail', 'Unknown error')}")
            return None
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器！请确保后端服务正在运行。")
        return None
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return None

def test_login():
    """测试用户登录"""
    print_section("2. 测试用户登录")

    url = f"{BASE_URL}/auth/login"
    data = {
        "username": "testuser",
        "password": "testpass123"
    }

    print(f"URL: {url}")
    print(f"数据: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, json=data)
        print(f"\n状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 登录成功！")
            print(f"用户ID: {result['user']['id']}")
            print(f"用户名: {result['user']['username']}")
            print(f"Token: {result['access_token'][:50]}...")
            return result['access_token']
        else:
            print(f"\n❌ 登录失败: {response.json().get('detail', 'Unknown error')}")
            return None
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器！")
        return None
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        return None

def test_verify_token(token: str):
    """测试Token验证"""
    print_section("3. 测试Token验证")

    url = f"{BASE_URL}/auth/verify"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"URL: {url}")
    print(f"Headers: Authorization: Bearer {token[:50]}...")

    try:
        response = requests.post(url, headers=headers)
        print(f"\n状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        if response.status_code == 200 and response.json().get('valid'):
            print(f"\n✅ Token验证成功！")
            print(f"用户ID: {response.json().get('user_id')}")
        else:
            print(f"\n❌ Token验证失败")
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

def test_get_me(token: str):
    """测试获取当前用户信息"""
    print_section("4. 测试获取当前用户信息")

    url = f"{BASE_URL}/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"URL: {url}")
    print(f"Headers: Authorization: Bearer {token[:50]}...")

    try:
        response = requests.get(url, headers=headers)
        print(f"\n状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        if response.status_code == 200:
            user = response.json()
            print(f"\n✅ 获取用户信息成功！")
            print(f"用户名: {user['username']}")
            print(f"邮箱: {user['email']}")
        else:
            print(f"\n❌ 获取用户信息失败")
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到服务器！")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

def test_invalid_auth():
    """测试无效的认证"""
    print_section("5. 测试无效认证")

    # 测试错误的用户名密码
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": "wronguser",
        "password": "wrongpass"
    }

    print("5.1 测试错误的用户名密码")
    print(f"URL: {url}")
    print(f"数据: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, json=data)
        print(f"\n状态码: {response.status_code}")
        if response.status_code == 401:
            print("✅ 正确拒绝了错误的凭据")
        else:
            print("❌ 应该返回401状态码")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

    # 测试无效的token
    print("\n5.2 测试无效的Token")
    url = f"{BASE_URL}/auth/me"
    headers = {
        "Authorization": "Bearer invalid-token-12345"
    }

    print(f"URL: {url}")
    print(f"Headers: Authorization: Bearer invalid-token-12345")

    try:
        response = requests.get(url, headers=headers)
        print(f"\n状态码: {response.status_code}")
        if response.status_code == 401:
            print("✅ 正确拒绝了无效的Token")
        else:
            print("❌ 应该返回401状态码")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def main():
    """主函数"""
    print("🔐 AI绘本平台 - 用户认证测试")
    print(f"后端地址: {BASE_URL}")
    print("\n请确保后端服务正在运行（python -m backend.app.main）")

    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ 后端服务未正常运行")
            return
    except:
        print("\n❌ 无法连接到后端服务，请确保服务正在运行")
        print("   启动命令: cd backend && python -m app.main")
        return

    # 运行测试
    token = None

    # 1. 测试注册
    token = test_register()

    # 2. 测试登录
    if not token:
        token = test_login()

    # 如果有token，继续测试
    if token:
        # 3. 验证token
        test_verify_token(token)

        # 4. 获取用户信息
        test_get_me(token)

    # 5. 测试无效认证
    test_invalid_auth()

    # 总结
    print_section("测试总结")
    print("✅ 认证系统基本功能测试完成")
    print("\n下一步:")
    print("1. 前端集成：在前端添加登录/注册界面")
    print("2. API保护：在需要认证的API端点添加get_current_user依赖")
    print("3. Token存储：将token存储在localStorage或cookie中")
    print("4. 自动刷新：实现token自动刷新机制")
    print("\n相关文档:")
    print("- [AUTH_IMPLEMENTATION.md](AUTH_IMPLEMENTATION.md)")

if __name__ == '__main__':
    main()
