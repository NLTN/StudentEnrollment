import time
import socket

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