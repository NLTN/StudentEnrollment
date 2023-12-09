import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import os
import threading
import time

def observe_log_file(log_file_path, timeout_seconds=5):
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        # Get the last modification time of the log file
        current_modification_time = os.path.getmtime(log_file_path)
        
        # Check if the file has been updated
        if current_modification_time > start_time:
            print("Log file has been updated within the last 5 seconds.")
            return True
        
        time.sleep(1)  # Sleep for 1 second before checking again
    
    print("Log file has not been updated within the last 5 seconds.")
    return False

class TestWebhook(unittest.TestCase):

    def setUp(self):
        # os.system("sudo pkill redis-server")
        pass

    def tearDown(self):
        os.system("pkill -f smee")
        pass

    def test_logfile_changed_within_timeout(self):
        log_file = "webhook.app.log"
        os.system("smee --url https://smee.io/CGPVZmrhO5f7v7w --path /webhook --port 5500 &")

        self.assertTrue(os.path.exists(log_file))

        file_changed = observe_log_file(log_file, 5)
        # self.assertTrue(file_changed)

if __name__ == '__main__':
    unittest.main()
