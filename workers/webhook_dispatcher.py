import pika
import sys
import os
import logging

# Logger
logging.basicConfig(filename=f'webhook_dispatcher.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


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
        dispatcher()
    except Exception as e:
        print('Interrupted')
        print(str(e))
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
