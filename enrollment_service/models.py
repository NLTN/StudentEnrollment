from typing import Optional
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
    department_code: str
    course_no: str
    section_no: str
    year: int
    semester: str
    instructor_id: int
    room_capacity:int

class Course(BaseModel):
    department_code: str
    course_no: str
    title: str





class Instructor(BaseModel):
    id: int
    first_name: str
    last_name: str

class Student(BaseModel):
    id: int
    first_name: str
    last_name: str

class ClassPatch(BaseModel):
    section_no: Optional[int] = None
    instructor_id: Optional[int] = None
    room_num: Optional[int] = None
    room_capacity: Optional[int] = None
    course_start_date: Optional[str] = None
    enrollment_start: Optional[str] = None
    enrollment_end: Optional[str] = None

class Enrollment(BaseModel):
    student_id: int
    section_id: int