import unittest
import requests
from tests.helpers import *
from tests.settings import BASE_URL
from tests.db_connection import get_redisdb
from tests.webhook_service import WebhookTestService
import pika
import time
import json

class AutoEnrollmentTest(unittest.TestCase):
    # Flag to indicate if a message was received
    message_received = False

    def setUp(self):
        unittest_setUp()

    def tearDown(self):
        unittest_tearDown()

    # ---------------- Helper Functions ----------------
    def purge_rabbitmq_queue(self, exchange_name, queue_name):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        # Declare a fanout exchange
        channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

        # Declare a queue and bind it to the fanout exchange
        channel.queue_declare(queue=queue_name)
        channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Purge the queue
        channel.queue_purge(queue=queue_name)

        # Close connection
        connection.close()

    def receive_from_fanout_exchange(self, exchange_name, queue_name, on_message_callback, timeout_seconds=10):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        # Declare a fanout exchange
        channel.exchange_declare(exchange=exchange_name, exchange_type='fanout')

        # Declare a queue and bind it to the fanout exchange
        channel.queue_declare(queue=queue_name)
        channel.queue_bind(exchange=exchange_name, queue=queue_name)

        # Set up the callback function for handling incoming messages
        channel.basic_consume(
            queue=queue_name, on_message_callback=on_message_callback, auto_ack=False)

        # Flag to indicate if a message was received
        self.message_received = False

        # Start consuming messages
        try:
            # Wait for messages within the specified timeout
            start_time = time.time()
            while not self.message_received and (time.time() - start_time) < timeout_seconds:
                # process events with a timeout of 1 second
                connection.process_data_events(time_limit=1)
        except KeyboardInterrupt:
            print("Interrupted. Exiting.")
        finally:
            connection.close()

        return self.message_received

    def test_auto_enrollment(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # Student 3 enrolls
        user_register(900003, "abc9898@csu.fullerton.edu", "1234", "Tom",
                        "Miller", ["Student"])
        access_token = user_login("abc9898@csu.fullerton.edu", password="1234")
        response = enroll_class(class_id, access_token)


        # BEFORE TEST: Get number of students on the waitlist before sending the request
        rdb = get_redisdb()
        count1 = rdb.zcard(class_id)
        # -------------------- Make API request --------------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student1.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/'
        response = requests.delete(url, headers=headers)


        # AFTER TEST: Get number of students on the waitlist after sending the request
        count2 = rdb.zcard(class_id)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count1, 2)
        self.assertEqual(count2, 1)

    
    def test_publish_message_to_RabbitMQ(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # Student 3 enrolls
        user_register(900003, "abc9898@csu.fullerton.edu", "1234", "Tom",
                        "Miller", ["Student"])
        access_token = user_login("abc9898@csu.fullerton.edu", password="1234")
        response = enroll_class(class_id, access_token)

        # ---------- Student 2 subscribe for notifications ---------
        subscribed_email = "abc2@csu.fullerton.edu"
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "email": subscribed_email
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response = requests.post(url, headers=headers, json=body)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)

        # RabbitMQ: Purge the queue
        self.purge_rabbitmq_queue("waitlist_exchange", "email")

        # BEFORE TEST: Get number of students on the waitlist before sending the request
        rdb = get_redisdb()
        count1 = rdb.zcard(class_id)

        # ------------------ Student 1 drops class -----------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student1.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/'
        response = requests.delete(url, headers=headers)


        # AFTER TEST: Get number of students on the waitlist after sending the request
        count2 = rdb.zcard(class_id)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count1, 2)
        self.assertEqual(count2, 1)

        received_email = None

        def callback(channel, method, properties, body):            
            # Flag to indicate if a message was received
            self.message_received = True

            try:
                data = json.loads(body)
                if "email" in data:
                    nonlocal received_email
                    received_email = data["email"]
            except json.decoder.JSONDecodeError as e:
                print(f"JSON decoding error: {e}")
            
            channel.stop_consuming()

            # Acknowledge the message to notify RabbitMQ that it has been processed
            channel.basic_ack(delivery_tag=method.delivery_tag)

        # RabbitMQ: Wait for the incoming message
        msg_received = self.receive_from_fanout_exchange("waitlist_exchange", "email", callback, 15)
        
        # ------------------------- Assert -------------------------
        self.assertTrue(msg_received)
        self.assertEqual(received_email, subscribed_email)

    def test_webhook_dispatcher(self):
        # ------------------- Create sample data -------------------
        # Register new users & Login
        users = create_sample_users()

        # Create a class
        response = create_class("SOC", 301, 2, 2024, "FA", 1, 1, users.registrar.access_token)
        class_id = response.json()["inserted_id"]

        # Student 1 enrolls
        response = enroll_class(class_id, users.student1.access_token)

        # Student 2 enrolls
        response = enroll_class(class_id, users.student2.access_token)

        # Student 3 enrolls
        user_register(900003, "abc9898@csu.fullerton.edu", "1234", "Tom",
                        "Miller", ["Student"])
        access_token = user_login("abc9898@csu.fullerton.edu", password="1234")
        response = enroll_class(class_id, access_token)

        # ---------- Student 2 subscribe for notifications ---------
        subscribed_email = "abc2@csu.fullerton.edu"
        subscribed_webhook_url = "http://localhost:5900/webhook"
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student2.access_token}"
        }
        body = {
            "email": subscribed_email,
            "webhook_url": subscribed_webhook_url
        }

        # Send request
        url = f'{BASE_URL}/api/class/{class_id}/subscribe'
        response = requests.post(url, headers=headers, json=body)

        # Start Webhook Test Service
        webhook_service = WebhookTestService(port=5900)
        webhook_service.start()

        # BEFORE TEST: Get number of students on the waitlist before sending the request
        rdb = get_redisdb()
        count1 = rdb.zcard(class_id)

        # ------------------ Student 1 drops class -----------------
        headers = {
            "Content-Type": "application/json;",
            "Authorization": f"Bearer {users.student1.access_token}"
        }

        # Send request
        url = f'{BASE_URL}/api/enrollment/{class_id}/'
        response = requests.delete(url, headers=headers)


        # AFTER TEST: Get number of students on the waitlist after sending the request
        count2 = rdb.zcard(class_id)

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)
        self.assertEqual(count1, 2)
        self.assertEqual(count2, 1)


        # Get data from WebhookTestService
        url = subscribed_webhook_url
        response = requests.get(url)

        # Shutdown Webhook Test Service
        webhook_service.stop()

        # ------------------------- Assert -------------------------
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        


if __name__ == '__main__':
    unittest.main()