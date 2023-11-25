#!/bin/sh

# Create .env file
sh ./bin/create-dotenv.sh

# Start Watchdog to detect the services are already running 
# and create databases (if needed).
python3 ./bin/watchdog.py &

# Start the services
foreman start -m gateway=1,enrollment_service=3,user_service=1,dynamodb=1,redis=1