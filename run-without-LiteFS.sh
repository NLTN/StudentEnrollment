#!/bin/sh

# Create .env file
sh ./bin/create-dotenv.sh

# *******************************************************************************
# ************** Update .env variable `ENABLE_USER_DB_REPLICATION` **************
# *******************************************************************************
ENV_FILE=".env"

# Load ENV_FILE
export $(grep -v '^#' $ENV_FILE | xargs)

# Define the variable name and the new value
VARIABLE_NAME="ENABLE_USER_DB_REPLICATION"
NEW_VALUE=false

# Update the variable in the .env file
sed -i "s|^$VARIABLE_NAME=.*$|$VARIABLE_NAME=$NEW_VALUE|" "$ENV_FILE"
# ------------------------------------- END -------------------------------------

# Start Watchdog to detect the services are already running 
# and create databases (if needed).
python3 ./bin/watchdog.py &

# Start the services
foreman start -m gateway=1,enrollment_service=3,user_service=1,dynamodb=1,redis=1,rabbitmq=1,webhook=1