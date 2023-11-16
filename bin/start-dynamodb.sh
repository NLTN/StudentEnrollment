#!/bin/bash

ENV_FILE=".env"

# Check if ENV_FILE exists
if [ ! -f $ENV_FILE ]; then
	echo "\e[31mError: .env File Not Found\e[0m"
	echo "To create .env file, run this command:"
	echo '   "sh ./bin/create-dotenv.sh"'
	exit 1
fi

# Load ENV_FILE
export $(grep -v '^#' $ENV_FILE | xargs)

# Create DB directory if not exists
mkdir -p $DYNAMODB_DATABASE_PATH

# AWS database configuration & credentials
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set region $AWS_REGION_NAME

# Start
java -D"java.library.path=./$DYNAMODB_LIBRARY_PATH/DynamoDBLocal_lib" \
    -jar $DYNAMODB_LIBRARY_PATH/DynamoDBLocal.jar \
    -disableTelemetry \
    -dbPath "$DYNAMODB_DATABASE_PATH" 
    # -inMemory \
    # -help