from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from http import HTTPStatus
from redis import Redis
from pydantic import BaseModel, Field
from typing import Optional
import json
from enrollment_service.db_connection import get_redisdb

app = FastAPI()

class SubscriptionPreference(BaseModel):
    webhook_url: Optional[str] = Field(default=None, exclude=True)
    email: Optional[str] = Field(default=None, exclude=True)


@app.post("/class/{class_id}/subscribe")
def subscribe_notification_for_course(
    class_id: str,
    preference: SubscriptionPreference,
    redisdb: Redis = Depends(get_redisdb),
    student_id: int = Header(alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    first_name: str = Header(alias="x-first-name"),
    last_name: str = Header(alias="x-last-name"),
    ):
    
    if not preference.webhook_url and not preference.email:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Please provide webhook_url and/or email to subscribe for notification")

    member_name = f'{student_id}#{first_name}#{last_name}'    
    is_student_waitlisted = redisdb.zrank(class_id, member_name) != None
    
    if not is_student_waitlisted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="User currently not waitlisted in course")
    
    is_subscribed = redisdb.hget(member_name, class_id) != None
    if not is_subscribed:
        try:                        
            if bool(redisdb.hset(member_name, class_id, json.dumps({"webhook_url": preference.webhook_url, "email": preference.email}))):
                return JSONResponse(status_code=HTTPStatus.OK, content={"detail" : f'successfully subscribed to class with class id {class_id}'})
            
        except:            
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail= "Something went wrong on our side!")

        
    raise HTTPException(status_code=HTTPStatus.CONFLICT, detail= f"User is already subscribed to notifcation for course with class id {class_id}")


@app.get("/subscriptions")
def get_user_subscriptions(
    redisdb: Redis = Depends(get_redisdb),
    student_id: int = Header(alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    first_name: str = Header(alias="x-first-name"),
    last_name: str = Header(alias="x-last-name"),
    ):
    
    member_name = f'{student_id}#{first_name}#{last_name}'
    
    student_notification_subscriptions = [{
        **json.loads(value), **{"class_id" : course.decode()}
    } for course, value in redisdb.hgetall(member_name).items()]
    
    return JSONResponse(status_code=HTTPStatus.OK, content={"notification subscription" : student_notification_subscriptions})

@app.delete("/class/{class_id}/unsubscribe")
def unsubscribe_notification_for_course(
    class_id: str,
    redisdb: Redis = Depends(get_redisdb),
    student_id: int = Header(alias="x-cwid", description="A unique ID for students, instructors, and registrars"),
    first_name: str = Header(alias="x-first-name"),
    last_name: str = Header(alias="x-last-name")
    ):

    member_name = f'{student_id}#{first_name}#{last_name}'
    is_subscribed = redisdb.hget(member_name, class_id) != None

    if is_subscribed:
        try:
            if bool(redisdb.hdel(member_name, class_id)):
                return JSONResponse(status_code=HTTPStatus.OK, content={"detail" : f'successfully unsubscribed from class with class id {class_id}'})

        except:
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Something went wrong on our side!")
            
    
    raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"User currently not subscribed for notifications for class with class id {class_id}")
    
