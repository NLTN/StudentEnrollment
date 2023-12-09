#!/bin/bash

sudo pkill redis-server
redis-server ./etc/redis.conf