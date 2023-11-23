#!/bin/sh

# Create .env file
sh ./bin/create-dotenv.sh

# Create user database if not exists
sh ./bin/create-user-db.sh

# Start the services
foreman start -m gateway=1,enrollment_service=3,user_service=1,dynamodb=1,redis=1