"""令牌 Schema 生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="schema",
    priority=51,
    requires=["TokenModelGenerator"],
    enabled_when=lambda c: c.get_auth_type() == 'complete',
    description="生成令牌 Schema (app/schemas/token.py)"
)
class TokenSchemaGenerator(BaseTemplateGenerator):
    """令牌 Schema 文件生成器"""

    def generate(self) -> None:
        """生成令牌 Schema 文件

        注意：当启用完整 JWT 认证时，此生成器由编排器调用
        """
        self._generate_token_schemas()

    def _generate_token_schemas(self) -> None:
        """生成令牌 Schemas"""
        imports = [
            "from datetime import datetime",
            "from typing import Optional",
            "from pydantic import BaseModel, Field, ConfigDict",
        ]

        content = '''# ========== 刷新令牌 Schemas ==========

class RefreshTokenBase(BaseModel):
    """刷新令牌基础 Schema"""
    device_name: Optional[str] = Field(None, max_length=200)
    device_type: Optional[str] = Field(None, max_length=50)


class RefreshTokenCreate(RefreshTokenBase):
    """刷新令牌创建 Schema"""
    user_id: int
    token: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class RefreshTokenResponse(RefreshTokenBase):
    """刷新令牌响应 Schema"""
    id: int
    user_id: int
    expires_at: datetime
    is_revoked: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求 Schema"""
    refresh_token: str = Field(..., description="用于刷新访问令牌的刷新令牌")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class RefreshTokenRevoke(BaseModel):
    """撤销刷新令牌 Schema"""
    token: Optional[str] = Field(None, description="要撤销的令牌")


# ========== 验证码 Schemas ==========

class VerificationCodeBase(BaseModel):
    """验证码基础 Schema"""
    code_type: str = Field(..., description="验证码类型（email_verification、password_reset 等）")


class VerificationCodeCreate(VerificationCodeBase):
    """验证码创建 Schema"""
    user_id: int
    code: str
    expires_at: datetime
    max_attempts: int = 5


class VerificationCodeResponse(VerificationCodeBase):
    """验证码响应 Schema"""
    id: int
    user_id: int
    expires_at: datetime
    is_used: bool
    attempts: int
    max_attempts: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VerificationCodeVerify(BaseModel):
    """验证码验证 Schema"""
    code: str = Field(..., min_length=4, max_length=10)
    code_type: str = Field(..., description="验证码类型（email_verification、password_reset 等）")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "123456",
                "code_type": "email_verification"
            }
        }
    )
'''

        self.file_ops.create_python_file(
            file_path="app/schemas/token.py",
            docstring="令牌相关 Pydantic Schemas - 完整 JWT 认证",
            imports=imports,
            content=content,
            overwrite=True
        )
