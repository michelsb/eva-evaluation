#!/bin/bash

ContainerArray=("filter"  "detection"  "capture"  "zookeeper"  "broker")

# List available videos here
VIDEO_HIGH_TRAFFIC_FULL="/usr/videos/manha_muito_movimento_traseira_full_15fps.mp4"
VIDEO_HIGH_TRAFFIC_720="/usr/videos/manha_muito_movimento_traseira_720p_15fps.mp4"
VIDEO_HIGH_TRAFFIC_480="/usr/videos/manha_muito_movimento_traseira_480p_15fps.mp4"

# Number of scenarios to run (do not change this value)
NUMBER_OF_SCENARIOS=6

# Configured values fo kafka retention policy (10 seconds)
KAFKA_LOG_RETENTION_MS=10000
KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS=5000

CONTAINER_NAME_ZOOKEEPER="zookeeper"
CONTAINER_NAME_KAFKA="broker"
CONTAINER_NAME_CAPTURE="capture"
CONTAINER_NAME_DETECTION="detection"
CONTAINER_NAME_FILTER="filter"
CONTAINER_NAME_STORAGE="storage"

# KR = Configured values fo kafka retention policy (10 seconds)
# NKR = Default values for kafka retention policy (7 days)
get_scenario()
{
	case $1 in
		1) 
			echo ">>>> SCENARIO 1 <<<<<"			
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_FULL
			CAMERA_FRAME_WIDTH="1920"
			CAMERA_FRAME_HEIGHT="1080"
			SCENARIO_NAME="1920_1080_NKR" # unique name for each scenario
			EXPERIMENT_SHIFT="high"
			kafka_retetion_enabled=false	
			;;
		2) 
			echo ">>>> SCENARIO 2 <<<<<"
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_FULL
			CAMERA_FRAME_WIDTH="1920"
			CAMERA_FRAME_HEIGHT="1080"
			SCENARIO_NAME="1920_1080_KR"
			EXPERIMENT_SHIFT="high"
			kafka_retetion_enabled=true				
			;;
		3) 	
			echo ">>>> SCENARIO 3 <<<<<"
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_720
			CAMERA_FRAME_WIDTH="1280"
			CAMERA_FRAME_HEIGHT="720"
			SCENARIO_NAME="1280_720_NKR"
			EXPERIMENT_SHIFT="high"	
			kafka_retetion_enabled=false
			;;
		4) 	
			echo ">>>> SCENARIO 4 <<<<<"
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_720
			CAMERA_FRAME_WIDTH="1280"
			CAMERA_FRAME_HEIGHT="720"
			SCENARIO_NAME="1280_720_KR"
			EXPERIMENT_SHIFT="high"
			kafka_retetion_enabled=true	
			;;
		5) 	
			echo ">>>> SCENARIO 5 <<<<<"
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_480
			CAMERA_FRAME_WIDTH="854"
			CAMERA_FRAME_HEIGHT="480"
			SCENARIO_NAME="854_480_NKR"
			EXPERIMENT_SHIFT="high"
			kafka_retetion_enabled=false
			;;
		6) 	
			echo ">>>> SCENARIO 6 <<<<<"
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_480
			CAMERA_FRAME_WIDTH="854"
			CAMERA_FRAME_HEIGHT="480"
			SCENARIO_NAME="854_480_KR" 
			EXPERIMENT_SHIFT="high"
			kafka_retetion_enabled=true
			;;
		*) 
			echo "Invalid input!"
			exit	
			;;
	esac
    
	CAPTURE_OPTIONS='-e CAMERA_CONFIG_SOURCE='$CAMERA_CONFIG_SOURCE' -e CAMERA_FRAME_WIDTH='$CAMERA_FRAME_WIDTH' -e CAMERA_FRAME_HEIGHT='$CAMERA_FRAME_HEIGHT' -e KAFKA_BROKER_URL="'$CONTAINER_NAME_KAFKA':9092" -e NEXT_MODULE="DETECTION"'
	DETECTION_OPTIONS='-e PLATE_WIDTH="120" -e PLATE_HEIGHT="80" -e KAFKA_BROKER_URL="'$CONTAINER_NAME_KAFKA':9092" -e NEXT_MODULE="FILTER" -e PREVIOUS_MODULE="CAPTURE"'
	FILTER_OPTIONS='-e KAFKA_BROKER_URL="'$CONTAINER_NAME_KAFKA:9092'" -e NEXT_MODULE="" -e PREVIOUS_MODULE="DETECTION"'
	KAFKA_OPTIONS='-e KAFKA_LISTENERS="EXTERNAL_SAME_HOST://:29092,INTERNAL://:9092" -e KAFKA_ADVERTISED_LISTENERS="INTERNAL://'$CONTAINER_NAME_KAFKA':9092,EXTERNAL_SAME_HOST://'$BROKER_IP':29092" -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP="INTERNAL:PLAINTEXT,EXTERNAL_SAME_HOST:PLAINTEXT" -e KAFKA_INTER_BROKER_LISTENER_NAME="INTERNAL" -e KAFKA_ZOOKEEPER_CONNECT="'${CONTAINER_NAME_ZOOKEEPER}':2181" -e KAFKA_BROKER_ID=2'
	ZOOKEEPER_OPTIONS=""

	if $kafka_retetion_enabled ; then
		KAFKA_OPTIONS=$KAFKA_OPTIONS" -e KAFKA_LOG_RETENTION_MS=$KAFKA_LOG_RETENTION_MS -e KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS=$KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS"
	fi
}