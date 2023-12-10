#!/bin/bash

# --------------- Kill redis-server ---------------
# Check if running inside a development container
if [ $REMOTE_CONTAINERS ]; then 
    sudo pkill redis-server
else
    sudo systemctl stop redis-server
fi

# -------------- Start redis-server ---------------
redis-server ./etc/redis.conf