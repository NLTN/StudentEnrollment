from fastapi import FastAPI
from .instructor_router import instructor_router
from .student_router import student_router
from .registrar_router import registrar_router
from .db_connection import get_dynamodb

# Create the main FastAPI application instance
app = FastAPI()
app.state.dynamo = get_dynamodb()

# Attach the routers to the main application
app.include_router(instructor_router)
app.include_router(student_router)
app.include_router(registrar_router)