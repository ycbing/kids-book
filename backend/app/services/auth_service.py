# backend/app/services/auth_service.py
"""
用户认证服务
处理用户注册、登录、JWT token生成和验证
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models.database import User
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """用户认证服务"""

    def __init__(self):
        self.secret_key = self._get_secret_key()
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24小时

    def _get_secret_key(self) -> str:
        """获取JWT密钥"""
        # 优先使用环境变量中的JWT密钥
        jwt_secret = getattr(settings, 'JWT_SECRET_KEY', None)
        if jwt_secret:
            return jwt_secret

        # 开发环境使用默认密钥（生产环境必须配置）
        if settings.DEBUG:
            logger.warning("⚠️  使用开发环境默认JWT密钥，生产环境必须配置JWT_SECRET_KEY！")
            return "dev-secret-key-change-in-production"

        raise ValueError(
            "生产环境必须配置 JWT_SECRET_KEY 环境变量！"
            "请在 .env 文件中添加: JWT_SECRET_KEY=your-secret-key-here"
        )

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """加密密码"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict) -> str:
        """创建JWT访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[int]:
        """验证JWT令牌并返回用户ID"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            user_id: int = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError as e:
            logger.warning(f"JWT验证失败: {e}")
            return None

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """验证用户凭据"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, db: Session, username: str, email: str, password: str) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            if existing_user.username == username:
                raise ValueError("用户名已存在")
            if existing_user.email == email:
                raise ValueError("邮箱已被注册")

        # 创建用户
        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"新用户注册成功: {username} (ID: {user.id})")
        return user

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """通过ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()

# 创建认证服务实例
auth_service = AuthService()
