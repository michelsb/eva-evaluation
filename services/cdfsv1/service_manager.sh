#!/bin/bash

start_services() 
{
    echo ""
	echo "# RUNNING BROKER MODULE"
    docker run -d --rm --name $CONTAINER_NAME_ZOOKEEPER --net=$DOCKER_NET -p 2181:2181 $IMAGE_ZOOKEEPER	
    sleep 10
	docker run -d --rm --name $CONTAINER_NAME_KAFKA --net=$DOCKER_NET -p 29092:29092 $KAFKA_OPTIONS $IMAGE_KAFKA    
	sleep $WAIT_KAFKA

    echo ""
	echo "# RUNNING STORAGE MODULE"
    ssh -i ../.ssh/id_rsa $CLOUD_SERVER_USER@$CLOUD_SERVER_IP 'for (( n=1; n<='$NSERVICES'; n++ )); docker container run -d --rm -ti --name '$CONTAINER_NAME_STORAGE'-'$EXPERIMENT_MACHINE'-${n} -e SERVICE_ID=SRV${n} -e CAMERA_ID=CAM${n} -e KAFKA_BROKER_URL='$BROKER_IP':29092 -e EXPERIMENT_MACHINE='$EXPERIMENT_MACHINE' -e EXPERIMENT_SHIFT='$EXPERIMENT_SHIFT' -e EXPERIMENT_RESOLUTION='$SCENARIO_NAME' -e EXPERIMENT_SERVICES_NUMBER='$SEQUENCE'  -v '$RESULTS_REMOTE_DIR'/'$SEQUENCE':/experiment/ '$IMAGE_STORAGE'; done'

	echo ""
	echo "# RUNNING DETECTION AND FILTER MODULES"
	for (( n=1; n<=$NSERVICES; n++ )) # Number of Services
	do
		docker container run -d --rm -ti $EXTRA_OPTIONS --name "${CONTAINER_NAME_FILTER}-${n}" --net=$DOCKER_NET -e SERVICE_ID="SRV${n}" -e CAMERA_ID="CAM${n}" -e KAFKA_BROKER_URL="$CONTAINER_NAME_KAFKA:9092" -e NEXT_MODULE="" -e PREVIOUS_MODULE="DETECTION" $FILTER_OPTIONS $IMAGE_FILTER
        docker container run -d --rm -ti $EXTRA_OPTIONS --name "${CONTAINER_NAME_DETECTION}-${n}" --net=$DOCKER_NET -e SERVICE_ID="SRV${n}" -e CAMERA_ID="CAM${n}" -e KAFKA_BROKER_URL="$CONTAINER_NAME_KAFKA:9092" -e NEXT_MODULE="FILTER" -e PREVIOUS_MODULE="CAPTURE" $DETECTION_OPTIONS $IMAGE_DETECTION
    done
	sleep 10

    echo ""
	echo "# RUNNING CAPTURING MODULE"		
	for (( n=1; n<=$NSERVICES; n++ )) # Number of Services
	do
		docker container run -d --rm -ti $EXTRA_OPTIONS --name "${CONTAINER_NAME_CAPTURE}-${n}" --net=$DOCKER_NET -e SERVICE_ID="SRV${n}" -e CAMERA_ID="CAM${n}" -e KAFKA_BROKER_URL="${CONTAINER_NAME_KAFKA}:9092" -e NEXT_MODULE="DETECTION" -v $VIDEO_SOURCE_PATH:/usr/videos $CAPTURE_OPTIONS $IMAGE_CAPTURE
	done
    sleep 10
}

stop_services() 
{
    echo ""
	echo "# STOPPING OLD REMOTE SERVICES"
	echo ""

	echo "Searching for old storage containers..."
	remote_cmd='cts=$(docker ps --filter name='$EXPERIMENT_MACHINE' --filter status=running -aq); [ -z $cts ] && { echo "There is no storage containers"; exit 0;} || { echo "Found storage containers. Stopping..."; docker stop $cts; }'
	ssh -i ../.ssh/id_rsa $CLOUD_SERVER_USER@$CLOUD_SERVER_IP $remote_cmd
	
	echo ""
	echo "# STOPPING OLD LOCAL SERVICES"

	for container in ${ContainerArray[*]};
	do
		echo "Searching for old $container containers..."
		cts=$(docker ps --filter name=${container} --filter status=running -aq)
		if [ -z "$cts" ]
		then
			echo "There's no $container containers"
		else
			echo "Found $container containers. Stopping..."
			docker stop $cts >/dev/null 2>&1
		fi	
		echo ""
	done

	sleep 10
}