"""Security management file generator"""
from core.decorators import Generator
from pathlib import Path
from .base import BaseTemplateGenerator


@Generator(
    category="app_config",
    priority=19,
    enabled_when=lambda c: c.has_auth(),
    description="生成安全工具 (app/core/security.py)"
)
class SecurityGenerator(BaseTemplateGenerator):
    """Security management generator"""

    def generate(self) -> None:
        """generate app/core/security.py"""
        if not self.config_reader.has_auth():
            return

        auth_type = self.config_reader.get_auth_type()
        has_refresh_token = self.config_reader.has_refresh_token()

        imports = [
            "import re",
            "from datetime import datetime, timedelta, timezone",
            "from typing import Dict, Optional, Union",
            "from jose import jwt",
            "from jose.exceptions import JWTError, ExpiredSignatureError",
            "import argon2",
            "from app.core.logger import logger_manager",
            "from app.core.config.settings import settings",
        ]

        content = self._generate_security_content(has_refresh_token)

        self.file_ops.create_python_file(
            file_path="app/core/security.py",
            docstring="Security management module - Password validation, hashing and JWT management",
            imports=imports,
            content=content,
            overwrite=True,
        )

    def _generate_security_content(self, has_refresh_token: bool) -> str:
        """生成安全管理核心内容"""

        # =========================
        # 密码校验器
        # =========================
        password_validator = '''logger = logger_manager.get_logger(__name__)


class PasswordValidator:
    """密码校验器，用于校验密码强度"""

    PASSWORD_PATTERNS = {
        "uppercase": r"[A-Z]",
        "lowercase": r"[a-z]",
        "digit": r"\\d",
        "special": r"[!@#$%^&*(),.?\\\":{}|<>]",
    }

    def __init__(self, min_length: int = 8):
        self.min_length = min_length
        self.logger = logger

    def validate(self, password: str) -> bool:
        """校验密码强度

        如不满足任一条件将抛出 ValueError
        """
        self._check_length(password)
        self._check_uppercase(password)
        self._check_lowercase(password)
        self._check_digit(password)
        self._check_special_char(password)
        self.logger.info("密码强度校验通过。")
        return True

    def _check_length(self, password: str):
        if len(password) < self.min_length:
            self.logger.warning("密码校验失败：长度不足。")
            raise ValueError(
                f"密码长度至少需要 {self.min_length} 位。"
            )

    def _check_uppercase(self, password: str):
        if not re.search(self.PASSWORD_PATTERNS["uppercase"], password):
            self.logger.warning("密码校验失败：缺少大写字母。")
            raise ValueError("密码必须至少包含一个大写字母。")

    def _check_lowercase(self, password: str):
        if not re.search(self.PASSWORD_PATTERNS["lowercase"], password):
            self.logger.warning("密码校验失败：缺少小写字母。")
            raise ValueError("密码必须至少包含一个小写字母。")

    def _check_digit(self, password: str):
        if not re.search(self.PASSWORD_PATTERNS["digit"], password):
            self.logger.warning("密码校验失败：缺少数字。")
            raise ValueError("密码必须至少包含一个数字。")

    def _check_special_char(self, password: str):
        if not re.search(self.PASSWORD_PATTERNS["special"], password):
            self.logger.warning("密码校验失败：缺少特殊字符。")
            raise ValueError("密码必须至少包含一个特殊字符。")
'''

        # =========================
        # 密码哈希器（Argon2）
        # =========================
        password_hasher = '''

class PasswordHasher:
    """密码哈希与校验（仅使用 Argon2）"""

    def __init__(self):
        self.logger = logger_manager.get_logger(__name__)
        # 使用 Argon2 的高安全性配置
        self.ph = argon2.PasswordHasher(
            time_cost=2,
            memory_cost=65536,  # 64MB
            parallelism=1,
            hash_len=32,
            salt_len=16,
        )
        self.logger.info("已启用 Argon2 进行密码哈希")

    def hash(self, password: str) -> str:
        """使用 Argon2 对密码进行哈希"""
        try:
            hashed = self.ph.hash(password)
            self.logger.debug("密码已成功进行 Argon2 哈希")
            return hashed
        except Exception as e:
            self.logger.error(f"Argon2 哈希失败: {e}")
            raise

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """校验明文密码与哈希密码是否匹配"""
        try:
            self.ph.verify(hashed_password, plain_password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            self.logger.debug("密码校验失败")
            return False
        except Exception as e:
            self.logger.error(f"密码校验异常: {e}")
            return False
'''

        # JWT manager - generate different version based on whether refresh_token exists
        if has_refresh_token:
            jwt_manager = '''

class JWTManager:
    """Handles JWT token creation, decoding and validation"""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        issuer: str,
        audience: str,
        access_token_expiry: int,
        refresh_token_expiry: int,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.access_token_expiry = access_token_expiry
        self.refresh_token_expiry = refresh_token_expiry
        self.logger = logger
    
    def timestamp_to_datetime(self, timestamp: int) -> datetime:
        """Convert a Unix timestamp to a UTC datetime object"""
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    
    def create_access_token(self, data: Dict) -> tuple[str, datetime]:
        """Create an access JWT token"""
        return self._create_token(data, self.access_token_expiry, "access")
    
    def create_refresh_token(self, data: Dict) -> tuple[str, datetime]:
        """Create a refresh JWT token"""
        return self._create_token(data, self.refresh_token_expiry, "refresh")
    
    def _create_token(
        self, data: Dict, expires_in_seconds: int, token_type: str
    ) -> tuple[str, datetime]:
        """Internal method for token creation"""
        exp_time = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        # Convert to UTC timestamp
        payload = {
            **data,
            "exp": int(exp_time.timestamp()),
            "iss": self.issuer,
            "aud": self.audience,
            "token_type": token_type,
        }
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        self.logger.info(
            f"{token_type} token created for user: {data.get('user_id')} "
            f"with expiration: {payload['exp']}"
        )
        return encoded_jwt, exp_time
    
    def decode_token(
        self, token: str, expected_jti: Optional[str] = None
    ) -> Union[Dict, None]:
        """Decode and validate a JWT token.
        
        Optionally verify the JTI claim if provided.
        """
        try:
            decoded_token = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["iss", "aud", "exp"]},
            )
            
            if expected_jti and decoded_token.get("jti") != expected_jti:
                self.logger.error("JTI mismatch. Token invalid.")
                return None
            
            self.logger.info(
                f"Token decoded successfully for user_id: {decoded_token.get('user_id')}"
            )
            return decoded_token
        except ExpiredSignatureError:
            self.logger.warning("JWT token has expired.")
        except JWTError as e:
            self.logger.error(f"Invalid JWT token: {e}")
        return None
'''
        else:
            # Version without refresh_token
            jwt_manager = '''

class JWTManager:
    """Handles JWT token creation, decoding and validation"""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        issuer: str,
        audience: str,
        access_token_expiry: int,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        self.access_token_expiry = access_token_expiry
        self.logger = logger
    
    def timestamp_to_datetime(self, timestamp: int) -> datetime:
        """Convert a Unix timestamp to a UTC datetime object"""
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    
    def create_access_token(self, data: Dict) -> tuple[str, datetime]:
        """Create an access JWT token"""
        return self._create_token(data, self.access_token_expiry, "access")
    
    def _create_token(
        self, data: Dict, expires_in_seconds: int, token_type: str
    ) -> tuple[str, datetime]:
        """Internal method for token creation"""
        exp_time = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        # Convert to UTC timestamp
        payload = {
            **data,
            "exp": int(exp_time.timestamp()),
            "iss": self.issuer,
            "aud": self.audience,
            "token_type": token_type,
        }
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        self.logger.info(
            f"{token_type} token created for user: {data.get('user_id')} "
            f"with expiration: {payload['exp']}"
        )
        return encoded_jwt, exp_time
    
    def decode_token(
        self, token: str, expected_jti: Optional[str] = None
    ) -> Union[Dict, None]:
        """Decode and validate a JWT token.
        
        Optionally verify the JTI claim if provided.
        """
        try:
            decoded_token = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["iss", "aud", "exp"]},
            )
            
            if expected_jti and decoded_token.get("jti") != expected_jti:
                self.logger.error("JTI mismatch. Token invalid.")
                return None
            
            self.logger.info(
                f"Token decoded successfully for user_id: {decoded_token.get('user_id')}"
            )
            return decoded_token
        except ExpiredSignatureError:
            self.logger.warning("JWT token has expired.")
        except JWTError as e:
            self.logger.error(f"Invalid JWT token: {e}")
        return None
'''
        
        # Security manager - generate different version based on whether refresh_token exists
        if has_refresh_token:
            security_manager = '''

class SecurityManager:
    """Main authentication service that orchestrates all auth operations"""
    
    def __init__(self, settings):
        self.validator = PasswordValidator()
        self.hasher = PasswordHasher()
        self.jwt_manager = JWTManager(
            secret_key=settings.jwt.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.jwt.JWT_ALGORITHM,
            issuer=settings.jwt.JWT_ISSUER,
            audience=settings.jwt.JWT_AUDIENCE,
            access_token_expiry=settings.jwt.JWT_ACCESS_TOKEN_EXPIRATION,
            refresh_token_expiry=settings.jwt.JWT_REFRESH_TOKEN_EXPIRATION,
        )
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        return self.validator.validate(password)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using Argon2"""
        return self.hasher.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.hasher.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict) -> tuple[str, datetime]:
        """Create an access token"""
        return self.jwt_manager.create_access_token(data)
    
    def create_refresh_token(self, data: Dict) -> tuple[str, datetime]:
        """Create a refresh token"""
        return self.jwt_manager.create_refresh_token(data)
    
    def decode_token(
        self, token: str, expected_jti: Optional[str] = None
    ) -> Union[Dict, None]:
        """Decode and validate a token"""
        return self.jwt_manager.decode_token(token, expected_jti)


security_manager = SecurityManager(settings)
'''
        else:
            # Version without refresh_token
            security_manager = '''

class SecurityManager:
    """Main authentication service that orchestrates all auth operations"""
    
    def __init__(self, settings):
        self.validator = PasswordValidator()
        self.hasher = PasswordHasher()
        self.jwt_manager = JWTManager(
            secret_key=settings.jwt.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.jwt.JWT_ALGORITHM,
            issuer=settings.jwt.JWT_ISSUER,
            audience=settings.jwt.JWT_AUDIENCE,
            access_token_expiry=settings.jwt.JWT_ACCESS_TOKEN_EXPIRATION,
        )
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        return self.validator.validate(password)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using Argon2"""
        return self.hasher.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.hasher.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict) -> tuple[str, datetime]:
        """Create an access token"""
        return self.jwt_manager.create_access_token(data)
    
    def decode_token(
        self, token: str, expected_jti: Optional[str] = None
    ) -> Union[Dict, None]:
        """Decode and validate a token"""
        return self.jwt_manager.decode_token(token, expected_jti)


security_manager = SecurityManager(settings)
'''
        
        # Convenience functions
        convenience_functions = '''

# Convenience functions (backward compatible)
def get_password_hash(password: str) -> str:
    """Hash password - convenience function"""
    return security_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password - convenience function"""
    return security_manager.verify_password(plain_password, hashed_password)
'''
        
        return (
            password_validator
            + password_hasher
            + jwt_manager
            + security_manager
            + convenience_functions
        )
