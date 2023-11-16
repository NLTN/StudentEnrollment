#!/bin/bash
sudo systemctl stop redis-server.service
redis-server ./etc/redis.conf