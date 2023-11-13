#!/bin/bash

# ------------------------------- CONFIGURATIONS -------------------------------
# The location where you want the "DynamoDB Local" program to be installed.
DYNAMODB_LIBRARY_PATH="./lib"
# ------------------------------------------------------------------------------



# Update package lists
sudo apt update

# *******************************************************************************
# *************************** Block to install KrakenD **************************
# *******************************************************************************
# Add the GPG key for the specified keyserver
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 5DE6FD698AD6FDD2

if [ $? -ne 0 ]; then
    echo "\e[31m \nERROR: Cannot add the GPG key\e[0m"
    exit 1
fi

# Add KrakenD repository to sources list
sudo echo "deb https://repo.krakend.io/apt stable main" | sudo tee /etc/apt/sources.list.d/krakend.list

if [ $? -ne 0 ]; then
    echo "\e[31m \nERROR: Cannot add KrakenD repository to sources list\e[0m"
    exit 1
fi

# Update package lists
sudo apt update

# Install KrakenD
sudo apt install -y krakend

if [ $? -ne 0 ]; then
    echo "\e[31m \nERROR: Cannot install KrakenD\e[0m"
    exit 1
fi
# ------------------------------------- END -------------------------------------

# *******************************************************************************
# *************************** Block to install AWS CLI **************************
# *******************************************************************************
TEMP_DIRECTORY="./temp_awscli"

# Clean up
rm -rf $TEMP_DIRECTORY

mkdir -p $TEMP_DIRECTORY


# Download AWS CLI
# Latest Version. The Nov 10, 2023 version has bugs: https://github.com/aws/aws-cli/issues/8320
# curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "$TEMP_DIRECTORY/awscliv2.zip"

# WORKAROUND: we are using the previous version: 2.13.33
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-2.13.33.zip" -o "$TEMP_DIRECTORY/awscliv2.zip"

if [ $? -ne 0 ]; then
    echo "\e[31m \nERROR: Cannot download AWS CLI\e[0m"
    exit 1
fi

# Extract
unzip $TEMP_DIRECTORY/awscliv2.zip -d $TEMP_DIRECTORY

# Install AWS CLI
sudo $TEMP_DIRECTORY/aws/install --update

if [ $? -ne 0 ]; then
    echo "\e[31m \nERROR: Cannot install AWS CLI\e[0m"
    exit 1
fi

# Clean up
rm -rf $TEMP_DIRECTORY
# rm -f $TEMP_DIRECTORY/awscliv2.zip
# rm -rf $TEMP_DIRECTORY/aws
# ------------------------------------- END -------------------------------------

# *******************************************************************************
# *************************** Block to install DynamoDB *************************
# *******************************************************************************

mkdir -p $DYNAMODB_LIBRARY_PATH

# Install Java Runtime Environment (JRE)
sudo apt install -y openjdk-19-jre-headless

if [ $? -ne 0 ]; then
    echo "\e[31m \nERROR: Cannot install Java Runtime Environment (JRE)\e[0m"
    exit 1
fi

# Clean up
rm $DYNAMODB_LIBRARY_PATH/dynamodbv2.tar.gz

# Download DynamoDB
curl https://d1ni2b6xgvw0s0.cloudfront.net/v2.x/dynamodb_local_latest.tar.gz \
    -o "$DYNAMODB_LIBRARY_PATH/dynamodbv2.tar.gz"

if [ $? -ne 0 ]; then
    echo "\e[31m \nERROR: Cannot download DynamoDB\e[0m"
    exit 1
fi

# Extract
tar -xzvf $DYNAMODB_LIBRARY_PATH/dynamodbv2.tar.gz \
    -C $DYNAMODB_LIBRARY_PATH

if [ $? -ne 0 ]; then
    echo "\e[31m \nERROR: Cannot extract dynamodbv2.tar.gz\e[0m"
    exit 1
fi

# Clean up
rm $DYNAMODB_LIBRARY_PATH/dynamodbv2.tar.gz

# ------------------------------------- END -------------------------------------


# *******************************************************************************
# ************************* Block to install other stuff ************************
# *******************************************************************************

# Install Redis 
sudo apt install -y redis

# Install SQLite3
sudo apt install -y sqlite3

# Install ruby-foreman
sudo apt install -y ruby-foreman

# Install entr
sudo apt install -y entr

# Install HTTPie for Terminal to work with REST APIs
sudo apt install -y httpie

# Install pip for Python 3
sudo apt install -y python3-pip

# Install required libaries for the project
if test -f "./requirements.txt"; then
	pip3 install -r requirements.txt

    if [ $? -ne 0 ]; then
        echo "\e[31m \nERROR: Cannot install required libaries for the project\e[0m"
        exit 1
    fi
fi

# ------------------------------------- END -------------------------------------

# Print 'Installation Successful'
echo "\n\n"
echo "*****************************************"
echo "*        Installation Successful        *"
echo "*****************************************"
echo "To start the servers, run: 'sh run.sh'"
echo "\n" 