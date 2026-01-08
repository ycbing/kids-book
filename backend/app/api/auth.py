# backend/app/api/auth.py
"""
用户认证API路由
提供用户注册、登录、token验证等接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.models.database import get_db, User
from app.models.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse
)
from app.services.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()

# ==================== 依赖注入 ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户

    Args:
        credentials: HTTP Bearer token
        db: 数据库会话

    Returns:
        当前登录的用户对象

    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 验证token
    token = credentials.credentials
    user_id = auth_service.verify_token(token)

    if user_id is None:
        raise credentials_exception

    # 获取用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user

# ==================== 认证端点 ====================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册

    创建新用户账号并返回访问令牌

    Args:
        request: 注册请求（用户名、邮箱、密码）
        db: 数据库会话

    Returns:
        访问令牌和用户信息

    Raises:
        HTTPException: 400 如果用户名或邮箱已存在
    """
    try:
        # 创建用户
        user = auth_service.create_user(
            db,
            username=request.username,
            email=request.email,
            password=request.password
        )

        # 生成访问令牌
        access_token = auth_service.create_access_token(
            data={"sub": user.id}
        )

        logger.info(f"用户注册成功: {request.username}")

        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录

    验证用户凭据并返回访问令牌

    Args:
        request: 登录请求（用户名、密码）
        db: 数据库会话

    Returns:
        访问令牌和用户信息

    Raises:
        HTTPException: 401 如果用户名或密码错误
    """
    # 验证用户
    user = auth_service.authenticate_user(
        db,
        username=request.username,
        password=request.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成访问令牌
    access_token = auth_service.create_access_token(
        data={"sub": user.id}
    )

    logger.info(f"用户登录成功: {request.username}")

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息

    需要认证：是

    Returns:
        当前登录用户的信息
    """
    return UserResponse.model_validate(current_user)

@router.post("/verify")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    验证访问令牌是否有效

    Args:
        credentials: HTTP Bearer token

    Returns:
        验证结果
    """
    token = credentials.credentials
    user_id = auth_service.verify_token(token)

    if user_id is None:
        return {"valid": False}

    return {"valid": True, "user_id": user_id}
