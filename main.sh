#!/bin/bash

# Creating environment variables (general configuration)
export $(cat .env | grep "#" -v)
# Importing packages
. /services/$SERVICE_TYPE/set_images.sh
. /services/$SERVICE_TYPE/set_scenarios.sh
. /services/$SERVICE_TYPE/service_manager.sh
. run_experiment.sh

echo "############################"
echo "SELECTED DEVICE: $EXPERIMENT_MACHINE"
echo "SELECTED SERVICE: $SERVICE_TYPE"
echo "############################"

echo ""
echo "## SETTING IMAGES PER DEVICE TYPE ##"
echo ""

# Defining images for the device type (function from set_images.sh)
get_images_per_device_type

# Testing connectivity with cloud server
echo ""
echo "## TESTING CLOUD SERVER CONNECTIVITY ##"
echo ""

ping -q -w 1 -c 1 $CLOUD_SERVER_IP > /dev/null && CONN=ok || CONN=error
[ $CONN = ok ] && { echo "Cloud Server is available. Starting experiments...";} || { echo "ERROR: Cloud Server is not accessible. Exiting..."; exit 0; }
echo ""

# Defining variables
RESULTS_LOCAL_DIR=services/$SERVICE_TYPE/results_$EXPERIMENT_MACHINE
RESULTS_REMOTE_DIR=/home/$CLOUD_SERVER_USER/eva-storage/$SERVICE_TYPE/results_$EXPERIMENT_MACHINE
BROKER_IP=$(ip -4 addr show $MAIN_INTERFACE | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

echo ""
echo "## CLEANING OLD SERVICES ##"
echo ""

# Function to stop old containers (from service_manager.sh)
stop_services

echo ""
echo "## CLEANING OLD FILES AND DOCKER NETWORK ##"
echo ""

rm -rf $RESULTS_LOCAL_DIR
ssh -i ../.ssh/id_rsa $CLOUD_SERVER_USER@$CLOUD_SERVER_IP "rm -rf $RESULTS_REMOTE_DIR"
echo "Old files removed"
docker network ls|grep $DOCKER_NET > /dev/null && NETEXISTS=ok || NETEXISTS=error
[ $NETEXISTS = ok ] && { echo "Old docker network $DOCKER_NET found. Removing..."; docker network rm $DOCKER_NET;} || { echo "No docker network $DOCKER_NET found";}

echo ""
echo "## INITIALIZING EXPERIMENTS ##"
echo ""

# Creating docker network
docker network create -d bridge $DOCKER_NET
# Get bridge name associated to docker network
network_id=$(docker network inspect -f {{.Id}} $DOCKER_NET) 
bridge_name="br-${network_id:0:12}"
# Defining metrics
MetricArrayPerContainer=("cpu_limit" "cpu" "cpu_per_core" "mem_utilization" "mem_usage_limit" "mem_usage" "mem" "net_eth0" "net_packets_eth0")
MetricArrayGlobal=("system.cpu" "system.ram" "system.net" "system.ip" "services.cpu" "services.mem_usage" "apps.cpu" "apps.mem" "apps.vmem" "tegrastat_tegrastats.gpu_load" "net.$MAIN_INTERFACE" "net_packets.$MAIN_INTERFACE" "net.$bridge_name" "net_packets.$bridge_name" "ipv4.packets" "ipv4.sockstat_sockets")
# Loop in total services running in the device
for s in $SEQ_NSERVICES;
do	
	# Creating directories to store results, both locally and remotelly
	mkdir -p $RESULTS_LOCAL_DIR/$s
	ssh -i ../.ssh/id_rsa $CLOUD_SERVER_USER@$CLOUD_SERVER_IP "mkdir -p $RESULTS_REMOTE_DIR/$s"
	# Loop in scenarios
	for (( m=1; m<=$NUMBER_OF_SCENARIOS; m++ )); 
	do
		# Configure scenario (from set_scenario.sh)
		get_scenario $m
		# Loop in the rounds
		for (( r=1; r<=$ROUNDS; r++ )); 
		do
			# Cleaning cache memory
    		sync; echo 3 > /proc/sys/vm/drop_caches
			# Perform experiment round (from run_experiment.sh)
			run_experiment $m $s $r 
		done		
	done
done
# Removing docker network at the end of experiments
docker network rm $DOCKER_NET