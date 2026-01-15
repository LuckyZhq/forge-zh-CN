"""Docker Compose 生成器"""
from core.decorators import Generator
from ..templates.base import BaseTemplateGenerator


@Generator(
    category="deployment",
    priority=101,
    requires=["DockerfileGenerator"],
    enabled_when=lambda c: c.has_docker(),
    description="生成 docker-compose.yml"
)
class DockerComposeGenerator(BaseTemplateGenerator):
    """Docker Compose 文件生成器"""

    def generate(self) -> None:
        """生成 docker-compose.yml 文件"""
        content = self._build_version()
        content += self._build_services()
        content += self._build_volumes()
        content += self._build_networks()

        self.file_ops.create_file(
            file_path="docker-compose.yml",
            content=content,
            overwrite=True
        )

    def _build_version(self) -> str:
        """构建版本声明"""
        return ''

    def _build_services(self) -> str:
        """构建服务配置"""
        content = '''services:
  app:
    build: .
    container_name: {project_name}
    ports:
      - "8000:8000"
    env_file:
      - ./secret/.env.production
    environment:
      - ENV=production
'''.format(project_name=self.config_reader.get_project_name())

        # 添加数据库连接环境变量
        db_type = self.config_reader.get_database_type()
        if db_type == "PostgreSQL":
            content += '''      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/{project_name}
'''.format(project_name=self.config_reader.get_project_name())
        elif db_type == "MySQL":
            content += '''      - DATABASE_URL=mysql+aiomysql://root:mysql@db:3306/{project_name}
'''.format(project_name=self.config_reader.get_project_name())

        # 如果启用 Redis，添加 Redis 环境变量
        if self.config_reader.has_redis():
            content += '''      - REDIS_CONNECTION_URL=redis://redis:6379
'''

        # 如果启用 Celery，添加 Celery 环境变量
        if self.config_reader.has_celery():
            content += '''      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
'''

        # 构建带有适当条件的依赖关系
        content += '''    volumes:
      - ./app:/app/app
    depends_on:
      db-migrate:
        condition: service_completed_successfully
'''

        if self.config_reader.has_redis():
            content += '''      redis:
        condition: service_started
'''

        content += '''    restart: unless-stopped
    networks:
      - app-network

'''

        # 添加数据库服务
        content += self._build_database_service()

        # 添加数据库迁移服务
        content += self._build_database_migration_service()

        # 如果启用 Redis，添加 Redis 服务
        if self.config_reader.has_redis():
            content += self._build_redis_service()

        # 如果启用 Celery，添加 Celery 服务
        if self.config_reader.has_celery():
            content += self._build_celery_services()

        return content

    def _build_database_service(self) -> str:
        """构建数据库服务配置"""
        db_type = self.config_reader.get_database_type()
        project_name = self.config_reader.get_project_name()

        if db_type == "PostgreSQL":
            return '''  db:
    image: postgres:15-alpine
    container_name: {project_name}_db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB={project_name}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      timeout: 20s
      retries: 10

'''.format(project_name=project_name)

        elif db_type == "MySQL":
            return '''  db:
    image: mysql:8.0
    container_name: {project_name}_db
    environment:
      - MYSQL_ROOT_PASSWORD=mysql
      - MYSQL_DATABASE={project_name}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-pmysql"]
      timeout: 20s
      retries: 10

'''.format(project_name=project_name)

        return ''

    def _build_database_migration_service(self) -> str:
        """构建数据库迁移服务配置"""
        project_name = self.config_reader.get_project_name()

        # 构建环境变量
        env_vars = '''      - ENV=production
'''

        # 添加数据库连接
        db_type = self.config_reader.get_database_type()
        if db_type == "PostgreSQL":
            env_vars += '''      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/{project_name}
'''.format(project_name=project_name)
        elif db_type == "MySQL":
            env_vars += '''      - DATABASE_URL=mysql+aiomysql://root:mysql@db:3306/{project_name}
'''.format(project_name=project_name)

        return '''  db-migrate:
    build: .
    container_name: {project_name}_db_migrate
    command: sh -c "alembic revision --autogenerate -m 'Auto migration' && alembic upgrade head"
    env_file:
      - ./secret/.env.production
    environment:
{env_vars}    volumes:
      - ./app:/app/app
      - ./alembic:/app/alembic
      - ./alembic.ini:/app/alembic.ini
    depends_on:
      db:
        condition: service_healthy
    networks:
      - app-network

'''.format(project_name=project_name, env_vars=env_vars)

    def _build_redis_service(self) -> str:
        """构建 Redis 服务配置"""
        project_name = self.config_reader.get_project_name()

        return '''  redis:
    image: redis:7-alpine
    container_name: {project_name}_redis
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - app-network

'''.format(project_name=project_name)

    def _build_celery_services(self) -> str:
        """构建 Celery 服务配置"""
        project_name = self.config_reader.get_project_name()

        # 构建环境变量
        env_vars = '''      - ENV=production
'''

        # 添加数据库连接
        db_type = self.config_reader.get_database_type()
        if db_type == "PostgreSQL":
            env_vars += '''      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/{project_name}
'''.format(project_name=project_name)
        elif db_type == "MySQL":
            env_vars += '''      - DATABASE_URL=mysql+aiomysql://root:mysql@db:3306/{project_name}
'''.format(project_name=project_name)

        # 添加 Redis 和 Celery 环境变量
        env_vars += '''      - REDIS_CONNECTION_URL=redis://redis:6379
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
'''

        # 构建带有适当条件的依赖关系
        depends_on_str = '''      db-migrate:
        condition: service_completed_successfully
      redis:
        condition: service_started
'''

        return '''  celery-worker:
    build: .
    container_name: {project_name}_celery_worker
    command: celery -A app.core.celery.celery_app worker --loglevel=info
    env_file:
      - ./secret/.env.production
    environment:
{env_vars}    volumes:
      - ./app:/app/app
    depends_on:
{depends_on_str}    restart: unless-stopped
    networks:
      - app-network

  celery-beat:
    build: .
    container_name: {project_name}_celery_beat
    command: celery -A app.core.celery.celery_app beat --loglevel=info
    env_file:
      - ./secret/.env.production
    environment:
{env_vars}    volumes:
      - ./app:/app/app
    depends_on:
{depends_on_str}    restart: unless-stopped
    networks:
      - app-network

'''.format(project_name=project_name, env_vars=env_vars, depends_on_str=depends_on_str)

    def _build_volumes(self) -> str:
        """构建数据卷配置"""
        db_type = self.config_reader.get_database_type()

        content = '''volumes:
'''

        if db_type == "PostgreSQL":
            content += '''  postgres_data:

'''
        elif db_type == "MySQL":
            content += '''  mysql_data:

'''

        return content

    def _build_networks(self) -> str:
        """构建网络配置"""
        return '''networks:
  app-network:
    driver: bridge
'''
