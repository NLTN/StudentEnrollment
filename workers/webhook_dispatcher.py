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

def post_data():
    try:
        headers = {
            "Content-Type": "application/json;"
        }
        body = {"key1": "value1", "key2": "value2"}

        # Send request
        url = f'http://localhost:5900/webhook'
        response = requests.post(url, headers=headers, json=body)

        # Check the HTTP response status code
        response.raise_for_status()
        logger.info("POST request successful")
        return True
    except requests.exceptions.RequestException as e:
        # Handle exceptions raised by the HTTP request
        logger.error(f"Failed to send POST request: {e}")
        # If the callback URL is not available, do not raise an exception
        return False

def dispatcher():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        msg = f" [x] Received {body}"

        # Log the received message
        logger.info(msg)

        try:
            # Attempt to send data to the webhook
            success = post_data()

            # Extract relevant information from the message and print it
            try:
                message_data = json.loads(body.decode('utf-8'))
                relevant_info = message_data.get("event_type", "")
                logger.info(f"Received relevant info: {relevant_info}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")

            # Acknowledge the message only if the POST request is successful
            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info("Message acknowledged.")
            else:
                logger.info("Message not acknowledged due to processing error.")

        except Exception as e:
            # Handle other unexpected exceptions
            logger.error(f"Unexpected error: {e}")

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

    logger.info(' [*] Waiting for messages. To exit press CTRL+C')

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
