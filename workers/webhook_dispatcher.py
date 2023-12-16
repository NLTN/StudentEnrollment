import pika
import requests
import logging
import json
from helper import wait_for_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pika_logger = logging.getLogger('pika')
pika_logger.setLevel(logging.WARNING)

def callback(ch, method, properties, body):
    # Log the received message
    # logger.info(body)
    
    # Load the binary body into a Python object
    data = json.loads(body.decode('utf-8'))
    webhook_url = data.get("webhook_url")

    if webhook_url:
        # Optional. Add an message
        data["message"] = "You have been successfully enrolled from the waitlist."
        
        try:
            headers = {
                "Content-Type": "application/json;"
            }
            
            # Send request
            response = requests.post(webhook_url, headers=headers, json=data)

            # Check the HTTP response status code
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Handle exceptions raised by the HTTP request
            logger.error(f"Failed to send POST request: {e}")
        else:
             # POST request is successful. Acknowledge the message!
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
def dispatcher():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    exchange_name = "waitlist_exchange"
    queue_name = "webhook"

    # Declare a fanout exchange
    channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

    # Declare a queue and bind it to the fanout exchange
    channel.queue_declare(queue=queue_name)
    channel.queue_bind(exchange=exchange_name, queue=queue_name)

    # Set up the callback function for handling incoming messages
    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=False)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Received interrupt, stopping consumption.")
        connection.close()

if __name__ == '__main__':
    try:
        is_rabbitmq_running = wait_for_service(host="localhost", port=5672, timeout=60)

        if not is_rabbitmq_running:
            raise Exception("RabbitMQ Not Running")

        # Start dispatcher
        dispatcher()
    except Exception as e:
        logger.error('Error during execution', exc_info=True)
