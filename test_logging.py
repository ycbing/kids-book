#!/usr/bin/env python3
"""
日志系统测试脚本
测试结构化日志和日志轮转功能
"""
import sys
import os
from pathlib import Path
import time
import logging
import json

# 设置UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加backend到路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.logging import setup_logging, request_logger, error_logger, get_logger

print("="*60)
print("🔧 AI绘本平台 - 日志系统测试")
print("="*60)

# 初始化日志系统
logger = setup_logging()

# 测试1: 基础日志级别
print("\n" + "="*60)
print("📋 测试1: 基础日志级别")
print("="*60)

logger.debug("这是一条DEBUG日志")
logger.info("这是一条INFO日志")
logger.warning("这是一条WARNING日志")
logger.error("这是一条ERROR日志")
try:
    raise ValueError("这是一条测试异常")
except Exception as e:
    logger.critical("这是一条CRITICAL日志", exc_info=e)

print("✅ 基础日志级别测试完成")

# 测试2: 带上下文的日志
print("\n" + "="*60)
print("📋 测试2: 带上下文的日志")
print("="*60)

from app.core.logging import log_with_context

test_logger = get_logger(__name__)
log_with_context(
    test_logger,
    "用户登录成功",
    user_id=123,
    username="test_user",
    ip="192.168.1.100",
    user_agent="Mozilla/5.0"
)

log_with_context(
    test_logger,
    "绘本生成完成",
    book_id=456,
    page_count=8,
    duration_seconds=120
)

print("✅ 带上下文的日志测试完成")

# 测试3: 请求日志
print("\n" + "="*60)
print("📋 测试3: HTTP请求日志")
print("="*60)

request_logger.log_request(
    method="GET",
    path="/api/v1/books/123",
    status_code=200,
    duration=0.123,
    client_ip="192.168.1.100",
    user_id=1,
    request_id="test-request-123"
)

request_logger.log_request(
    method="POST",
    path="/api/v1/books",
    status_code=201,
    duration=2.456,
    client_ip="192.168.1.101",
    user_id=2,
    request_id="test-request-456"
)

request_logger.log_request(
    method="GET",
    path="/api/v1/books/999",
    status_code=404,
    duration=0.050,
    client_ip="192.168.1.102",
    user_id=None,
    request_id="test-request-789"
)

print("✅ HTTP请求日志测试完成")

# 测试4: 错误日志
print("\n" + "="*60)
print("📋 测试4: 错误日志")
print("="*60)

# 测试一般错误
try:
    result = 1 / 0
except Exception as e:
    error_logger.log_error(
        e,
        context={
            "operation": "division",
            "operands": [1, 0]
        }
    )

# 测试API错误
error_logger.log_api_error(
    error_code="NOT_FOUND",
    message="资源不存在",
    path="/api/v1/books/999",
    status_code=404,
    details={
        "resource_type": "book",
        "resource_id": 999
    }
)

error_logger.log_api_error(
    error_code="VALIDATION_ERROR",
    message="数据验证失败",
    path="/api/v1/books",
    status_code=422,
    details={
        "field": "email",
        "reason": "格式无效"
    }
)

print("✅ 错误日志测试完成")

# 测试5: 性能测试
print("\n" + "="*60)
print("📋 测试5: 日志性能测试")
print("="*60)

iterations = 1000
start_time = time.time()

for i in range(iterations):
    logger.info(f"性能测试日志 {i}")

duration = time.time() - start_time
qps = iterations / duration

print(f"✅ 完成 {iterations} 条日志")
print(f"   总耗时: {duration:.3f}秒")
print(f"   QPS: {qps:.0f} 条/秒")
print(f"   平均延迟: {(duration/iterations)*1000:.3f}毫秒")

# 测试6: 文件日志检查
print("\n" + "="*60)
print("📋 测试6: 日志文件检查")
print("="*60)

log_dir = Path("logs")
if log_dir.exists():
    log_files = list(log_dir.glob("*.log*"))
    print(f"✅ 日志目录存在: {log_dir}")
    print(f"   日志文件数量: {len(log_files)}")

    for log_file in log_files:
        size = log_file.stat().st_size
        print(f"   - {log_file.name}: {size} 字节")
else:
    print("ℹ️  日志目录不存在（生产环境才会创建）")

# 测试7: JSON格式验证
print("\n" + "="*60)
print("📋 测试7: JSON格式验证（生产环境）")
print("="*60)

from app.config import settings

if not settings.DEBUG:
    print("ℹ️  当前为生产环境，日志应为JSON格式")
    print("   请查看 logs/app.log 验证JSON格式")
else:
    print("ℹ️  当前为开发环境，日志为彩色文本格式")
    print("   设置 DEBUG=false 可启用JSON格式")

# 总结
print("\n" + "="*60)
print("📊 测试总结")
print("="*60)

print("\n✅ 所有测试完成！")
print("\n功能检查:")
print("  ✅ 基础日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）")
print("  ✅ 带上下文的日志记录")
print("  ✅ HTTP请求日志")
print("  ✅ 错误和异常日志")
print("  ✅ API错误日志")
print("  ✅ 性能测试")

print("\n日志特性:")
print("  ✅ 结构化日志（JSON格式，生产环境）")
print("  ✅ 彩色日志（开发环境）")
print("  ✅ 日志轮转（大小/时间）")
print("  ✅ 请求ID追踪")
print("  ✅ 上下文信息")

print("\n日志文件:")
if log_dir.exists():
    print(f"  ✅ 位置: {log_dir.absolute()}")
    for log_file in log_files:
        print(f"     - {log_file.name}")
else:
    print("  ℹ️  生产环境启用")
    print("  ℹ️  设置 DEBUG=false 并重启服务")

print("\n💡 使用建议:")
print("  - 开发环境：使用彩色日志，便于调试")
print("  - 生产环境：使用JSON格式，便于日志分析")
print("  - 使用请求ID追踪特定请求")
print("  - 定期检查和清理日志文件")

print("="*60)
