"""数据库备份任务生成器"""
from core.decorators import Generator
from pathlib import Path
from ..base import BaseTemplateGenerator


@Generator(
    category="task",
    priority=60,
    enabled_when=lambda c: c.has_celery(),
    description="生成数据库备份任务 (app/tasks/backup_database_task.py)"
)
class BackupDatabaseTaskGenerator(BaseTemplateGenerator):
    """数据库备份任务生成器"""

    def generate(self) -> None:
        """生成数据库备份任务文件"""
        project_name = self.config_reader.get_project_name()

        imports = [
            "import gzip",
            "import os",
            "import subprocess",
            "from datetime import datetime, timedelta",
            "from pathlib import Path",
            "from urllib.parse import urlparse",
            "from typing import Optional, List",
            "",
            "from app.core.celery import celery_app, with_db_init",
            "from app.core.config.settings import settings",
            "from app.core.logger import logger_manager",
        ]

        content = f'''logger = logger_manager.get_logger(__name__)


def _parse_database_url(database_url: str) -> dict:
    """解析数据库连接 URL
    
    参数：
        database_url: 数据库连接字符串，例如 mysql://user:password@host:port/database
        
    返回：
        dict: 包含 host、port、user、password、database、db_type 等信息
    """
    try:
        parsed = urlparse(database_url)
        
        # 处理不同类型的数据库
        if parsed.scheme.startswith('mysql'):
            db_type = 'mysql'
            host = parsed.hostname or 'localhost'
            port = parsed.port or 3306
            user = parsed.username or 'root'
            password = parsed.password or ''
            database = parsed.path.lstrip('/') if parsed.path else '{project_name}'
        elif parsed.scheme.startswith('postgresql'):
            db_type = 'postgresql'
            host = parsed.hostname or 'localhost'
            port = parsed.port or 5432
            user = parsed.username or 'postgres'
            password = parsed.password or ''
            database = parsed.path.lstrip('/') if parsed.path else '{project_name}'
        elif parsed.scheme.startswith('sqlite'):
            db_type = 'sqlite'
            # SQLite 使用文件路径作为数据库
            database_path = database_url.replace('sqlite:///', '').replace('sqlite://', '')
            return {{
                'db_type': db_type,
                'database_path': database_path,
                'database': Path(database_path).stem  # 使用文件名作为数据库名
            }}
        else:
            raise ValueError(f"不支持的数据库类型: {{parsed.scheme}}")
        
        return {{
            'db_type': db_type,
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }}
            
    except Exception as e:
        logger.error(f"解析数据库 URL 失败: {{e}}")
        raise


def _dump_database(db_config: dict, output_file: Path) -> bool:
    """导出数据库
    
    参数：
        db_config: 数据库配置字典
        output_file: 输出文件路径
        
    返回：
        bool: 是否导出成功
    """
    try:
        db_type = db_config['db_type']
        
        if db_type == 'mysql':
            return _dump_mysql(db_config, output_file)
        elif db_type == 'postgresql':
            return _dump_postgresql(db_config, output_file)
        elif db_type == 'sqlite':
            return _dump_sqlite(db_config, output_file)
        else:
            logger.error(f"不支持的数据库类型: {{db_type}}")
            return False
            
    except Exception as e:
        logger.error(f"导出数据库时发生错误: {{e}}")
        return False


def _dump_mysql(db_config: dict, output_file: Path) -> bool:
    """使用 mysqldump 导出 MySQL 数据库"""
    try:
        # 构建 mysqldump 命令
        cmd = [
            'mysqldump',
            f"--host={{db_config['host']}}",
            f"--port={{db_config['port']}}",
            f"--user={{db_config['user']}}",
            '--single-transaction',  # 保证数据一致性
            '--routines',  # 包含存储过程和函数
            '--triggers',  # 包含触发器
            '--events',  # 包含事件
            '--quick',  # 快速模式
            '--lock-tables=false',  # 不锁表
            db_config['database']
        ]
        
        # 通过环境变量设置密码（更安全）
        env = os.environ.copy()
        if db_config['password']:
            env['MYSQL_PWD'] = db_config['password']
        
        logger.info(f"开始导出 MySQL 数据库: {{db_config['database']}}")
        
        # 执行 mysqldump
        with open(output_file, 'wb') as f:
            subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                check=True
            )
        
        # 校验文件大小
        file_size = output_file.stat().st_size
        if file_size == 0:
            logger.error("导出的数据库文件为空")
            return False
        
        file_size_mb = file_size / 1024 / 1024
        logger.info(f"MySQL 数据库导出成功: {{output_file.name}} ({{file_size_mb:.2f}} MB)")
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"mysqldump 执行失败: {{error_msg}}")
        return False
    except Exception as e:
        logger.error(f"导出 MySQL 数据库时发生错误: {{e}}")
        return False


def _dump_postgresql(db_config: dict, output_file: Path) -> bool:
    """使用 pg_dump 导出 PostgreSQL 数据库"""
    try:
        # 构建 pg_dump 命令
        cmd = [
            'pg_dump',
            f"--host={{db_config['host']}}",
            f"--port={{db_config['port']}}",
            f"--username={{db_config['user']}}",
            '--no-password',  # 不交互式输入密码
            '--verbose',  # 详细输出
            '--clean',  # 包含清理命令
            '--if-exists',  # 如果存在则删除
            '--create',  # 包含创建数据库命令
            db_config['database']
        ]
        
        # 通过环境变量设置密码
        env = os.environ.copy()
        if db_config['password']:
            env['PGPASSWORD'] = db_config['password']
        
        logger.info(f"开始导出 PostgreSQL 数据库: {{db_config['database']}}")
        
        # 执行 pg_dump
        with open(output_file, 'wb') as f:
            subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                check=True
            )
        
        # 校验文件大小
        file_size = output_file.stat().st_size
        if file_size == 0:
            logger.error("导出的数据库文件为空")
            return False
        
        file_size_mb = file_size / 1024 / 1024
        logger.info(f"PostgreSQL 数据库导出成功: {{output_file.name}} ({{file_size_mb:.2f}} MB)")
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"pg_dump 执行失败: {{error_msg}}")
        return False
    except Exception as e:
        logger.error(f"导出 PostgreSQL 数据库时发生错误: {{e}}")
        return False


def _dump_sqlite(db_config: dict, output_file: Path) -> bool:
    """导出 SQLite 数据库"""
    try:
        database_path = Path(db_config['database_path'])
        
        if not database_path.exists():
            logger.error(f"SQLite 数据库文件不存在: {{database_path}}")
            return False
        
        logger.info(f"开始导出 SQLite 数据库: {{database_path}}")
        
        # 使用 sqlite3 命令导出
        cmd = [
            'sqlite3',
            str(database_path),
            '.dump'
        ]
        
        with open(output_file, 'wb') as f:
            subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                check=True
            )
        
        # 校验文件大小
        file_size = output_file.stat().st_size
        if file_size == 0:
            logger.error("导出的数据库文件为空")
            return False
        
        file_size_mb = file_size / 1024 / 1024
        logger.info(f"SQLite 数据库导出成功: {{output_file.name}} ({{file_size_mb:.2f}} MB)")
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"sqlite3 执行失败: {{error_msg}}")
        return False
    except Exception as e:
        logger.error(f"导出 SQLite 数据库时发生错误: {{e}}")
        return False


def _compress_file(input_file: Path, output_file: Path) -> bool:
    """压缩文件
    
    参数：
        input_file: 原始文件路径
        output_file: 压缩后文件路径
        
    返回：
        bool: 是否压缩成功
    """
    try:
        logger.info(f"开始压缩文件: {{input_file.name}}")
        
        with open(input_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb', compresslevel=6) as f_out:
                f_out.writelines(f_in)
        
        original_size = input_file.stat().st_size
        compressed_size = output_file.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        logger.info(
            f"压缩完成: {{output_file.name}} "
            f"({{compressed_size / 1024 / 1024:.2f}} MB, "
            f"压缩率: {{compression_ratio:.1f}}%)"
        )
        return True
        
    except Exception as e:
        logger.error(f"压缩文件时发生错误: {{e}}")
        return False


def _cleanup_old_backups(backup_dir: Path, database_name: str, retention_days: int) -> None:
    """清理过期的本地备份文件
    
    参数：
        backup_dir: 备份目录
        database_name: 数据库名称
        retention_days: 保留天数
    """
    if retention_days <= 0:
        logger.info("保留天数 <= 0，跳过清理步骤")
        return
    
    try:
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        logger.info(f"开始清理 {{cutoff_date.strftime('%Y-%m-%d')}} 之前的备份文件")
        
        pattern = f"{{database_name}}_backup_*.sql.gz"
        backup_files = list(backup_dir.glob(pattern))
        
        if not backup_files:
            logger.info("未找到任何备份文件")
            return
        
        files_to_delete = []
        for backup_file in backup_files:
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                files_to_delete.append(backup_file)
        
        if not files_to_delete:
            logger.info("没有需要清理的旧备份文件")
            return
        
        logger.info(f"发现 {{len(files_to_delete)}} 个需要删除的旧备份文件")
        
        success_count = 0
        for file_to_delete in files_to_delete:
            try:
                file_to_delete.unlink()
                logger.info(f"已删除旧备份文件: {{file_to_delete.name}}")
                success_count += 1
            except Exception as e:
                logger.error(f"删除文件 {{file_to_delete.name}} 失败: {{e}}")
        
        logger.info(f"清理完成，成功删除 {{success_count}} 个文件")
        
    except Exception as e:
        logger.error(f"清理旧备份文件时发生错误: {{e}}", exc_info=True)


@celery_app.task(
    name="backup_database_task",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 失败后 5 分钟重试
    time_limit=3600,         # 硬超时 1 小时
    soft_time_limit=3300,    # 软超时 55 分钟
)
@with_db_init
def backup_database_task(
    self,
    database_name: Optional[str] = None,
    retention_days: int = 30,
    backup_dir: Optional[str] = None
) -> dict:
    """将数据库备份到本地存储
    
    参数：
        database_name: 数据库名称，默认从 DATABASE_URL 中解析
        retention_days: 保留天数，超过该时间的备份会被自动删除（<=0 表示不清理）
        backup_dir: 备份目录，默认 ./backups/database
        
    返回：
        dict: 备份结果信息
    """
    sql_file = None
    gz_file = None
    
    try:
        # 1. 解析数据库配置
        database_url = settings.database.DATABASE_URL
        db_config = _parse_database_url(database_url)
        
        if database_name:
            db_config['database'] = database_name
        
        logger.info(f"开始数据库备份: {{db_config['database']}}")
        
        # 2. 创建备份目录
        backup_path = Path(backup_dir) if backup_dir else Path('./backups/database')
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 3. 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_name = db_config['database']
        sql_file = backup_path / f"{{db_name}}_backup_{{timestamp}}.sql"
        gz_file = backup_path / f"{{db_name}}_backup_{{timestamp}}.sql.gz"
        
        # 4. 导出数据库
        if not _dump_database(db_config, sql_file):
            raise Exception("数据库导出失败")
        
        # 5. 压缩文件
        if not _compress_file(sql_file, gz_file):
            raise Exception("文件压缩失败")
        
        # 6. 删除原始 SQL 文件
        sql_file.unlink(missing_ok=True)
        
        # 7. 清理旧备份
        if retention_days > 0:
            try:
                _cleanup_old_backups(backup_path, db_name, retention_days)
            except Exception as cleanup_error:
                logger.warning(f"清理旧备份文件失败: {{cleanup_error}}")
        
        # 8. 返回成功结果
        backup_file_size = gz_file.stat().st_size
        result = {{
            'success': True,
            'database': db_name,
            'backup_file': str(gz_file),
            'file_size_mb': round(backup_file_size / 1024 / 1024, 2),
            'timestamp': timestamp,
            'retention_days': retention_days,
            'message': '备份成功'
        }}
        
        logger.info(f"✅ 备份完成: {{gz_file}} ({{result['file_size_mb']}} MB)")
        return result
        
    except Exception as e:
        logger.error(f"数据库备份失败: {{e}}", exc_info=True)
        
        # 清理可能存在的临时文件
        for file in [sql_file, gz_file]:
            if file and file.exists():
                try:
                    file.unlink()
                    logger.debug(f"已清理临时文件: {{file}}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件 {{file}} 失败: {{cleanup_error}}")
        
        # 重试任务
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300)
        
        # 超过最大重试次数，返回失败结果
        return {{
            'success': False,
            'database': database_name or 'unknown',
            'error': str(e),
            'message': '备份失败'
        }}
'''

        self.file_ops.create_python_file(
            file_path="app/tasks/backup_database_task.py",
            docstring="数据库备份任务 —— 备份到本地存储",
            imports=imports,
            content=content,
            overwrite=True
        )
