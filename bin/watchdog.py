import os
import time
import socket
from pydantic_settings import BaseSettings


class Settings(BaseSettings, env_file=".env", extra="ignore"):
    USER_SERVICE_PRIMARY_DB_PATH: str


settings = Settings()


def wait_for_service(host, port, timeout=60):
    """
    Waits for a network service to become available on a specified host and port.

    Parameters:
    - host (str): The hostname or IP address of the target service.
    - port (int): The port number on which the service is expected to be available.
    - timeout (int, optional): The maximum time (in seconds) to wait for the service. Default is 60 seconds.

    Returns:
    - bool: True if the service is detected and available within the specified timeout, False otherwise.

    Example:
    ```python
    # Wait for a service on localhost:8080 with a timeout of 30 seconds
    result = wait_for_service("localhost", 8080, timeout=30)

    if result:
        print("Service is available!")
    else:
        print("Service could not be detected within the specified timeout.")
    ```
    """

    start_time = time.time()

    # status codes:
    # 0 - Initial value
    # 1 - Detected the service is up and running
    # 2 - Timeout
    status = 0

    while status == 0:
        try:
            socket.create_connection((host, port), timeout=5)
            print(f"Watchdog: Detected the service at {host}:{port} is up!")
            status = 1

        except (socket.error, socket.timeout):
            if time.time() - start_time > timeout:
                print(f"Watchdog: Timed out waiting for {host}:{port}")
                status = 2
            time.sleep(1)

    return status == 1


if __name__ == "__main__":
    print("Watchdog: Started")

    is_dynamodb_running = wait_for_service("localhost", 8000)

    if is_dynamodb_running:
        if not os.path.exists(settings.USER_SERVICE_PRIMARY_DB_PATH):
            print("Watchdog: Creating user database")
            os.system("sh ./bin/create-user-db.sh")
            os.system("sh ./bin/seed.sh")
            print("Watchdog: Creating Enrollment database")
        else:
            print("Watchdog: Detected user database already exists")
    else:
        print("Watchdog: Service could not be detected within the specified timeout.")

    # RabbitMQ
    is_rabbitmq_running = wait_for_service("localhost", 5672)

    if is_dynamodb_running and is_rabbitmq_running:
        print("Watchdog: RabbitMQ and DynamoDB are up and running")
        print("Watchdog: Done")
    else:
        print("Watchdog: RabbitMQ and/or DynamoDB could not be detected within the specified timeout.")
