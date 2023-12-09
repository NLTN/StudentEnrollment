#!/bin/sh

sudo pkill rabbitmq
sudo rabbitmq-server start
sudo pkill rabbitmq