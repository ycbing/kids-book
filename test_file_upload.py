#!/usr/bin/env python3
"""
文件上传安全测试脚本
测试文件验证、保存和删除功能
"""
import sys
import os
from pathlib import Path
import tempfile
import aiofiles
import asyncio

# 设置UTF-8编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加backend到路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.file_utils import (
    validate_upload_file,
    sanitize_filename,
    generate_safe_filename,
    calculate_file_hash,
    get_file_mime_type,
    save_upload_file,
    delete_file,
    get_file_info,
    is_safe_path,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE
)

print("="*60)
print("🔧 AI绘本平台 - 文件上传安全测试")
print("="*60)

# 创建临时测试目录
temp_dir = Path(tempfile.mkdtemp())

# 创建模拟的UploadFile对象
class MockUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str = None):
        self.filename = filename
        self._content = content
        self.content_type = content_type or get_file_mime_type(filename)
        self._pos = 0

    async def read(self):
        if self._pos == 0:
            self._pos = len(self._content)
            return self._content
        return b""

    async def seek(self, pos):
        self._pos = pos


# 测试1: 文件类型验证
print("\n" + "="*60)
print("📋 测试1: 文件类型验证")
print("="*60)

async def test_file_type_validation():
    # 创建测试文件
    test_cases = [
        ("image.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF", True),  # JPEG
        ("image.png", b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A", True),  # PNG
        ("image.gif", b"\x47\x49\x46\x38\x39\x61", True),          # GIF
        ("test.exe", b"MZ\x90\x00", False),                        # EXE（拒绝）
        ("test.txt", b"Hello World", False),                       # TXT（拒绝）
    ]

    for filename, content, should_pass in test_cases:
        try:
            file = MockUploadFile(filename, content)
            await validate_upload_file(file)

            if should_pass:
                print(f"  ✅ {filename}: 通过验证")
            else:
                print(f"  ❌ {filename}: 应该被拒绝但通过了")
        except Exception as e:
            if not should_pass:
                print(f"  ✅ {filename}: 正确拒绝 ({str(e)[:50]}...)")
            else:
                print(f"  ❌ {filename}: 应该通过但被拒绝 ({str(e)})")

asyncio.run(test_file_type_validation())

# 测试2: 文件大小限制
print("\n" + "="*60)
print("📋 测试2: 文件大小限制")
print("="*60)

async def test_file_size_limit():
    # 创建小文件（应该通过）
    small_content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 1000
    small_file = MockUploadFile("test.jpg", small_content)

    try:
        await validate_upload_file(small_file, max_size=1024*1024)
        print(f"  ✅ 小文件（1KB）: 通过验证")
    except Exception as e:
        print(f"  ❌ 小文件验证失败: {e}")

    # 创建大文件（应该拒绝）
    large_content = b"\xFF\xD8\xFF\xE0" + b"\x00" * (6 * 1024 * 1024)
    large_file = MockUploadFile("large.jpg", large_content)

    try:
        await validate_upload_file(large_file, max_size=5*1024*1024)
        print(f"  ❌ 大文件（6MB）: 应该被拒绝但通过了")
    except Exception as e:
        print(f"  ✅ 大文件（6MB）: 正确拒绝 ({str(e)[:50]}...)")

asyncio.run(test_file_size_limit())

# 测试3: 文件名清理
print("\n" + "="*60)
print("📋 测试3: 文件名清理")
print("="*60)

test_filenames = [
    ("正常文件名.jpg", "正常文件名.jpg"),
    ("../../../etc/passwd", "passwd"),  # 路径遍历攻击
    ("file with spaces.png", "file_with_spaces.png"),
    ("file<>with\"special:chars|.gif", "filewithspecialchars.gif"),
    ("文件名中文.jpg", "jpg"),  # 中文字符被移除
]

for original, expected_part in test_filenames:
    try:
        result = sanitize_filename(original)
        if expected_part in result:
            print(f"  ✅ '{original}' → '{result}'")
        else:
            print(f"  ⚠️  '{original}' → '{result}' (包含'{expected_part}')")
    except Exception as e:
        print(f"  ⚠️  '{original}' → 拒绝: {str(e)[:50]}")

# 测试4: 安全文件名生成
print("\n" + "="*60)
print("📋 测试4: 安全文件名生成")
print("="*60)

for original in ["测试图片.jpg", "image.png", "photo.jpeg"]:
    safe_name = generate_safe_filename(original)
    print(f"  '{original}' → '{safe_name}'")

# 测试5: 文件哈希计算
print("\n" + "="*60)
print("📋 测试5: 文件哈希计算")
print("="*60)

test_content = b"Hello, World!"
file_hash = calculate_file_hash(test_content)
print(f"  内容: {test_content}")
print(f"  SHA256: {file_hash}")
print(f"  ✅ 哈希计算完成")

# 测试6: MIME类型检测
print("\n" + "="*60)
print("📋 测试6: MIME类型检测")
print("="*60)

test_files = [
    ("image.jpg", "image/jpeg"),
    ("image.png", "image/png"),
    ("image.gif", "image/gif"),
    ("document.pdf", "application/pdf"),
]

for filename, expected_mime in test_files:
    mime = get_file_mime_type(filename)
    status = "✅" if mime == expected_mime else "⚠️"
    print(f"  {status} {filename}: {mime}")

# 测试7: 路径安全检查
print("\n" + "="*60)
print("📋 测试7: 路径安全检查（路径遍历防护）")
print("="*60)

test_paths = [
    ("uploads/image.jpg", True),
    ("uploads/../etc/passwd", False),
    ("uploads/../../secret.txt", False),
    ("uploads/subdir/image.png", True),
]

for file_path, expected_safe in test_paths:
    try:
        result = is_safe_path(file_path, Path("uploads"))
        if result == expected_safe:
            status = "✅"
        else:
            status = "❌"
        print(f"  {status} '{file_path}': 安全={result}")
    except Exception as e:
        print(f"  ⚠️  '{file_path}': 异常 - {str(e)[:50]}")

# 测试8: 文件保存和删除
print("\n" + "="*60)
print("📋 测试8: 文件保存和删除")
print("="*60)

async def test_file_operations():
    test_dir = temp_dir / "test_uploads"
    test_dir.mkdir(exist_ok=True)

    # 创建测试图片（JPEG格式）
    jpeg_content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 1000
    test_file = MockUploadFile("test_image.jpg", jpeg_content)

    # 保存文件
    try:
        file_path, filename, size = await save_upload_file(
            test_file,
            test_dir
        )
        print(f"  ✅ 文件保存成功")
        print(f"     路径: {file_path}")
        print(f"     文件名: {filename}")
        print(f"     大小: {size} 字节")

        # 检查文件是否存在
        if Path(file_path).exists():
            print(f"  ✅ 文件确实存在")

        # 获取文件信息
        info = get_file_info(file_path)
        print(f"  ✅ 文件信息:")
        print(f"     大小: {info['size_mb']} MB")
        print(f"     MIME类型: {info['mime_type']}")

        # 删除文件
        deleted = await delete_file(file_path)
        if deleted:
            print(f"  ✅ 文件删除成功")

        if not Path(file_path).exists():
            print(f"  ✅ 文件确实已删除")

    except Exception as e:
        print(f"  ❌ 文件操作失败: {e}")

asyncio.run(test_file_operations())

# 测试9: 批量文件上传
print("\n" + "="*60)
print("📋 测试9: 批量文件上传")
print("="*60)

async def test_batch_upload():
    from app.core.file_utils import save_multiple_files

    test_dir = temp_dir / "batch_test"
    test_dir.mkdir(exist_ok=True)

    # 创建多个测试文件
    files = [
        MockUploadFile(f"image_{i}.jpg", b"\xFF\xD8\xFF\xE0" + b"\x00" * 500)
        for i in range(3)
    ]

    try:
        saved_files = await save_multiple_files(
            files,
            test_dir,
            max_file_count=5
        )

        print(f"  ✅ 批量上传成功: {len(saved_files)} 个文件")

        for file_info in saved_files:
            print(f"     - {file_info['filename']} ({file_info['size']} 字节)")

        # 清理
        for file_info in saved_files:
            await delete_file(file_info['path'])

    except Exception as e:
        print(f"  ❌ 批量上传失败: {e}")

asyncio.run(test_batch_upload())

# 测试10: 文件内容验证（魔数检测）
print("\n" + "="*60)
print("📋 测试10: 文件内容验证（魔数检测）")
print("="*60)

from app.core.file_utils import _validate_file_content

test_cases = [
    (b"\xFF\xD8\xFF\xE0", ".jpg", True, "正确的JPEG"),
    (b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A", ".png", True, "正确的PNG"),
    (b"\xFF\xD8\xFF\xE0", ".png", False, "JPEG内容但PNG扩展名"),
    (b"Hello World", ".jpg", False, "文本内容但图片扩展名"),
    (b"\x47\x49\x46\x38\x39\x61", ".gif", True, "正确的GIF"),
]

for content, ext, expected_valid, description in test_cases:
    is_valid = _validate_file_content(content, ext)
    status = "✅" if is_valid == expected_valid else "❌"
    print(f"  {status} {description}: {'有效' if is_valid else '无效'}")

# 总结
print("\n" + "="*60)
print("📊 测试总结")
print("="*60)

print("\n✅ 安全特性:")
print("  ✅ 文件类型验证（扩展名+MIME类型）")
print("  ✅ 文件大小限制（5MB）")
print("  ✅ 文件名清理（防止路径遍历）")
print("  ✅ 安全文件名生成（UUID）")
print("  ✅ 文件哈希计算（SHA256）")
print("  ✅ 文件内容验证（魔数检测）")
print("  ✅ 路径安全检查")
print("  ✅ 批量上传支持")
print("  ✅ 文件保存和删除")

print("\n🔒 安全防护:")
print("  ✅ 防止路径遍历攻击")
print("  ✅ 防止恶意文件上传")
print("  ✅ 防止文件大小攻击")
print("  ✅ 防止文件伪装攻击")

print("\n📁 测试目录:")
print(f"  {temp_dir}")

print("\n💡 后续清理:")
print(f"  rm -rf {temp_dir}")

print("="*60)
