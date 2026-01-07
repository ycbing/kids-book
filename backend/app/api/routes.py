# backend/app/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket
from sqlalchemy.orm import Session
from typing import List
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

@router.post("/books", response_model=BookResponse)
async def create_book(
    request: BookCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建新绘本并开始生成"""
    
    # 临时用户ID（实际应从认证中获取）
    user_id = 1
    
    # 创建绘本记录
    book = await book_service.create_book(db, request, user_id)
    
    # 后台生成内容
    background_tasks.add_task(
        book_service.generate_book_content,
        db, book.id, request
    )
    
    return book_service.get_book(db, book.id)

@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取绘本详情"""
    
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="绘本不存在")
    
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
        raise HTTPException(status_code=404, detail="绘本不存在")
    
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
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# ============ AI生成API ============

@router.post("/generate/story", response_model=StoryResponse)
async def generate_story(request: StoryGenerateRequest):
    """单独生成故事（不保存）"""
    
    try:
        story = await ai_service.generate_story(request)
        return story
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate/image", response_model=ImageResponse)
async def generate_image(request: ImageGenerateRequest):
    """单独生成图片"""
    
    try:
        image = await ai_service.generate_image(request)
        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/books/{book_id}/regenerate-image/{page_number}")
async def regenerate_page_image(
    book_id: int,
    page_number: int,
    style: str = None,
    db: Session = Depends(get_db)
):
    """重新生成某页的配图"""
    
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="绘本不存在")
    
    page = next((p for p in book.pages if p.page_number == page_number), None)
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    try:
        from app.models.schemas import ArtStyle
        art_style = ArtStyle(style) if style else ArtStyle(book.style)
        
        request = ImageGenerateRequest(
            prompt=page.image_prompt,
            style=art_style
        )
        result = await ai_service.generate_image(request)
        
        # 更新页面图片
        book_service.update_page(db, book_id, page_number, image_url=result.image_url)
        
        return {"image_url": result.image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        raise HTTPException(status_code=404, detail="绘本不存在")
    
    try:
        if request.format == "pdf":
            output_path = await export_service.export_to_pdf(book, request.quality)
        else:
            output_paths = await export_service.export_to_images(book, request.format)
            output_path = output_paths[0] if output_paths else None
        
        return {
            "message": "导出成功",
            "download_url": f"/api/v1/download/{output_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
