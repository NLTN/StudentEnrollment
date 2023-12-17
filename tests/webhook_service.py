import time
import threading
from fastapi import FastAPI

import os
import subprocess

def get_pid_by_port(port):
    try:
        result = subprocess.check_output(["lsof", "-t", f"-i:{port}"])
        return int(result.decode("utf-8").strip())
    except subprocess.CalledProcessError:
        return None

def kill_process_by_port(port):
    pid = get_pid_by_port(port)
    if pid:
        try:
            os.kill(pid, 9)  # SIGKILL
            print(f"Process with PID {pid} killed successfully.")
        except ProcessLookupError:
            print(f"Process with PID {pid} not found.")
    else:
        print(f"No process found on port {port}.")


class ServiceManager:
    def __init__(self, port=8000 , shutdown_timer=30):
        self.port = port
        self.app = FastAPI()
        self.shutdown_event = threading.Event()
        self.shutdown_timer = threading.Timer(shutdown_timer, self.shutdown)

    def start(self):
        kill_process_by_port(self.port)
        self.shutdown_timer.start()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        import uvicorn
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)

    def shutdown(self):
        self.shutdown_event.set()

    def stop(self):
        self.shutdown_event.set()
        self.shutdown_timer.cancel()

    def is_shutdown(self):
        return self.shutdown_event.is_set()


class WebhookTestService:
    def __init__(self, port=8000):
        self.incoming_data = list()
        
        # Create a service manager
        self.manager = ServiceManager(port=port, shutdown_timer=30)

        # FastAPI routes
        @self.manager.app.post("/webhook")
        async def post_data(data: dict):
            self.incoming_data.append(data)
            return {"message": "Webhook received"}
        
        @self.manager.app.get("/webhook")
        async def get_data():
            return self.incoming_data

    def start(self):
        self.manager.start()
        # print(self.manager.is_shutdown())
        
    def stop(self):
        self.manager.stop()
        # print(self.manager.is_shutdown())


# if __name__ == '__main__':
#     print("Start")
#     webhook_service = WebhookService()
#     webhook_service.start()
#     print("Exit")
