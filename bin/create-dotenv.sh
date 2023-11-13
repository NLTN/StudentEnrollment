#!/bin/bash

ENV_FILE=".env"

# Function
insert_if_not_exists() {
	# Parameters
    variable_name=$1
    new_value=$2

    # Check if the .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        # If the .env file doesn't exist, create it and add the variable
        echo "$variable_name=$new_value" >> "$ENV_FILE"
    else
        # Check if the variable doesn't exists in the .env file
		if ! grep -q "^$variable_name=" "$ENV_FILE"; then
			# Get the ASCII value of the last character
			last_byte=$(tail -c 1 "$ENV_FILE" | od -An -tuC)
			
			# Check if the last character is a newline
			if [ ! "$(($last_byte + 0))" -eq 0 ] && [ ! "$last_byte" -eq 10 ]; then
				# Very important: 
				# To make sure an empty line will be appended at the end of the file
				echo "" >> "$ENV_FILE"
			fi
			
			# Append the variable to the end of file
			echo "$variable_name=$new_value" >> "$ENV_FILE"
		fi
    fi
}

# Insert environment variables
insert_if_not_exists "ENROLLMENT_SERVICE_DB_PATH" '"./var/enrollment_local.db"'
insert_if_not_exists "USER_SERVICE_PRIMARY_DB_PATH" '"./var/primary/fuse/user.db"'
insert_if_not_exists "USER_SERVICE_SECONDARY_DB_PATH" '"./var/secondary/fuse/user.db"'
insert_if_not_exists "USER_SERVICE_TERTIARY_DB_PATH" '"./var/tertiary/fuse/user.db"'
insert_if_not_exists "DYNAMODB_LIBRARY_PATH" '"./lib"'
insert_if_not_exists "DYNAMODB_DATABASE_PATH" '"./var"'
insert_if_not_exists "AWS_ACCESS_KEY_ID" '"enrollment"'
insert_if_not_exists "AWS_SECRET_ACCESS_KEY" '"123456"'
insert_if_not_exists "AWS_REGION_NAME" '"local"'