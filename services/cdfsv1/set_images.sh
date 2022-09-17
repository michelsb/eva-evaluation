#!/bin/bash

ContainerArray=("filter"  "detection"  "capture"  "zookeeper"  "broker")
IMAGE_STORAGE="alessilva/eva-storage:2022-05-12"

get_images_per_device_type()
{    
    case $EXPERIMENT_MACHINE in
        x86)            
            # Without ROI, with frame resolution
            IMAGE_CAPTURE="" 
            IMAGE_DETECTION=""	
            IMAGE_FILTER=""
            IMAGE_ZOOKEEPER=""
            IMAGE_KAFKA=""
            EXTRA_OPTIONS="--gpus all"
            WAIT_KAFKA=10		
            ;;
        jetson) 
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
        rpi4)
            IMAGE_CAPTURE="alessilva/eva-raspberry-tflite-capture:2022-05-16"
            IMAGE_DETECTION="alessilva/eva-raspberry-tflite-detection:2022-05-16"	
            IMAGE_FILTER="alessilva/eva-raspberry-tflite-filter:2022-05-16"
            IMAGE_ZOOKEEPER="alessilva/eva_arm7_broker_zookeeper:latest"		
            IMAGE_KAFKA="alessilva/eva_arm7_broker_kafka:latest"
            EXTRA_OPTIONS=""
            WAIT_KAFKA=20
            ;;	
        *) 
            echo "ERROR: There's no device type $EXPERIMENT_MACHINE. Exiting..."
            exit	
            ;;
    esac
}