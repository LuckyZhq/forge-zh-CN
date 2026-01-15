"""配置文件读取模块"""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigReader:
    """配置文件读取器

    负责读取和解析 .forge/config.json 配置文件
    """

    # 配置验证规则
    REQUIRED_FIELDS = ['project_name', 'database', 'features']
    VALID_DATABASE_TYPES = ['PostgreSQL', 'MySQL', 'SQLite']
    VALID_ORM_TYPES = ['SQLModel']
    VALID_AUTH_TYPES = ['basic', 'complete']

    def __init__(self, project_path: Path):
        """初始化配置读取器

        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path)
        self.config: Optional[Dict[str, Any]] = None
        self.config_file = self.project_path / ".forge" / "config.json"

    def load_config(self) -> Dict[str, Any]:
        """从 .forge/config.json 加载配置

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
        """
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"配置文件未找到: {self.config_file}\n"
                f"请先运行 'forge init' 创建配置。"
            )

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(
                f"配置文件中存在无效的 JSON: {e}"
            )

        return self.config

    def validate_config(self) -> bool:
        """验证配置文件完整性

        Returns:
            配置是否有效

        Raises:
            ConfigValidationError: 配置验证失败
        """
        if not self.config:
            raise ConfigValidationError("配置未加载")

        # 检查必需字段
        self._validate_required_fields()

        # 验证数据库配置
        self._validate_database_config()

        # 验证身份验证配置
        self._validate_auth_config()

        return True

    def _validate_required_fields(self) -> None:
        """验证必需字段"""
        missing_fields = [
            field for field in self.REQUIRED_FIELDS
            if field not in self.config
        ]
        if missing_fields:
            raise ConfigValidationError(
                f"缺少必需字段: {', '.join(missing_fields)}"
            )

    def _validate_database_config(self) -> None:
        """验证数据库配置"""
        db_config = self.config.get('database')
        if not db_config:
            raise ConfigValidationError("数据库配置是必需的")

        if 'type' not in db_config:
            raise ConfigValidationError("数据库类型是必需的")

        if db_config['type'] not in self.VALID_DATABASE_TYPES:
            raise ConfigValidationError(
                f"无效的数据库类型: {db_config['type']}. "
                f"有效类型: {', '.join(self.VALID_DATABASE_TYPES)}"
            )

        if 'orm' not in db_config:
            raise ConfigValidationError("ORM 类型是必需的")

        if db_config['orm'] not in self.VALID_ORM_TYPES:
            raise ConfigValidationError(
                f"无效的 ORM 类型: {db_config['orm']}. "
                f"有效类型: {', '.join(self.VALID_ORM_TYPES)}"
            )

    def _validate_auth_config(self) -> None:
        """验证身份验证配置"""
        features = self.config.get('features', {})
        auth_config = features.get('auth', {})
        auth_type = auth_config.get('type')

        if not auth_type or auth_type == 'none':
            raise ConfigValidationError(
                "身份验证是必需的但未配置"
            )

        if auth_type not in self.VALID_AUTH_TYPES:
            raise ConfigValidationError(
                f"无效的身份验证类型: {auth_type}. "
                f"有效类型: {', '.join(self.VALID_AUTH_TYPES)}"
            )

    # ========== 配置获取方法 ==========

    def get_project_name(self) -> str:
        """获取项目名称"""
        return self.config.get('project_name', 'my-project')

    def get_database_config(self) -> Dict[str, str]:
        """获取数据库配置"""
        db_config = self.config.get('database')
        if not db_config:
            raise ConfigValidationError("数据库配置是必需的")
        return db_config

    def get_database_type(self) -> str:
        """获取数据库类型"""
        return self.get_database_config()['type']

    def get_orm_type(self) -> str:
        """获取 ORM 类型"""
        return self.get_database_config()['orm']

    def get_migration_tool(self) -> Optional[str]:
        """获取迁移工具"""
        return self.get_database_config().get('migration_tool')

    def has_migration(self) -> bool:
        """检查数据库迁移是否启用"""
        return self.get_migration_tool() is not None

    def get_features(self) -> Dict[str, Any]:
        """获取功能配置"""
        return self.config.get('features', {})

    def has_auth(self) -> bool:
        """检查身份验证是否启用(身份验证现在是必需的)"""
        return True

    def get_auth_type(self) -> str:
        """获取身份验证类型"""
        features = self.get_features()
        auth_config = features.get('auth', {})
        auth_type = auth_config.get('type')
        if not auth_type or auth_type == 'none':
            raise ConfigValidationError(
                "身份验证是必需的但未配置"
            )
        return auth_type

    def has_refresh_token(self) -> bool:
        """检查刷新令牌是否启用"""
        features = self.get_features()
        auth_config = features.get('auth', {})
        return auth_config.get('refresh_token', False)

    def has_cors(self) -> bool:
        """检查 CORS 是否启用"""
        return self.get_features().get('cors', False)

    def has_dev_tools(self) -> bool:
        """检查开发工具是否包含"""
        return self.get_features().get('dev_tools', False)

    def has_testing(self) -> bool:
        """检查测试工具是否包含"""
        return self.get_features().get('testing', False)

    def has_docker(self) -> bool:
        """检查 Docker 配置是否包含"""
        return self.get_features().get('docker', False)

    def has_redis(self) -> bool:
        """检查 Redis 是否启用"""
        redis_config = self.get_features().get('redis', False)
        # 支持布尔值和对象格式
        if isinstance(redis_config, bool):
            return redis_config
        return redis_config.get('enabled', False)

    def get_redis_features(self) -> list:
        """获取 Redis 功能列表"""
        redis_config = self.get_features().get('redis', {})
        if isinstance(redis_config, bool):
            return ["caching", "sessions", "queues"] if redis_config else []
        return redis_config.get('features', [])

    def has_celery(self) -> bool:
        """检查 Celery 是否启用"""
        celery_config = self.get_features().get('celery', False)
        # 支持布尔值和对象格式
        if isinstance(celery_config, bool):
            return celery_config
        return celery_config.get('enabled', False)

    def get_celery_features(self) -> list:
        """获取 Celery 功能列表"""
        celery_config = self.get_features().get('celery', {})
        if isinstance(celery_config, bool):
            return ["background_tasks", "scheduled_tasks", "task_monitoring"] if celery_config else []
        return celery_config.get('features', [])

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """获取元数据信息"""
        return self.config.get('metadata')

    def get_created_at(self) -> Optional[str]:
        """获取配置创建时间"""
        metadata = self.get_metadata()
        return metadata.get('created_at') if metadata else None

    def get_forge_version(self) -> Optional[str]:
        """获取 Forge 版本"""
        metadata = self.get_metadata()
        return metadata.get('forge_version') if metadata else None
