import os.path
from typing import Literal

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    MODE: Literal["DEV", "TEST", "PROD"]
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @model_validator(mode="before")
    @classmethod
    def get_database_url(cls, v):
        v["DATABASE_URL"] = (
            f"postgresql+asyncpg://{v['DB_USER']}:{v['DB_PASS']}@{v['DB_HOST']}"
            f":{v['DB_PORT']}/{v['DB_NAME']}"
        )
        return v

    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_USER: str
    TEST_DB_PASS: str
    TEST_DB_NAME: str

    @model_validator(mode="before")
    @classmethod
    def get_test_database_url(cls, v):
        v["TEST_DATABASE_URL"] = (
            f"postgresql+asyncpg://{v['TEST_DB_USER']}:{v['TEST_DB_PASS']}@{v['TEST_DB_HOST']}"
            f":{v['TEST_DB_PORT']}/{v['TEST_DB_NAME']}"
        )
        return v

    SECRET_KEY: str
    ALGORITHM: str

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str

    REDIS_HOST: str
    REDIS_PORT: int

    DATABASE_URL: str = ""
    TEST_DATABASE_URL: str = ""

    class Config:
        env_file = "/etc/secrets/.env"

        @classmethod
        def load_env(cls):
            load_dotenv(cls.env_file)


settings = Config()
