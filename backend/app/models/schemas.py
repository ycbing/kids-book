# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AgeGroup(str, Enum):
    TODDLER = "0-3岁"
    PRESCHOOL = "3-6岁"
    EARLY_ELEMENTARY = "6-9岁"
    ELEMENTARY = "9-12岁"

class ArtStyle(str, Enum):
    WATERCOLOR = "水彩风格"
    CARTOON = "卡通风格"
    REALISTIC = "写实风格"
    FLAT = "扁平插画"
    HAND_DRAWN = "手绘风格"
    ANIME = "动漫风格"
    PAPER_CUT = "剪纸风格"
    OIL_PAINTING = "油画风格"

# 绘本创建请求
class BookCreateRequest(BaseModel):
    title: Optional[str] = None
    theme: str = Field(..., description="故事主题，如：友谊、勇气、环保")
    keywords: List[str] = Field(default=[], description="关键词列表")
    target_age: AgeGroup = Field(default=AgeGroup.PRESCHOOL)
    style: ArtStyle = Field(default=ArtStyle.WATERCOLOR)
    page_count: int = Field(default=8, ge=4, le=20)
    custom_prompt: Optional[str] = Field(None, description="自定义故事要求")

class PageContent(BaseModel):
    page_number: int
    text_content: str
    image_prompt: str
    image_url: Optional[str] = None

class BookResponse(BaseModel):
    id: int
    title: str
    description: str
    theme: str
    target_age: str
    style: str
    status: str
    cover_image: Optional[str]
    pages: List[PageContent]
    created_at: datetime
    
    class Config:
        from_attributes = True

# 故事生成请求
class StoryGenerateRequest(BaseModel):
    theme: str
    keywords: List[str] = []
    target_age: AgeGroup
    page_count: int = 8
    custom_prompt: Optional[str] = None

class StoryPage(BaseModel):
    page_number: int
    text: str
    scene_description: str
    image_prompt: str

class StoryResponse(BaseModel):
    title: str
    description: str
    pages: List[StoryPage]

# 图像生成请求
class ImageGenerateRequest(BaseModel):
    prompt: str
    style: ArtStyle
    negative_prompt: Optional[str] = None

class ImageResponse(BaseModel):
    image_url: str
    revised_prompt: Optional[str] = None

# 导出请求
class ExportRequest(BaseModel):
    book_id: int
    format: str = Field(default="pdf", pattern="^(pdf|png|jpg)$")
    quality: str = Field(default="high", pattern="^(low|medium|high)$")

# ==================== 认证相关模型 ====================

# 用户注册请求
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码")

# 用户登录请求
class UserLoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

# 用户响应
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Token响应
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
