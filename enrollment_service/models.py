from typing import Optional
from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# import logging.config

class Settings(BaseSettings, env_file=".env", extra="ignore"):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str
    endpoint_url: str = "http://localhost:8000"
    
class Personnel(BaseModel):
    cwid: int
    first_name: str
    last_name: str
    roles: list[str]


class Config(BaseModel):
    auto_enrollment_enabled : bool

class PatchInstructor(BaseModel):
    cwid: int

class ClassCreate(BaseModel):
    id: Optional[str] = None
    department_code: str
    course_no: int
    section_no: int
    year: int
    semester: str
    title: str = None
    instructor_cwid: int
    room_capacity:int
    enrollment_count: int = 0
    available: str = "true"

class ClassPatch(BaseModel):
    instructor_cwid: Optional[int] = None
    
class Course(BaseModel):
    department_code: str
    course_no: int
    title: str

#update model here for subscription 
class Subscription(BaseModel):
    user_id: str
    course_id: str
    email: str = ""
    webhook_url: str = ""

class SubscriptionsList(BaseModel):
    subscriptions: List[Subscription]
