import boto3
import redis
from redis import Redis
from pydantic_settings import BaseSettings


class TableNames:
    CONFIGS = "config"
    COURSES = "Course"
    CLASSES = "Class"
    ENROLLMENTS = "Enrollment"
    PERSONNEL = "Personnel"


class Settings(BaseSettings, env_file=".env", extra="ignore"):
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION_NAME: str


settings = Settings()


def get_db():
    raise NotImplementedError

def get_redisdb() -> Redis:
    return redis.Redis()

def get_dynamodb():
    db = boto3.resource(
        "dynamodb",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME,
        endpoint_url="http://localhost:8000"
    )
    return db