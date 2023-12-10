#!/bin/bash

# sudo pkill redis-server
sudo systemctl stop redis-server
redis-server ./etc/redis.conf