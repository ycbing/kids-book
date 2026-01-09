# backend/app/core/file_utils.py
"""
文件上传安全工具
提供安全的文件上传、验证和处理功能
"""
import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import Set, Optional, Tuple
import aiofiles
from fastapi import UploadFile, HTTPException

from app.config import settings
from app.core.exceptions import BadRequestException


# ========== 配置 ==========

# 允许的图片文件扩展名
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"
}

# 允许的MIME类型
ALLOWED_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/bmp"
}

# 最大文件大小（5MB）
MAX_FILE_SIZE = 5 * 1024 * 1024

# 允许的文件名字符（防止路径遍历）
SAFE_FILENAME_CHARS = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "._-"
)


# ========== 验证函数 ==========

async def validate_upload_file(
    file: UploadFile,
    max_size: int = MAX_FILE_SIZE,
    allowed_extensions: Optional[Set[str]] = None,
    allowed_mime_types: Optional[Set[str]] = None
) -> None:
    """
    验证上传的文件

    参数:
        file: FastAPI UploadFile对象
        max_size: 最大文件大小（字节）
        allowed_extensions: 允许的文件扩展名集合
        allowed_mime_types: 允许的MIME类型集合

    异常:
        BadRequestException: 文件验证失败
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
    if allowed_mime_types is None:
        allowed_mime_types = ALLOWED_MIME_TYPES

    # 1. 检查文件名
    if not file.filename:
        raise BadRequestException("文件名不能为空")

    # 2. 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise BadRequestException(
            f"不支持的文件类型: {file_ext}。"
            f"允许的类型: {', '.join(allowed_extensions)}"
        )

    # 3. 检查MIME类型
    if file.content_type and file.content_type not in allowed_mime_types:
        raise BadRequestException(
            f"无效的文件类型: {file.content_type}。"
            f"允许的类型: {', '.join(allowed_mime_types)}"
        )

    # 4. 读取文件内容
    content = await file.read()

    # 5. 检查文件大小
    if len(content) > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise BadRequestException(
            f"文件过大。最大允许: {max_size_mb:.0f}MB，"
            f"实际: {len(content) / (1024 * 1024):.2f}MB"
        )

    # 6. 验证文件内容（魔数检测）
    if not _validate_file_content(content, file_ext):
        raise BadRequestException("文件内容与扩展名不匹配")

    # 7. 重置文件指针
    await file.seek(0)


def _validate_file_content(content: bytes, file_ext: str) -> bool:
    """
    通过文件头（魔数）验证文件内容

    参数:
        content: 文件内容
        file_ext: 文件扩展名

    返回:
        bool: 文件内容是否有效
    """
    if len(content) < 4:
        return False

    # 文件头魔数
    magic_numbers = {
        b'\xFF\xD8\xFF': '.jpg',  # JPEG
        b'\xFF\xD8\xFF\xE0': '.jpg',
        b'\xFF\xD8\xFF\xE1': '.jpg',
        b'\x89\x50\x4E\x47': '.png',  # PNG
        b'\x47\x49\x46\x38': '.gif',  # GIF
        b'\x52\x49\x46\x46': '.webp', # WEBP (RIFF)
        b'\x42\x4D': '.bmp',          # BMP
    }

    # 检查文件头
    for magic, ext in magic_numbers.items():
        if content.startswith(magic):
            return ext == file_ext

    # PNG的特殊处理（需要检查更多字节）
    if file_ext == '.png':
        return content[:8] == b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'

    return False


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符

    参数:
        filename: 原始文件名

    返回:
        str: 安全的文件名
    """
    # 获取文件名（不包含路径）
    name = Path(filename).name

    # 移除路径遍历字符
    if ".." in name or "/" in name or "\\" in name:
        raise BadRequestException("文件名包含非法字符")

    # 只保留安全字符
    safe_name = "".join(
        c for c in name
        if c in SAFE_FILENAME_CHARS
    )

    # 如果清理后为空，使用默认名称
    if not safe_name or safe_name.startswith("."):
        safe_name = "file"

    return safe_name


def generate_safe_filename(original_filename: str) -> str:
    """
    生成安全的文件名（UUID + 原始扩展名）

    参数:
        original_filename: 原始文件名

    返回:
        str: 安全的唯一文件名
    """
    # 获取文件扩展名
    ext = Path(original_filename).suffix.lower()

    # 生成UUID文件名
    unique_name = str(uuid.uuid4())

    return f"{unique_name}{ext}"


def calculate_file_hash(content: bytes) -> str:
    """
    计算文件的SHA256哈希值

    参数:
        content: 文件内容

    返回:
        str: 十六进制哈希值
    """
    return hashlib.sha256(content).hexdigest()


def get_file_mime_type(filename: str) -> str:
    """
    获取文件的MIME类型

    参数:
        filename: 文件名

    返回:
        str: MIME类型
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


# ========== 文件保存 ==========

async def save_upload_file(
    file: UploadFile,
    destination_dir: Path,
    max_size: int = MAX_FILE_SIZE,
    allowed_extensions: Optional[Set[str]] = None
) -> Tuple[str, str, int]:
    """
    安全地保存上传文件

    参数:
        file: UploadFile对象
        destination_dir: 目标目录
        max_size: 最大文件大小
        allowed_extensions: 允许的文件扩展名

    返回:
        Tuple[str, str, int]: (文件路径, 文件名, 文件大小)

    异常:
        BadRequestException: 文件验证失败
        HTTPException: 文件保存失败
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS

    # 1. 验证文件
    await validate_upload_file(file, max_size, allowed_extensions)

    # 2. 生成安全的文件名
    safe_filename = generate_safe_filename(file.filename)

    # 3. 确保目标目录存在
    destination_dir.mkdir(parents=True, exist_ok=True)

    # 4. 构建完整的文件路径
    file_path = destination_dir / safe_filename

    # 5. 安全检查：确保文件路径在目标目录内
    try:
        file_path = file_path.resolve()
        dest_dir_resolved = destination_dir.resolve()

        # 检查文件路径是否以目标目录开头
        if not str(file_path).startswith(str(dest_dir_resolved)):
            raise BadRequestException("无效的文件路径")
    except Exception as e:
        raise BadRequestException(f"路径验证失败: {str(e)}")

    # 6. 读取文件内容
    content = await file.read()

    # 7. 计算文件哈希（用于去重）
    file_hash = calculate_file_hash(content)

    # 8. 检查文件是否已存在（通过哈希）
    existing_file = await _find_file_by_hash(destination_dir, file_hash)
    if existing_file:
        # 文件已存在，返回现有文件路径
        return str(existing_file), existing_file.name, len(content)

    # 9. 保存文件
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件保存失败: {str(e)}"
        )

    return str(file_path), safe_filename, len(content)


async def _find_file_by_hash(directory: Path, file_hash: str) -> Optional[Path]:
    """
    通过哈希值查找已存在的文件

    参数:
        directory: 搜索目录
        file_hash: 文件哈希值

    返回:
        Optional[Path]: 文件路径，如果不存在返回None
    """
    if not directory.exists():
        return None

    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                    if calculate_file_hash(content) == file_hash:
                        return file_path
            except:
                continue

    return None


# ========== 文件删除 ==========

async def delete_file(file_path: str) -> bool:
    """
    安全地删除文件

    参数:
        file_path: 文件路径

    返回:
        bool: 是否成功删除
    """
    try:
        path = Path(file_path).resolve()

        # 安全检查：确保在允许的目录内
        upload_dir = Path(settings.UPLOAD_DIR).resolve()
        output_dir = Path(settings.OUTPUT_DIR).resolve()

        if not (str(path).startswith(str(upload_dir)) or
                str(path).startswith(str(output_dir))):
            raise BadRequestException("只能删除上传和输出目录的文件")

        # 删除文件
        if path.exists() and path.is_file():
            path.unlink()
            return True

        return False

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件删除失败: {str(e)}"
        )


# ========== 文件信息 ==========

def get_file_info(file_path: str) -> dict:
    """
    获取文件信息

    参数:
        file_path: 文件路径

    返回:
        dict: 文件信息
    """
    path = Path(file_path)

    if not path.exists():
        raise BadRequestException("文件不存在")

    stat = path.stat()

    return {
        "filename": path.name,
        "size": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "created_at": stat.st_ctime,
        "modified_at": stat.st_mtime,
        "extension": path.suffix,
        "mime_type": get_file_mime_type(path.name)
    }


# ========== 批量操作 ==========

async def save_multiple_files(
    files: list[UploadFile],
    destination_dir: Path,
    max_total_size: int = 20 * 1024 * 1024,  # 20MB
    max_file_count: int = 10
) -> list[dict]:
    """
    批量保存多个文件

    参数:
        files: UploadFile对象列表
        destination_dir: 目标目录
        max_total_size: 总大小限制
        max_file_count: 最大文件数量

    返回:
        list[dict]: 文件信息列表

    异常:
        BadRequestException: 验证失败
    """
    # 1. 检查文件数量
    if len(files) > max_file_count:
        raise BadRequestException(
            f"文件数量过多。最多允许: {max_file_count}，"
            f"实际: {len(files)}"
        )

    # 2. 保存文件
    saved_files = []
    total_size = 0

    for file in files:
        file_path, file_name, file_size = await save_upload_file(
            file,
            destination_dir
        )

        total_size += file_size

        # 检查总大小
        if total_size > max_total_size:
            # 删除已保存的文件
            for saved_file in saved_files:
                await delete_file(saved_file["path"])

            raise BadRequestException(
                f"文件总大小过大。"
                f"最大允许: {max_total_size / (1024 * 1024):.0f}MB"
            )

        saved_files.append({
            "path": file_path,
            "filename": file_name,
            "size": file_size
        })

    return saved_files


# ========== 安全检查 ==========

def is_safe_path(file_path: str, base_dir: Path) -> bool:
    """
    检查文件路径是否安全（防止路径遍历攻击）

    参数:
        file_path: 文件路径
        base_dir: 基础目录

    返回:
        bool: 路径是否安全
    """
    try:
        # 解析路径
        path = Path(file_path).resolve()
        base = base_dir.resolve()

        # 检查是否在基础目录内
        return str(path).startswith(str(base))

    except Exception:
        return False


def validate_file_path(file_path: str, allowed_dirs: list[Path]) -> bool:
    """
    验证文件路径是否在允许的目录内

    参数:
        file_path: 文件路径
        allowed_dirs: 允许的目录列表

    返回:
        bool: 路径是否有效
    """
    try:
        path = Path(file_path).resolve()

        for allowed_dir in allowed_dirs:
            allowed = allowed_dir.resolve()
            if str(path).startswith(str(allowed)):
                return True

        return False

    except Exception:
        return False
