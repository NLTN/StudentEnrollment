from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings
# import logging.config

class Settings(BaseSettings, env_file="enrollment_service/.env", extra="ignore"):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region_name: str
    endpoint_url: str
    
class Personnel(BaseModel):
    cwid: int
    first_name: str
    last_name: str
    role: str

class Instructor(BaseModel):
    id: int
    first_name: str
    last_name: str

class Student(BaseModel):
    id: int
    first_name: str
    last_name: str

class Course(BaseModel):
    department_code: str
    course_no: int
    title: str

class ClassPatch(BaseModel):
    section_no: Optional[int] = None
    instructor_id: Optional[int] = None
    room_num: Optional[int] = None
    room_capacity: Optional[int] = None
    course_start_date: Optional[str] = None
    enrollment_start: Optional[str] = None
    enrollment_end: Optional[str] = None

class ClassCreate(BaseModel):
    dept_code: str
    course_num: int
    section_no: int
    academic_year: int
    semester: str
    instructor_id: int
    room_num: int
    room_capacity:int
    course_start_date: str
    enrollment_start: str
    enrollment_end: str

class Enrollment(BaseModel):
    student_id: int
    section_id: int