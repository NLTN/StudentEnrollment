from fastapi import FastAPI
from .instructor_router import instructor_router
from .student_router import student_router
from .registrar_router import registrar_router
from .models import Settings
from .Dynamo import Dynamo
import redis

# Create the main FastAPI application instance
app = FastAPI()
settings = Settings()
app.state.dynamo =  Dynamo(config=settings)
app.state.redis = redis.Redis()

# Attach the routers to the main application
app.include_router(instructor_router)
app.include_router(student_router)
app.include_router(registrar_router)