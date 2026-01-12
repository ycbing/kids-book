# backend/app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pathlib import Path
import asyncio
import json

from app.models.database import get_db, User
from app.models.schemas import (
    BookCreateRequest, BookResponse,
    StoryGenerateRequest, StoryResponse,
    ImageGenerateRequest, ImageResponse,
    ExportRequest
)
from app.services.book_service import book_service
from app.services.ai_service import ai_service
from app.services.export_service import export_service
from app.services.book_tasks import generate_book_content_task, regenerate_page_image_task
from app.core.exceptions import NotFoundException, BadRequestException
from app.core.rate_limit import rate_limit, RATE_LIMIT_CONFIGS

router = APIRouter()

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_progress(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

manager = ConnectionManager()

# ============ 绘本相关API ============

@router.post(
    "/books",
    response_model=Dict[str, Any],
    summary="创建新绘本",
    description="""
    创建一个新的AI绘本并自动开始生成内容。

    **生成流程**:
    1. 创建绘本记录（初始状态: draft）
    2. 启动后台异步任务
    3. 生成故事文本（根据主题和关键词）
    4. 逐页生成配图（根据文本和风格）
    5. 更新绘本状态为completed

    **预计时间**: 8页绘本约需2-3分钟，16页约需4-6分钟

    **风格选项**:
    - 水彩风格 (watercolor): 温柔和艺术感
    - 卡通风格 (cartoon): 活泼有趣
    - 素描风格 (sketch): 简洁黑白
    - 油画风格 (oil): 质感丰富
    """,
    responses={
        200: {"description": "绘本创建成功，返回book_id和task_id"},
        400: {"description": "请求参数错误"},
        401: {"description": "未授权"},
        429: {"description": "请求过于频繁，请稍后重试"},
        500: {"description": "服务器内部错误"}
    },
    tags=["绘本管理"]
)
@rate_limit(
    max_requests=RATE_LIMIT_CONFIGS["strict"][0],
    window_seconds=RATE_LIMIT_CONFIGS["strict"][1]
)
async def create_book(
    request: BookCreateRequest,
    db: Session = Depends(get_db)
):
    """创建新绘本并启动Celery异步生成任务"""

    # 临时用户ID（实际应从认证中获取）
    user_id = 1

    # 创建绘本记录
    book = await book_service.create_book(db, request, user_id)

    # 启动Celery异步任务
    task = generate_book_content_task.delay(
        book_id=book.id,
        request_data=request.dict(),
        user_id=user_id
    )

    logger.info(f"✅ 绘本创建成功 - Book ID: {book.id}, Task ID: {task.id}")

    return {
        "book_id": book.id,
        "task_id": task.id,
        "status": "generating",
        "message": "绘本已创建，正在生成内容..."
    }

@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    summary="获取绘本详情",
    description="""
    根据绘本ID获取完整的绘本信息，包括所有页面和配图。

    **返回信息**:
    - 绘本基本信息（标题、主题、风格等）
    - 所有页面列表（文本和配图URL）
    - 创建和更新时间
    - 当前状态

    **状态说明**:
    - draft: 草稿，正在生成中
    - generating: 内容生成中
    - completed: 生成完成
    - failed: 生成失败
    """,
    responses={
        200: {"description": "成功获取绘本详情"},
        404: {"description": "绘本不存在"}
    },
    tags=["绘本管理"]
)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取绘本详情"""

    book = book_service.get_book(db, book_id)
    if not book:
        raise NotFoundException(f"绘本 {book_id} 不存在")

    return book

@router.get(
    "/books",
    response_model=List[BookResponse],
    summary="获取绘本列表",
    description="""
    获取当前用户的绘本列表，支持分页。

    **分页参数**:
    - skip: 跳过的记录数（默认0）
    - limit: 返回的记录数（默认20，最大100）

    **排序**: 按创建时间倒序排列，最新的在前
    """,
    responses={
        200: {"description": "成功获取绘本列表"}
    },
    tags=["绘本管理"]
)
async def list_books(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取绘本列表"""

    user_id = 1  # 临时用户ID
    return book_service.get_user_books(db, user_id, skip, limit)

@router.delete(
    "/books/{book_id}",
    summary="删除绘本",
    description="""
    删除指定的绘本及其所有相关文件（包括配图）。

    **注意**: 此操作不可逆，删除后无法恢复
    """,
    responses={
        200: {"description": "删除成功"},
        404: {"description": "绘本不存在"}
    },
    tags=["绘本管理"]
)
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    """删除绘本"""

    success = book_service.delete_book(db, book_id)
    if not success:
        raise NotFoundException(f"绘本 {book_id} 不存在")

    return {"message": "删除成功"}

@router.put(
    "/books/{book_id}/pages/{page_number}",
    summary="更新页面内容",
    description="""
    更新指定页面的文本内容。

    **注意**: 不会重新生成配图，如需重新生成配图请使用regenerate-image接口
    """,
    responses={
        200: {"description": "更新成功"},
        404: {"description": "绘本或页面不存在"}
    },
    tags=["绘本管理"]
)
async def update_page(
    book_id: int,
    page_number: int,
    text_content: str = None,
    db: Session = Depends(get_db)
):
    """更新页面内容"""

    try:
        page = book_service.update_page(db, book_id, page_number, text_content)
        return {"message": "更新成功", "page": page}
    except NotFoundException:
        raise

# ============ AI生成API ============

@router.post(
    "/generate/story",
    response_model=StoryResponse,
    summary="生成故事文本",
    description="""
    单独生成故事文本，不创建绘本记录。

    **用途**: 预览故事内容，或用于自定义绘本创作

    **生成参数**:
    - theme: 故事主题（如：小兔子学会分享）
    - keywords: 关键词列表（如：友谊、分享）
    - target_age: 目标年龄段（如：3-6岁）
    """,
    responses={
        200: {"description": "故事生成成功"},
        429: {"description": "请求过于频繁"},
        500: {"description": "AI服务异常"}
    },
    tags=["图片生成"]
)
@rate_limit(
    max_requests=RATE_LIMIT_CONFIGS["strict"][0],
    window_seconds=RATE_LIMIT_CONFIGS["strict"][1]
)
async def generate_story(request: StoryGenerateRequest):
    """单独生成故事（不保存）"""

    try:
        story = await ai_service.generate_story(request)
        return story
    except Exception as e:
        # 全局异常处理器会捕获并转换为统一格式
        raise

@router.post(
    "/generate/image",
    response_model=ImageResponse,
    summary="生成配图",
    description="""
    根据文本描述生成单张配图。

    **参数说明**:
    - prompt: 图片描述文本
    - style: 艺术风格（watercolor、cartoon、sketch、oil）

    **返回**: 图片的URL和相关信息
    """,
    responses={
        200: {"description": "图片生成成功"},
        429: {"description": "请求过于频繁"},
        500: {"description": "AI服务异常"}
    },
    tags=["图片生成"]
)
@rate_limit(
    max_requests=RATE_LIMIT_CONFIGS["strict"][0],
    window_seconds=RATE_LIMIT_CONFIGS["strict"][1]
)
async def generate_image(request: ImageGenerateRequest):
    """单独生成图片"""

    try:
        image = await ai_service.generate_image(request)
        return image
    except Exception as e:
        raise

@router.post(
    "/books/{book_id}/regenerate-image/{page_number}",
    summary="重新生成配图",
    description="""
    为指定页面重新生成配图，可指定不同的风格。

    **流程**: 异步执行，返回task_id用于查询进度

    **参数**:
    - style: 可选，新的艺术风格（默认使用绘本原风格）
    """,
    responses={
        200: {"description": "重新生成任务已启动"},
        404: {"description": "绘本或页面不存在"},
        429: {"description": "请求过于频繁"}
    },
    tags=["图片生成"]
)
@rate_limit(
    max_requests=RATE_LIMIT_CONFIGS["strict"][0],
    window_seconds=RATE_LIMIT_CONFIGS["strict"][1]
)
async def regenerate_page_image(
    book_id: int,
    page_number: int,
    style: str = None,
    db: Session = Depends(get_db)
):
    """重新生成某页的配图（使用Celery异步任务）"""

    book = book_service.get_book(db, book_id)
    if not book:
        raise NotFoundException(f"绘本 {book_id} 不存在")

    page = next((p for p in book.pages if p.page_number == page_number), None)
    if not page:
        raise NotFoundException(f"绘本 {book_id} 的页面 {page_number} 不存在")

    # 启动Celery异步任务
    task = regenerate_page_image_task.delay(
        book_id=book_id,
        page_number=page_number,
        style=style or book.style
    )

    logger.info(f"✅ 配图重新生成任务已启动 - Book ID: {book_id}, Page: {page_number}, Task ID: {task.id}")

    return {
        "task_id": task.id,
        "status": "regenerating",
        "message": f"正在重新生成第 {page_number} 页配图..."
    }

# ============ 导出API ============

@router.post(
    "/books/{book_id}/export",
    summary="导出绘本",
    description="""
    将绘本导出为指定格式的文件。

    **支持格式**:
    - pdf: PDF文档，适合打印
    - png: PNG图片（每页一张）
    - jpg: JPEG图片（每页一张）

    **质量选项**:
    - standard: 标准质量，文件较小
    - high: 高质量，文件较大

    **流程**:
    1. 生成导出文件
    2. 返回文件名
    3. 使用/download接口下载文件
    """,
    responses={
        200: {"description": "导出成功，返回文件信息"},
        404: {"description": "绘本不存在"},
        400: {"description": "绘本无内容可导出"}
    },
    tags=["导出功能"]
)
async def export_book(
    book_id: int,
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """导出绘本"""

    book = book_service.get_book(db, book_id)
    if not book:
        raise NotFoundException(f"绘本 {book_id} 不存在")

    try:
        if request.format == "pdf":
            output_path = await export_service.export_to_pdf(book, request.quality)
            # 只返回文件名，不是完整路径
            filename = Path(output_path).name
            file_type = "pdf"
        else:
            output_paths = await export_service.export_to_images(book, request.format)
            if not output_paths:
                raise BadRequestException("导出失败，没有可导出的图片")
            # 返回第一个图片文件
            filename = Path(output_paths[0]).name
            file_type = request.format

        return {
            "message": "导出成功",
            "filename": filename,
            "file_type": file_type,
            "book_id": book_id
        }
    except (NotFoundException, BadRequestException):
        raise
    except Exception as e:
        raise

@router.get(
    "/download/{book_id}/{filename}",
    summary="下载导出文件",
    description="""
    下载已导出的绘本文件。

    **注意**: 需要先调用export接口生成文件
    """,
    responses={
        200: {"description": "文件下载"},
        404: {"description": "文件不存在"}
    },
    tags=["导出功能"]
)
async def download_file(book_id: int, filename: str):
    """下载导出的文件"""

    from app.config import settings
    from fastapi.responses import FileResponse

    # 安全检查：确保文件名不包含路径遍历
    if ".." in filename or "/" in filename or "\\" in filename:
        raise BadRequestException("无效的文件名：包含路径遍历字符")

    # 构建文件路径
    file_path = Path(settings.OUTPUT_DIR) / filename

    # 如果直接文件不存在，尝试在book_id子目录中查找
    if not file_path.exists():
        book_dir = Path(settings.OUTPUT_DIR) / f"book_{book_id}"
        file_path = book_dir / filename

    if not file_path.exists():
        raise NotFoundException(f"文件 {filename} 不存在")

    # 返回文件
    media_type = "application/pdf" if filename.endswith(".pdf") else "image/png"
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )

# ============ WebSocket进度推送 ============

@router.websocket(
    "/ws/{client_id}",
    name="WebSocket进度推送",
    summary="实时生成进度",
    description="""
    WebSocket连接，用于实时推送生成进度。

    **消息格式**:
    ```json
    {
      "type": "progress",
      "book_id": 123,
      "stage": "generating_story",
      "current": 3,
      "total": 8,
      "message": "正在生成第3页..."
    }
    ```

    **连接方式**: ws://host/api/v1/ws/{client_id}
    """,
    tags=["绘本管理"]
)
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket连接，用于推送生成进度"""

    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息
    except Exception:
        manager.disconnect(client_id)


# ============ Celery任务状态API ============

@router.get(
    "/tasks/{task_id}",
    summary="查询任务状态",
    description="""
    查询Celery异步任务的执行状态和进度。

    **任务状态**:
    - PENDING: 任务等待中
    - STARTED: 任务已开始
    - PROGRESS: 任务进行中（有进度信息）
    - SUCCESS: 任务完成
    - FAILURE: 任务失败

    **进度信息**: PROGRESS状态时包含current/total字段
    """,
    responses={
        200: {"description": "任务状态信息"},
        404: {"description": "任务不存在"}
    },
    tags=["绘本管理"]
)
async def get_task_status(task_id: str):
    """
    查询Celery任务状态

    返回任务状态信息，包括进度、结果等
    """
    from app.core.celery_app import celery_app

    # 获取任务结果
    result = celery_app.AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": result.state,
        "result": None if result.state == 'PENDING' else result.info if result.state != 'SUCCESS' else result.result
    }

    # 添加状态信息
    if result.state == 'PENDING':
        response["message"] = "任务等待中..."
    elif result.state == 'STARTED':
        response["message"] = "任务执行中..."
    elif result.state == 'PROGRESS':
        response["message"] = "任务进行中..."
        response["progress"] = result.info
    elif result.state == 'SUCCESS':
        response["message"] = "任务完成"
        response["result"] = result.result
    elif result.state == 'FAILURE':
        response["message"] = "任务失败"
        response["error"] = str(result.info)
    else:
        response["message"] = f"未知状态: {result.state}"

    return response


@router.post(
    "/tasks/{task_id}/cancel",
    summary="取消任务",
    description="""
    取消正在执行的异步任务。

    **注意**:
    - 只能取消尚未开始或正在执行的任务
    - 已完成的任务无法取消
    """,
    responses={
        200: {"description": "任务已取消"}
    },
    tags=["绘本管理"]
)
async def cancel_task(task_id: str):
    """
    取消正在执行的Celery任务

    注意：只能取消尚未开始的任务，正在执行的任务无法中断
    """
    from app.core.celery_app import celery_app

    # 撤销任务
    celery_app.control.revoke(task_id, terminate=True)

    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "任务已取消"
    }
