import boto3
import redis
from redis import Redis
from pydantic_settings import BaseSettings
from .dynamoclient import DynamoClient


class TableNames:
    CONFIGS = "Config"
    COURSES = "Course"
    CLASSES = "Class"
    ENROLLMENTS = "Enrollment"
    DROPLIST = "Droplist"
    PERSONNEL = "Personnel"


class Settings(BaseSettings, env_file=".env", extra="ignore"):
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION_NAME: str


settings = Settings()


def get_db():
    raise NotImplementedError


def get_redisdb() -> Redis:
    yield redis.Redis()

def get_dynamodb():
    yield DynamoClient(settings.AWS_ACCESS_KEY_ID,
                       settings.AWS_SECRET_ACCESS_KEY,
                       settings.AWS_REGION_NAME,
                       "http://localhost:8000")