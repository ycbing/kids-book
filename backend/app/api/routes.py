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

@router.post("/books", response_model=Dict[str, Any])
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

@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取绘本详情"""

    book = book_service.get_book(db, book_id)
    if not book:
        raise NotFoundException(f"绘本 {book_id} 不存在")

    return book

@router.get("/books", response_model=List[BookResponse])
async def list_books(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取绘本列表"""
    
    user_id = 1  # 临时用户ID
    return book_service.get_user_books(db, user_id, skip, limit)

@router.delete("/books/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    """删除绘本"""

    success = book_service.delete_book(db, book_id)
    if not success:
        raise NotFoundException(f"绘本 {book_id} 不存在")

    return {"message": "删除成功"}

@router.put("/books/{book_id}/pages/{page_number}")
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

@router.post("/generate/story", response_model=StoryResponse)
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

@router.post("/generate/image", response_model=ImageResponse)
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

@router.post("/books/{book_id}/regenerate-image/{page_number}")
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

@router.post("/books/{book_id}/export")
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

@router.get("/download/{book_id}/{filename}")
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

@router.websocket("/ws/{client_id}")
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

@router.get("/tasks/{task_id}")
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


@router.post("/tasks/{task_id}/cancel")
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
