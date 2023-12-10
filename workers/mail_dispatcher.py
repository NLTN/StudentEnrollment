import pika
import logging
from helper import wait_for_service

# Logger
logging.basicConfig(filename=f'mail_dispatcher.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def dispatcher():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        msg = f" [x] Received {body}"
        print(msg)
        logging.info(msg)

    channel.basic_consume(queue='hello',
                          auto_ack=True,
                          on_message_callback=callback)

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