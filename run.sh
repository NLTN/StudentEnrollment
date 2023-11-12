#!/bin/sh

# Create .env file
sh ./bin/create-dotenv.sh

# Start the services
foreman start -m gateway=1,enrollment_service=3,user_service=1