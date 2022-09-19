#!/bin/bash

run_experiment()
{
    SCENARIO=$1
	NSERVICES=$2
    SEQUENCE=$3     

    echo ""
	echo ">>>> STARTING AT $(date) - DEVICE ${EXPERIMENT_MACHINE} - NUMBER OF SERVICES ${NSERVICES} - SCENARIO ${SCENARIO} - SEQUENCE ${SEQUENCE} <<<<"
    echo ""

    echo ""
	echo "## STARTING SERVICES ##"
    echo ""
    # Function to start services (from start_services.sh)
    start_services

    echo ""
	echo "## STARTING TIMER ##"
	for (( t=$DURATION; t>=1; t-- )) # Select scenario
	do
		echo "$t minutes left"
		sleep 60		
	done

    echo ""
    echo "## LOCAL DATA RETRIEVING ##"

    TIME_COLLECTION=$[$DURATION*60]

    for metric in ${MetricArrayGlobal[*]};
    do
        curl -Ss "http://localhost:19999/api/v1/data?chart=${metric}&format=csv&after=-${TIME_COLLECTION}&group=max&points=30&options=nonzero" > $RESULTS_LOCAL_DIR/$NSERVICES/global_${metric}_${EXPERIMENT_MACHINE}_${EXPERIMENT_SHIFT}_${SCENARIO_NAME}_${SEQUENCE}.csv
    done

    for container in ${ContainerArray[*]};
    do
        #for (( n=1; n<=$NSERVICES; n++ )) # Number of Services
        #do
            #NAME_CONTAINER=$container-${n}
            #ID_CONTAINER=$(docker ps -aqf "name=${NAME_CONTAINER}")  
        CreatedContainersArray=$(docker ps -af "name=${container}" --format "{{.Names}}")
        for created_container_name in ${CreatedContainersArray[*]};
        do
            for metric in ${MetricArrayPerContainer[*]};
            do
                curl -Ss "http://localhost:19999/api/v1/data?chart=cgroup_${created_container_name}.${metric}&format=csv&after=-${TIME_COLLECTION}&group=max&points=30&options=nonzero" > $RESULTS_LOCAL_DIR/$NSERVICES/${created_container_name}_${metric}_${EXPERIMENT_MACHINE}_${EXPERIMENT_SHIFT}_${SCENARIO_NAME}_${SEQUENCE}.csv
            done
        done
        #done
    done

    echo ""
	echo "## STOPPING SERVICES ##"
    # Function to stop services (from start_services.sh)
    stop_services

    echo ""
    echo "## REMOTE DATA RETRIEVING ##"

    scp -i ../.ssh/id_rsa $CLOUD_SERVER_USER@$CLOUD_SERVER_IP:$RESULTS_REMOTE_DIR/$SEQUENCE/stats*_*_*_${EXPERIMENT_MACHINE}_${EXPERIMENT_SHIFT}_${SCENARIO_NAME}_${SEQUENCE}.* $RESULTS_LOCAL_DIR/$NSERVICES/.

    echo ""
	echo ">>>> FINISHING AT $(date) <<<<"
}