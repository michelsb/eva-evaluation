#!/bin/bash

# Which device will be used (jetson, rpi4 or x86 are supported)
EXPERIMENT_MACHINE=jetson

# Service to be used in experiments
SERVICE_TYPE=cdfsv1

# Number of experiments repetition
ROUNDS=1

# Number of services created for a single experiment
NUMBER_OF_SERVICES=1
JUMP_SIZE=1
SEQ_NSERVICES=$(seq 1 ${JUMP_SIZE} ${NUMBER_OF_SERVICES})
# Optionally you can run just for a fixed number of services, not a sequence. For example:
# SEQ_NSERVICES=2
# Just run for 2 services, not a sequence of 1 then 2

# Duration of a single experiment in minutes
DURATION=1

# Network interface to send frames out
MAIN_INTERFACE=eth0

# Docker virtual network
DOCKER_NET=eva-net

# IP Address from the storage server (previously the user must enable the key ssh authentication)
CLOUD_SERVER_IP=10.0.20.10
CLOUD_SERVER_USER=admin
#CLOUD_SERVER_IP=localhost
#CLOUD_SERVER_USER=michel

# The path to the videos
VIDEO_SOURCE_PATH=/opt/cam_videos

