import os
import tempfile
import logging
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, HttpUrl


class WebConfig(BaseModel):
    """WebConfig class"""

    debug: Optional[bool] = False
    secret_key: str = Field(..., alias="secret-key")
    time_zone: Optional[str] = Field(..., alias="time-zone")
    temp_dir: Optional[str] = Field(
        default=tempfile.gettempdir(),
        alias="temp-dir",
    )
    log_level: Optional[str] = Field(
        default="INFO",
        alias="log-level",
    )
    log_dir: Optional[str] = None
    public_link_expiry: Optional[int] = Field(
        gt=0, default=60, alias="public-link-expiry"
    )


class IndexerConfig(BaseModel):
    """Indexer config"""

    period: Optional[int] = Field(gt=0, default=180)  # minutes


class DatabaseConfig(BaseModel):
    """Database config"""

    host: Optional[str] = Field(
        min_length=1,
        default="localhost",
    )
    port: Optional[int] = Field(
        gte=1,
        lte=65535,
        default=5432,
    )
    name: str = Field(min_length=1)
    user: str
    password: str


class RedisConfig(BaseModel):
    """Redis config"""

    host: Optional[str] = Field(
        min_length=1,
        default="localhost",
    )
    port: Optional[int] = Field(
        gte=1,
        lte=65535,
        default=6379,
    )
    db: Optional[int] = Field(
        gte=1,
        lte=12,
        default=0,
    )


class SecurityConfig(BaseModel):
    """Security config class"""

    block_spam: Optional[bool] = Field(
        default=True,
        alias="block-spam",
    )
    block_trigger: int = Field(
        gte=1,
        default=5,
        alias="block-trigger",
    )
    block_duration: int = Field(
        gte=1,
        default=600,
        alias="block-duration",
    )  # seconds
    domain: List[HttpUrl]


class ReverseProxyConfig(BaseModel):
    """Reverse proxy config class"""

    ip_header: Optional[str] = Field(..., alias="ip-header")


class Config(BaseModel):
    """Config class"""

    web: WebConfig
    indexer: Optional[IndexerConfig] = IndexerConfig()
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    reverse_proxy: Optional[ReverseProxyConfig] = Field(..., alias="reverse-proxy")


class ConfigFileNotFoundException(Exception):
    """Config file not found exception"""


class ConfigManager:
    """Config manager"""

    _ENV_KEY = "RPIDRIVE_DATA_DIR"
    logger = logging.getLogger(__name__)

    @staticmethod
    def load_config(path: str = None) -> Config:
        """Load config from file"""
        paths = []
        if path:
            paths.append(path)
        else:
            if os.environ.get(ConfigManager._ENV_KEY, None):
                paths.append(os.environ[ConfigManager._ENV_KEY])
            paths.append(os.path.join(os.getcwd(), "config.yaml"))
        paths = [x for x in paths if x and os.path.exists(x)]
        if not paths:
            raise ConfigFileNotFoundException("Config file doesn't exist.")
        with open(paths[0], "r") as f_h:
            return Config.model_validate(yaml.safe_load(f_h.read()))
