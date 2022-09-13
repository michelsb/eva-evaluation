#!/bin/bash

NUMBER_MACHINE=$1
ROUNDS=$2
SEQ_NSERVICES=$(seq 1 1 $3)
BROKER_IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
NUM_SCENARIOS=6
#VIDEO_SOURCE_HIGH_TRAFFIC="/usr/videos/manha_muito_movimento_traseira.mp4"
#VIDEO_SOURCE_HIGH_TRAFFIC="/usr/videos/manha_muito_movimento_traseira_720p_15pfs.mp4"
#VIDEO_SOURCE_LOW_TRAFFIC="/usr/videos/manha_pouco_movimento_traseira.mp4"

VIDEO_HIGH_TRAFFIC_FULL="/usr/videos/manha_muito_movimento_traseira_full_15pfs.mp4"
VIDEO_HIGH_TRAFFIC_720="/usr/videos/manha_muito_movimento_traseira_720p_15pfs.mp4"
VIDEO_HIGH_TRAFFIC_480="/usr/videos/manha_muito_movimento_traseira_480p_15pfs.mp4"

IMAGE_STORAGE="alessilva/eva-storage:2022-05-12"

ContainerArray=("filter"  "detection"  "capture"  "zookeeper"  "broker")
MetricArrayPerContainer=("cpu_limit" "cpu" "cpu_per_core" "mem_utilization" "mem_usage_limit" "mem_usage" "mem" "net_eth0" "net_packets_eth0")
MetricArrayGlobal=("system.cpu" "system.ram" "system.net" "system.ip" "services.cpu" "services.mem_usage" "apps.cpu" "apps.mem" "apps.vmem" "tegrastat_tegrastats.gpu_load" "net.eth0" "net_packets.eth0" "net.br_b2970c97f922" "net_packets.br_b2970c97f922" "ipv4.packets" "ipv4.sockstat_sockets")

# Testing device type
case $NUMBER_MACHINE in
	1) 
		EXPERIMENT_MACHINE="jetson"
		# Without ROI, with frame resolution
		IMAGE_CAPTURE="alessilva/eva-jetson-tensorrt-capture:2022-05-17" 
		# With ROI, without frame resolution
		#IMAGE_CAPTURE="alessilva/eva-jetson-tensorrt-capture:2022-05-11" 
		IMAGE_DETECTION="alessilva/eva-jetson-tensorrt-detection:2022-05-11"	
		IMAGE_FILTER="alessilva/eva-jetson-tensorrt-filter:2022-05-11"
		IMAGE_ZOOKEEPER="alessilva/eva_arm64_broker_zookeeper:27_10_21"
		IMAGE_KAFKA="alessilva/eva_arm64_broker_kafka:27_10_21"
		EXTRA_OPTIONS="--gpus all"
		WAIT_KAFKA=10		
		;;
	2) 	
		EXPERIMENT_MACHINE="rpi4"
		IMAGE_CAPTURE="alessilva/eva-raspberry-tflite-capture:2022-05-16"
		IMAGE_DETECTION="alessilva/eva-raspberry-tflite-detection:2022-05-16"	
		IMAGE_FILTER="alessilva/eva-raspberry-tflite-filter:2022-05-16"
		IMAGE_ZOOKEEPER="alessilva/eva_arm7_broker_zookeeper:latest"		
		IMAGE_KAFKA="alessilva/eva_arm7_broker_kafka:latest"
		EXTRA_OPTIONS=""
		WAIT_KAFKA=20
		;;
	*) 
		echo "Invalid input!"
		exit	
		;;
esac

RESULTS_DIR=results_$EXPERIMENT_MACHINE

echo ""
echo "##### CLEANING RESIDUAL SERVICES #####"

docker stop $(docker ps --filter name=capture --filter status=running -aq)
docker stop $(docker ps --filter name=detection --filter status=running -aq)
docker stop $(docker ps --filter name=filter --filter status=running -aq)
case $NUMBER_MACHINE in
	1) 
		ssh -i ../.ssh/id_rsa admin@10.0.20.10 'docker stop $(docker ps --filter name=storage-jetson --filter status=running -aq)'	
		;;
	2) 	
		ssh -i ../.ssh/id_rsa admin@10.0.20.10 'docker stop $(docker ps --filter name=storage-rpi4 --filter status=running -aq)'
		;;
	*) 
		echo "Invalid input!"
		exit	
		;;
esac
docker stop broker
docker stop zookeeper
sleep 10

set_scenario()
{
	case $1 in
		7) 
			echo ">>>> SCENARIO 1 <<<<<"
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_FULL
			CAMERA_FRAME_WIDTH="1920"
			CAMERA_FRAME_HEIGHT="1080"
			EXPERIMENT_RESOLUTION="1920_1080"
			EXPERIMENT_SHIFT="high"	
			;;
		2) 	
			echo ">>>> SCENARIO 2 <<<<<"
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_720
			CAMERA_FRAME_WIDTH="1280"
			CAMERA_FRAME_HEIGHT="720"
			EXPERIMENT_RESOLUTION="1280_720"
			EXPERIMENT_SHIFT="high"	
			;;
		3) 	
			echo ">>>> SCENARIO 3 <<<<<"
			CAMERA_CONFIG_SOURCE=$VIDEO_HIGH_TRAFFIC_480
			CAMERA_FRAME_WIDTH="854"
			CAMERA_FRAME_HEIGHT="480"
			EXPERIMENT_RESOLUTION="854_480"
			EXPERIMENT_SHIFT="high"
			;;
		# 4) 	
		# 	echo ">>>> SCENARIO 4 <<<<<"
		# 	CAMERA_CONFIG_SOURCE=$VIDEO_SOURCE_LOW_TRAFFIC
		# 	CAMERA_FRAME_WIDTH="1920"
		# 	CAMERA_FRAME_HEIGHT="1080"
		# 	EXPERIMENT_RESOLUTION="1920_1080"
		# 	EXPERIMENT_SHIFT="low"
		# 	;;
		# 5) 
		# 	echo ">>>> SCENARIO 5 <<<<<"
		# 	CAMERA_CONFIG_SOURCE=$VIDEO_SOURCE_LOW_TRAFFIC
		# 	CAMERA_FRAME_WIDTH="1200"
		# 	CAMERA_FRAME_HEIGHT="800"
		# 	EXPERIMENT_RESOLUTION="1200_800"
		# 	EXPERIMENT_SHIFT="low"
		# 	;;
		# 6) 
		# 	echo ">>>> SCENARIO 6 <<<<<"
		# 	CAMERA_CONFIG_SOURCE=$VIDEO_SOURCE_LOW_TRAFFIC
		# 	CAMERA_FRAME_WIDTH="960"
		# 	CAMERA_FRAME_HEIGHT="540"
		# 	EXPERIMENT_RESOLUTION="960_540"
		# 	EXPERIMENT_SHIFT="low"
		# 	;;
		# 1) 
		# 	echo ">>>> SCENARIO 1* <<<<<"
		# 	CAMERA_CONFIG_SOURCE=$VIDEO_SOURCE_HIGH_TRAFFIC
		# 	CAMERA_FRAME_WIDTH="1280"
		# 	CAMERA_FRAME_HEIGHT="720"
		# 	EXPERIMENT_RESOLUTION="1280_720"
		# 	EXPERIMENT_SHIFT="high"	
		# 	;;
		*) 
			echo "Invalid input!"
			exit	
			;;
	esac
}

run_experiment()
{	
	SCENARIO=$1
	NSERVICES=$2 
	set_scenario $SCENARIO
	for (( r=1; r<=$ROUNDS; r++ )) # Experiment Round
	do  
		sync; echo 3 > /proc/sys/vm/drop_caches
		SEQUENCE=$r

		echo ""
		echo ">>>> STARTING AT $(date) - DEVICE ${EXPERIMENT_MACHINE} - NUMBER OF SERVICES ${NSERVICES} - SCENARIO ${SCENARIO} - SEQUENCE ${SEQUENCE} <<<<"

		echo ""
		echo "##### STARTING SERVICES #####"

		echo ""
		echo "# RUNNING BROKER MODULE"

		docker run -d --rm --name zookeeper --net=arquitetura-network -p 2181:2181 $IMAGE_ZOOKEEPER
		sleep 10
		docker run -d --rm --name broker --net=arquitetura-network -p 29092:29092 -e KAFKA_LISTENERS="EXTERNAL_SAME_HOST://:29092,INTERNAL://:9092" -e KAFKA_ADVERTISED_LISTENERS="INTERNAL://broker:9092,EXTERNAL_SAME_HOST://${BROKER_IP}:29092" -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP="INTERNAL:PLAINTEXT,EXTERNAL_SAME_HOST:PLAINTEXT" -e KAFKA_INTER_BROKER_LISTENER_NAME="INTERNAL" -e KAFKA_ZOOKEEPER_CONNECT="zookeeper:2181" -e KAFKA_BROKER_ID="2" $IMAGE_KAFKA
		sleep $WAIT_KAFKA

		echo ""
		echo "# RUNNING STORAGE MODULE"

		for (( n=1; n<=$NSERVICES; n++ )) # Number of Services
		do		
			ssh -i ../.ssh/id_rsa admin@10.0.20.10 "docker container run -d --rm -ti --name storage-${EXPERIMENT_MACHINE}-${n} -e SERVICE_ID=SRV${n} -e CAMERA_ID=CAM${n} -e KAFKA_BROKER_URL=${BROKER_IP}:29092 -e EXPERIMENT_MACHINE=${EXPERIMENT_MACHINE} -e EXPERIMENT_SHIFT=${EXPERIMENT_SHIFT} -e EXPERIMENT_RESOLUTION=${EXPERIMENT_RESOLUTION} -e EXPERIMENT_SERVICES_NUMBER=${SEQUENCE}  -v /home/admin/experiments/:/experiment/ ${IMAGE_STORAGE}"
		done

		echo ""
		echo "# RUNNING FILTER MODULE"
		#docker container run -d --rm -ti --gpus all --name filter --net=arquitetura-network -e SERVICE_ID=$SERVICE_ID -e CAMERA_ID=$CAMERA_ID -e KAFKA_BROKER_URL="broker:9092" -e FPS_EXPERIMENT=True -e FILTER_ON="" $IMAGE_FILTER
		for (( n=1; n<=$NSERVICES; n++ )) # Number of Services
		do
			docker container run -d --rm -ti $EXTRA_OPTIONS --name "filter-${n}" --net=arquitetura-network -e SERVICE_ID="SRV${n}" -e CAMERA_ID="CAM${n}" -e KAFKA_BROKER_URL="broker:9092" -e NEXT_MODULE="" -e PREVIOUS_MODULE="DETECTION" $IMAGE_FILTER
		done
		sleep 10

		echo ""
		echo "# RUNNING DETECTION MODULE"	
		#docker container run -d --rm -ti --gpus all --name capture_detection --net=arquitetura-network -e SERVICE_ID=$SERVICE_ID -e CAMERA_ID=$CAMERA_ID -e CAMERA_CONFIG_SOURCE=$CAMERA_CONFIG_SOURCE -e CAMERA_CONFIG_RETRY_CONNECTION="120" -e CAMERA_FRAME_WIDTH=$CAMERA_FRAME_WIDTH -e CAMERA_FRAME_HEIGHT=$CAMERA_FRAME_HEIGHT -e CAMERA_PLATE_WIDTH="200" -e CAMERA_PLATE_HEIGHT="80" -e KAFKA_BROKER_URL="broker:9092" -e DEBUG="" -e FPS_EXPERIMENT=True -v /home/user/Vídeos/:/usr/videos/ $IMAGE_CAPTURE_DETECTION
		for (( n=1; n<=$NSERVICES; n++ )) # Number of Services
		do
		docker container run -d --rm -ti $EXTRA_OPTIONS --name "detection-${n}" --net=arquitetura-network -e SERVICE_ID="SRV${n}" -e CAMERA_ID="CAM${n}" -e PLATE_WIDTH="120" -e PLATE_HEIGHT="80" -e KAFKA_BROKER_URL="broker:9092" -e NEXT_MODULE="FILTER" -e PREVIOUS_MODULE="CAPTURE" $IMAGE_DETECTION
		done
		sleep 10

		echo ""
		echo "# RUNNING CAPTURING MODULE"
		#docker container run -d --rm -ti --gpus all --name capture_detection --net=arquitetura-network -e SERVICE_ID=$SERVICE_ID -e CAMERA_ID=$CAMERA_ID -e CAMERA_CONFIG_SOURCE=$CAMERA_CONFIG_SOURCE -e CAMERA_CONFIG_RETRY_CONNECTION="120" -e CAMERA_FRAME_WIDTH=$CAMERA_FRAME_WIDTH -e CAMERA_FRAME_HEIGHT=$CAMERA_FRAME_HEIGHT -e CAMERA_PLATE_WIDTH="200" -e CAMERA_PLATE_HEIGHT="80" -e KAFKA_BROKER_URL="broker:9092" -e DEBUG="" -e FPS_EXPERIMENT=True -v /home/user/Vídeos/:/usr/videos/ $IMAGE_CAPTURE_DETECTION
		for (( n=1; n<=$NSERVICES; n++ )) # Number of Services
		do
		docker container run -d --rm -ti $EXTRA_OPTIONS --name "capture-${n}" --net=arquitetura-network -e SERVICE_ID="SRV${n}" -e CAMERA_ID="CAM${n}" -e CAMERA_CONFIG_SOURCE=$CAMERA_CONFIG_SOURCE -e CAMERA_FRAME_WIDTH=$CAMERA_FRAME_WIDTH -e CAMERA_FRAME_HEIGHT=$CAMERA_FRAME_HEIGHT -e KAFKA_BROKER_URL="broker:9092" -e NEXT_MODULE="DETECTION" -v /opt/cam_videos:/usr/videos $IMAGE_CAPTURE
		done
		#sleep 10

		echo ""
		echo "##### RESTARTING NETDATA #####"
		systemctl restart netdata

		echo ""
		echo "##### INITIALIZING TIMER #####"
		sleep 10
		echo "9 minutes left"
		sleep 60
		echo "8 minutes left"
		sleep 60
		echo "7 minutes left"
		sleep 60
		echo "6 minutes left"
		sleep 60
		echo "5 minutes left"
		sleep 60
		echo "4 minutes left"
		sleep 60
		echo "3 minutes left"
		sleep 60
		echo "2 minutes left"
		sleep 60
		echo "1 minute left"
		sleep 60

		echo ""
		echo "##### COLLECTING DATA #####"

		for metric in ${MetricArrayGlobal[*]};
		do
			curl -Ss "http://localhost:19999/api/v1/data?chart=${metric}&format=csv&after=-540&group=max&points=30&options=nonzero" > $RESULTS_DIR/$NSERVICES/global_${metric}_${EXPERIMENT_MACHINE}_${EXPERIMENT_SHIFT}_${EXPERIMENT_RESOLUTION}_${SEQUENCE}.csv
		done

		for container in ${ContainerArray[*]};
		do
			for (( n=1; n<=$NSERVICES; n++ )) # Number of Services
			do
				NAME_CONTAINER=$container-${n}
				ID_CONTAINER=$(docker ps -aqf "name=${NAME_CONTAINER}")  
				for metric in ${MetricArrayPerContainer[*]};
				do
					#if [ $EXPERIMENT_MACHINE == "jetson" ]
					#then
					#	LABEL_CONTAINER=$ID_CONTAINER
					#else
					#LABEL_CONTAINER=$NAME_CONTAINER
					#fi
					curl -Ss "http://localhost:19999/api/v1/data?chart=cgroup_${NAME_CONTAINER}.${metric}&format=csv&after=-540&group=max&points=30&options=nonzero" > $RESULTS_DIR/$NSERVICES/${NAME_CONTAINER}_${metric}_SRV${n}_CAM${n}_${EXPERIMENT_MACHINE}_${EXPERIMENT_SHIFT}_${EXPERIMENT_RESOLUTION}_${SEQUENCE}.csv
				done
			done
		done

		echo ""
		echo "##### STOPPING SERVICES #####"		

		echo ""
		echo "STOPPING CAPTURE MODULE"
		docker stop $(docker ps --filter name=capture --filter status=running -aq)
		echo ""
		echo "STOPPING DETECTION MODULE"	
		docker stop $(docker ps --filter name=detection --filter status=running -aq)
		echo ""
		echo "STOPPING FILTER MODULE"
		docker stop $(docker ps --filter name=filter --filter status=running -aq)
		echo ""
		echo "STOPPING STORAGE MODULE"
		case $NUMBER_MACHINE in
			1) 
				ssh -i ../.ssh/id_rsa admin@10.0.20.10 'docker stop $(docker ps --filter name=storage-jetson --filter status=running -aq)'	
				;;
			2) 	
				ssh -i ../.ssh/id_rsa admin@10.0.20.10 'docker stop $(docker ps --filter name=storage-rpi4 --filter status=running -aq)'
				;;
			*) 
				echo "Invalid input!"
				exit	
				;;
		esac		
		
		scp -i ../.ssh/id_rsa admin@10.0.20.10:/home/admin/experiments/stats*_*_*_${EXPERIMENT_MACHINE}_${EXPERIMENT_SHIFT}_${EXPERIMENT_RESOLUTION}_${SEQUENCE}.* $RESULTS_DIR/$NSERVICES/.
		

		echo ""
		echo "STOPPING BROKER MODULE"
		docker stop broker
		docker stop zookeeper

		echo ""
		echo ">>>> FINISHING AT $(date) <<<<"

	done
}

echo ""
echo "##### INITIALIZING EXPERIMENTS #####"
echo ""

rm -rf $RESULTS_DIR
for s in $SEQ_NSERVICES
do	
	mkdir -p $RESULTS_DIR/$s
	ssh -i ../.ssh/id_rsa admin@10.0.20.10 "rm -f /home/admin/experiments/stats*_*_*_${EXPERIMENT_MACHINE}_*"
	if [ $s -gt 1 ]
	then
		NUM_SCENARIOS=1
	fi
	for (( m=1; m<=$NUM_SCENARIOS; m++ )) # Select scenario
	do
		run_experiment $m $s
		#echo "SCENARIO ${m} NUM SERVICES ${s}"
	done
done
