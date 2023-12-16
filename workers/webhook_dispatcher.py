import pika
import requests
from helper import wait_for_service

def post_data():
    try:
        # ---------- Student 2 subscribe for notifications ---------
        headers = {
            "Content-Type": "application/json;"
        }
        body = {"key1": "value1", "key2":"value2"}

        # Send request
        url = f'http://localhost:5900/webhook'
        response = requests.post(url, headers=headers, json=body)
    except Exception as e:
        print(e)

def dispatcher():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        msg = f" [x] Received {body}"
        print(msg)
        post_data()

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
    
    print(' [*] Waiting for messages. To exit press CTRL+C')

    channel.start_consuming()


if __name__ == '__main__':
    try:
        is_rabbitmq_running = wait_for_service(host="localhost", port=5672, timeout=60)

        if not is_rabbitmq_running:
            raise Exception("RabbitMQ Not Running")
        
        # Start dispatcher
        dispatcher()
    except Exception as e:
        print('Interrupted', e)