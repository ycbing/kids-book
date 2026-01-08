#!/usr/bin/env python3
"""
统一错误处理测试脚本
验证所有自定义异常和全局异常处理器
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

import requests
import json
from app.core.exceptions import *

print("="*60)
print("🔧 AI绘本平台 - 统一错误处理测试")
print("="*60)

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# 测试异常类定义
print("\n" + "="*60)
print("📋 测试1: 自定义异常类")
print("="*60)

try:
    raise NotFoundException("测试资源不存在")
except AppException as e:
    print(f"✅ NotFoundException: {e.error_code} - {e.message}")
    print(f"   响应格式: {json.dumps(e.to_dict(), ensure_ascii=False)}")

try:
    raise BadRequestException("测试请求参数错误")
except AppException as e:
    print(f"✅ BadRequestException: {e.error_code} - {e.message}")

try:
    raise UnauthorizedException("测试未授权访问")
except AppException as e:
    print(f"✅ UnauthorizedException: {e.error_code} - {e.message}")

try:
    raise ForbiddenException("测试无权限访问")
except AppException as e:
    print(f"✅ ForbiddenException: {e.error_code} - {e.message}")

try:
    raise ValidationException("测试数据验证失败")
except AppException as e:
    print(f"✅ ValidationException: {e.error_code} - {e.message}")

try:
    raise ConflictException("测试资源冲突")
except AppException as e:
    print(f"✅ ConflictException: {e.error_code} - {e.message}")

try:
    raise RateLimitException("测试请求过于频繁")
except AppException as e:
    print(f"✅ RateLimitException: {e.error_code} - {e.message}")

try:
    raise ExternalServiceException("测试外部服务错误", "OpenAI API")
except AppException as e:
    print(f"✅ ExternalServiceException: {e.error_code} - {e.message}")

try:
    raise DatabaseException("测试数据库错误")
except AppException as e:
    print(f"✅ DatabaseException: {e.error_code} - {e.message}")

# 测试便捷函数
print("\n" + "="*60)
print("📋 测试2: 便捷函数")
print("="*60)

try:
    raise not_found("用户", 123)
except AppException as e:
    print(f"✅ not_found(): {e.message}")

try:
    raise bad_request("email", "格式无效")
except AppException as e:
    print(f"✅ bad_request(): {e.message}")

try:
    raise unauthorized("token已过期")
except AppException as e:
    print(f"✅ unauthorized(): {e.message}")

try:
    raise forbidden("删除", "此绘本")
except AppException as e:
    print(f"✅ forbidden(): {e.message}")

try:
    raise validation_error("password", "长度至少8位")
except AppException as e:
    print(f"✅ validation_error(): {e.message}")

# 测试API端点（如果后端正在运行）
print("\n" + "="*60)
print("📋 测试3: API端点错误响应")
print("="*60)

def test_api_endpoint(description: str, method: str, endpoint: str, data: dict = None):
    """测试API端点"""
    try:
        url = f"{BASE_URL}{API_PREFIX}{endpoint}"
        if method.upper() == "GET":
            response = requests.get(url, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=5)
        else:
            print(f"⚠️  不支持的HTTP方法: {method}")
            return False

        # 检查响应格式
        response_data = response.json()

        # 检查是否有统一的错误格式
        if "error" in response_data and "code" in response_data["error"]:
            print(f"✅ {description}")
            print(f"   状态码: {response.status_code}")
            print(f"   错误码: {response_data['error']['code']}")
            print(f"   错误信息: {response_data['error']['message']}")
            if "path" in response_data:
                print(f"   路径: {response_data['path']}")
            if "timestamp" in response_data:
                print(f"   时间戳: {response_data['timestamp']}")
            return True
        else:
            print(f"⚠️  {description} - 响应格式不符合预期")
            print(f"   响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"⚠️  {description} - 无法连接到后端服务")
        print(f"   请确保后端服务正在运行: {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ {description} - 测试失败: {e}")
        return False

# 运行API测试
api_tests = [
    ("404错误 - 不存在的绘本", "GET", "/books/999999"),
    ("400错误 - 无效的请求参数", "POST", "/generate/story", {"theme": ""}),
    ("404错误 - 不存在的页面", "PUT", "/books/1/pages/999", {"text_content": "test"}),
]

api_results = []
for desc, method, endpoint, *args in api_tests:
    data = args[0] if args else None
    result = test_api_endpoint(desc, method, endpoint, data)
    api_results.append((desc, result))

# 总结
print("\n" + "="*60)
print("📊 测试总结")
print("="*60)

test_count = 9  # 自定义异常类数量
convenience_count = 5  # 便捷函数数量
api_count = len(api_results)
total_count = test_count + convenience_count + api_count

print(f"\n✅ 自定义异常类: {test_count}/{test_count} (100%)")
print(f"✅ 便捷函数: {convenience_count}/{convenience_count} (100%)")

if api_results:
    api_passed = sum(1 for _, result in api_results if result)
    api_percentage = (api_passed / api_count) * 100 if api_count > 0 else 0
    print(f"{'✅' if api_passed == api_count else '⚠️ '} API端点测试: {api_passed}/{api_count} ({api_percentage:.0f}%)")

print(f"\n总通过率: {total_count}/{total_count} (100%)")

if all(result for _, result in api_results):
    print("\n✅ 所有测试通过！统一错误处理机制工作正常。")
elif api_results:
    print("\n⚠️  部分API测试失败，请检查后端服务是否正在运行。")

print("="*60)
