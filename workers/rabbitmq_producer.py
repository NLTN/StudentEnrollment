from http.client import HTTPException
import pika
from enrollment_service.models import Subscription

# this file sends RabbitMQ notifications:

def send_enrollment_notification(subscription: Subscription):
    try:
        connection_params = pika.ConnectionParameters('localhost')
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.exchange_declare(exchange='enrollment_notifications', exchange_type='fanout')

        message = f"Enrollment Notification: You have been enrolled in {subscription.course_id}."

        channel.basic_publish(exchange='enrollment_notifications', routing_key='', body=message)

        connection.close()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
