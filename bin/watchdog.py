import os
import time
import socket
from pydantic_settings import BaseSettings


class Settings(BaseSettings, env_file=".env", extra="ignore"):
    USER_SERVICE_PRIMARY_DB_PATH: str


settings = Settings()


def wait_for_service(host, port, timeout=60):
    start_time = time.time()
    done = False

    while not done:
        try:
            socket.create_connection((host, port), timeout=5)
            print(f"Watchdog: Detected the service at {host}:{port} is up!")
            done = True

        except (socket.error, socket.timeout):
            if time.time() - start_time > timeout:
                print(f"Timed out waiting for {host}:{port}")
                done = True
            time.sleep(1)


if __name__ == "__main__":
    wait_for_service("localhost", 8000)

    if not os.path.exists(settings.USER_SERVICE_PRIMARY_DB_PATH):
        print("Watchdog: Creating user database")
        os.system("sh ./bin/create-user-db.sh")
        os.system("sh ./bin/seed.sh")
        print("Watchdog: Creating Enrollment database")
    else:
        print("Watchdog: Detected user database already exists")

    print("Watchdog: Done")
