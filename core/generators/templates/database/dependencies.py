"""数据库依赖注入文件生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="database",
    priority=32,
    requires=["DatabaseConnectionGenerator"],
    description="生成数据库依赖 (app/core/database/dependencies.py)"
)
class DatabaseDependenciesGenerator(BaseTemplateGenerator):
    """数据库依赖注入生成器"""

    def generate(self) -> None:
        """生成 app/core/database/dependencies.py"""
        # 仅在启用认证时生成 dependencies.py
        if not self.config_reader.has_auth():
            return

        db_type = self.config_reader.get_database_type()
        auth_type = self.config_reader.get_auth_type()

        # 根据数据库类型确定对应的管理器
        if db_type == "PostgreSQL":
            db_manager = "postgresql_manager"
            db_import = "from app.core.database.postgresql import postgresql_manager"
        else:  # MySQL
            db_manager = "mysql_manager"
            db_import = "from app.core.database.mysql import mysql_manager"

        imports = [
            "from fastapi import Depends, HTTPException, Response",
            "from sqlalchemy.ext.asyncio import AsyncSession",
            "from sqlalchemy import func",
        ]

        # 根据 ORM 类型添加不同的 select 导入
        orm_type = self.config_reader.get_orm_type()
        if orm_type == "SQLModel":
            imports.append("from sqlmodel import select")
        else:
            imports.append("from sqlalchemy import select")

        imports.extend([
            "from fastapi.security import APIKeyCookie",
            db_import,
            "from app.core.logger import logger_manager",
        ])

        # 根据认证类型生成不同的依赖注入内容
        if auth_type == "complete":
            imports.extend([
                "from app.crud.auth_crud import get_auth_crud",
                "from app.models.auth_model import Token, TokenType",
                "from app.core.security import security_manager",
                "from app.core.config.settings import settings",
            ])

            content = self._generate_complete_auth_dependencies(db_manager)
        else:  # basic
            imports.extend([
                "from app.crud.user_crud import get_user_crud",
                "from app.core.security import security_manager",
            ])

            content = self._generate_basic_auth_dependencies(db_manager)

        self.file_ops.create_python_file(
            file_path="app/core/database/dependencies.py",
            docstring="FastAPI 数据库依赖注入",
            imports=imports,
            content=content,
            overwrite=True
        )

    def _generate_complete_auth_dependencies(self, db_manager: str) -> str:
        """生成完整认证模式下的依赖注入代码"""
        return f'''get_access_token_cookie = APIKeyCookie(
    name="access_token",
    auto_error=False,
    scheme_name="Bearer",
    description="用于身份认证的访问令牌",
)

get_refresh_token_cookie = APIKeyCookie(
    name="refresh_token",
    auto_error=False,
    scheme_name="Bearer",
    description="用于刷新身份的刷新令牌",
)


class Dependencies:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_crud = get_auth_crud(db)
        self.{db_manager.split('_')[0]}_manager = {db_manager}
        self.security_manager = security_manager
        self.logger = logger_manager.get_logger(__name__)
    
    async def get_current_user(
        self,
        access_token: str = Depends(get_access_token_cookie),
        db: AsyncSession = Depends({db_manager}.get_db),
    ):
        """获取当前用户（需要认证）"""
        self.logger.info(
            f"调用 get_current_user，access_token: "
            f"{{'***' if access_token else 'None'}}"
        )
        
        if not access_token:
            self.logger.warning("请求中未提供 access_token")
            raise HTTPException(
                status_code=401,
                detail="未授权访问",
            )
        
        # 校验访问令牌
        try:
            self.logger.info("开始解析 access_token")
            token_data = security_manager.decode_token(access_token)
            
            if token_data:
                self.logger.info(
                    f"令牌解析成功，user_id: {{token_data.get('user_id')}}"
                )
                user_id = token_data.get("user_id")
                
                if user_id:
                    self.logger.info(f"在数据库中校验 token，user_id: {{user_id}}")
                    
                    # 在数据库中校验 access token 的有效性
                    valid_access_token = await db.execute(
                        select(Token).where(
                            Token.user_id == user_id,
                            Token.type == TokenType.access,
                            Token.is_active == True,
                            Token.expired_at > func.utc_timestamp(),
                        )
                    )
                    valid_token = valid_access_token.scalar_one_or_none()
                    
                    if valid_token:
                        self.logger.info(f"数据库中存在有效 token: {{valid_token.id}}")
                        
                        # 获取用户信息
                        user = await self.auth_crud.get_user_by_id(user_id)
                        
                        if (
                            user
                            and user.is_active
                            and user.is_verified
                            and not user.is_deleted
                        ):
                            self.logger.info(f"用户通过 access_token 认证: {{user.email}}")
                            return user
                        else:
                            self.logger.warning(
                                f"用户状态校验失败 - "
                                f"active: {{user.is_active if user else 'N/A'}}, "
                                f"verified: {{user.is_verified if user else 'N/A'}}, "
                                f"deleted: {{user.is_deleted if user else 'N/A'}}"
                            )
                    else:
                        self.logger.warning(f"数据库中未找到有效 token，user_id: {{user_id}}")
                else:
                    self.logger.warning("解析后的 token 中未包含 user_id")
            else:
                self.logger.warning("令牌解析结果为空")
        except Exception as e:
            self.logger.warning(f"access_token 校验失败: {{str(e)}}")
        
        # 所有校验失败，返回未授权
        self.logger.warning("所有令牌校验均失败")
        raise HTTPException(
            status_code=401,
            detail="未授权访问",
        )
    
    async def cleanup_tokens(
        self,
        response: Response,
    ) -> bool:
        """清理用户令牌（用于登出）"""
        response.delete_cookie(
            "access_token",
            domain=settings.domain.COOKIE_DOMAIN,
            path="/",
        )
        self.logger.info("access_token Cookie 已删除")
        
        response.delete_cookie(
            "refresh_token",
            domain=settings.domain.COOKIE_DOMAIN,
            path="/",
        )
        self.logger.info("refresh_token Cookie 已删除")
        
        return True
'''

    def _generate_basic_auth_dependencies(self, db_manager: str) -> str:
        """生成基础认证模式下的依赖注入代码"""
        return f'''get_access_token_cookie = APIKeyCookie(
    name="access_token",
    auto_error=False,
    scheme_name="Bearer",
    description="用于身份认证的访问令牌",
)


class Dependencies:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_crud = get_user_crud(db)
        self.{db_manager.split('_')[0]}_manager = {db_manager}
        self.security_manager = security_manager
        self.logger = logger_manager.get_logger(__name__)
    
    async def get_current_user(
        self,
        access_token: str = Depends(get_access_token_cookie),
        db: AsyncSession = Depends({db_manager}.get_db),
    ):
        """获取当前用户（需要认证）"""
        self.logger.info(
            f"调用 get_current_user，access_token: "
            f"{{'***' if access_token else 'None'}}"
        )
        
        if not access_token:
            self.logger.warning("请求中未提供 access_token")
            raise HTTPException(
                status_code=401,
                detail="未授权访问",
            )
        
        # 校验访问令牌
        try:
            self.logger.info("开始解析 access_token")
            token_data = security_manager.decode_token(access_token)
            
            if token_data:
                self.logger.info(
                    f"令牌解析成功，user_id: {{token_data.get('user_id')}}"
                )
                user_id = token_data.get("user_id")
                
                if user_id:
                    # 从数据库获取用户信息
                    user = await self.user_crud.get_user_by_id(user_id)
                    
                    if user and user.is_active and not user.is_deleted:
                        self.logger.info(f"用户认证成功: {{user.email}}")
                        return user
                    else:
                        self.logger.warning(
                            f"用户状态校验失败 - "
                            f"active: {{user.is_active if user else 'N/A'}}, "
                            f"deleted: {{user.is_deleted if user else 'N/A'}}"
                        )
                else:
                    self.logger.warning("解析后的 token 中未包含 user_id")
            else:
                self.logger.warning("令牌解析结果为空")
        except Exception as e:
            self.logger.warning(f"access_token 校验失败: {{str(e)}}")
        
        # 校验失败，返回未授权
        self.logger.warning("令牌校验失败")
        raise HTTPException(
            status_code=401,
            detail="未授权访问",
        )
'''
