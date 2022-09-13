#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys 
import os
import csv  
import re
import matplotlib.pyplot as plt
import numpy as np
import rpy2.robjects as robjects
from datetime import datetime

#service_array=["SERVICE_FILTER","SERVICE_NFILTER"]
#cam_per_service={"SERVICE_FILTER":"CAM_FILTER","SERVICE_NFILTER":"CAM_NFILTER"}

target_array=["jetson","rpi4"]
scenario_nservices={"jetson":[1,2,3],"rpi4":[1]}
array_frame_resolution = {"single_service":["1920_1080","1200_800","960_540"], "multiple_services":["1920_1080"]}
factors = ["frame_resolution"]
factors_title = {"frame_resolution":"Frame Resolution"}
array_time = {"single_service":["high","low"],"multiple_services":["high"]}
containers=["capture","detection","filter"]#"zookeeper","broker"]
#metrics_containers=["cpu_limit","cpu","cpu_per_core","mem_utilization","mem_usage_limit","mem_usage","mem","net_eth0","net_packets_eth0"]
metrics_global={"jetson":["system.cpu","system.ram","system.net","system.ip","tegrastat_tegrastats.gpu_load","net.eth0","net_packets.eth0","net.br_b2970c97f922","net_packets.br_b2970c97f922","ipv4.packets"],
"rpi4":["system.cpu","system.ram","system.net","system.ip","net.eth0","net_packets.eth0","ipv4.packets"]}

metrics_containers=["cpu_limit","mem_usage","net_eth0","net_packets_eth0"]
metrics_latency=["capture","send_detection","arrive_detection","detection","send_filter","arrive_filter","filter","send_storage","arrive_storage"]
metrics_latency_defined = {"mod_cap_delay":["capture","send_detection"],
    "kafka_cap_det_delay":["send_detection","arrive_detection"],
    "mod_det_delay":["arrive_detection","send_filter"],
    "kafka_det_fil_delay":["send_filter","arrive_filter"],
    "mod_fil_delay":["arrive_filter","send_storage"],
    "kafka_cloud_delay":["send_storage","arrive_storage"],
    "parcial_delay":["capture","send_storage"],
    "total_delay":["capture","arrive_storage"]}
traffic_metric_array = ["system.net","system.ip","net.eth0","net_packets.eth0","net.br_b2970c97f922","net_packets.br_b2970c97f922","ipv4.packets","net_eth0","net_packets_eth0"]
metrics_class=["total_frames","total_frames_class_0","total_frames_class_1","total_bytes","total_bytes_class_0","total_bytes_class_1"]

# Charts data 

array_time_color = {"high":"orangered","low":"dimgrey"}
#array_container_title = {"filter":"Filter","capture":"Capture","detection":"Detection"} 
#array_container_color = {"filter":"Filter","capture":"Capture","detection":"Detection"}

metrics_global_defined_for_charts = ["system.cpu","system.ram","tegrastat_tegrastats.gpu_load"]
metrics_latency_defined_for_charts = [
    "mod_cap_delay",
    "kafka_cap_det_delay",
    "mod_det_delay",
    "kafka_det_fil_delay",
    "mod_fil_delay",
    "kafka_cloud_delay"]
array_global_title={"system.cpu":"CPU","system.ram":"RAM Memory","tegrastat_tegrastats.gpu_load":"GPU"}
array_latency_title={"mod_cap_delay":"Capture","mod_det_delay":"Detection","mod_fil_delay":"Filter","kafka_cloud_delay":"Filter to Cloud","kafka_cap_det_delay":"KafkaCD","kafka_det_fil_delay":"KafkaDF"}
array_time_title = {"high":"High Traffic","low":"Low Traffic"} 
array_metrics_title={"cpu_limit":"CPU Usage (%)","mem_usage":"Memory Usage (MiB)","net_eth0":"Outbound Traffic (Mbps)","net_packets_eth0":"Outbound Traffic (pkts/s)"}
array_container_title={"capture":"Capture","detection":"Detection","filter":"Filter"}
array_target_title={"jetson":"Jetson Xavier NX","rpi4":"Raspberry PI 4"}
array_target_abr={"jetson":"Jetson","rpi4":"RPI4"}


#metrics = ["cpu","mem","gpu","net"]
#metrics_position = {"cpu":3,"mem":2,"gpu":1}
#metrics_title = {"cpu":"CPU Utilization (%)","mem":"Memory Load (%)","gpu":"GPU Utilization (%)","net":"Outbound Traffic (kbps)"}
#row_metrics_containers={"cpu_limit":1,"cpu":,"cpu_per_core","mem_utilization","mem_usage_limit","mem_usage","mem","net_eth0","net_packets_eth0"}
#metrics_global=["system.cpu","system.ram","system.net","system.ip","services.cpu","services.mem_usage","apps.cpu","apps.mem","apps.vmem","tegrastat_tegrastats.gpu_load","net.eth0","net_packets.eth0","net.br_b2970c97f922","net_packets.br_b2970c97f922","ipv4.packets","ipv4.sockstat_sockets"]

r = robjects.r
r.library("nortest")
r.library("MASS")
r('''
        wilcox.onesample.test <- function(v, verbose=FALSE) {
           wilcox.test(v,mu=median(v),conf.int=TRUE, conf.level = 0.95)
        }       
        ''')
wilcoxon_test_one_sample = robjects.r['wilcox.onesample.test']
close_pdf = robjects.r('dev.off') 
#confidence_interval = 0.05
rounds = 10

os.system("rm -rf ./figures")
os.system("mkdir -p ./figures/eda/global ./figures/charts/global")

for container in containers:
    os.system("mkdir -p ./figures/eda/"+container)
for metric_defined in metrics_latency_defined:
    os.system("mkdir -p ./figures/eda/"+metric_defined)
for metric in metrics_class:
    os.system("mkdir -p ./figures/eda/"+metric)

os.system("mkdir -p ./figures/charts/containers")
os.system("mkdir -p ./figures/charts/latency")

global_samples = {}
container_samples = {}
latency_samples = {}
class_samples = {}

def get_timestamp (date):
    value_microsec = datetime.strptime(date,"%m-%d-%Y %H:%M:%S.%f")
    timestamp1 = value_microsec.timestamp() * 1000
    timestamp2 = datetime.strptime(date,"%m-%d-%Y %H:%M:%S.%f")[:-3]
    print("1: ", timestamp1)
    print("2: ", timestamp2)
    return timestamp1

def get_datetime (date):
    return float(date)*1000
    #return datetime.strptime(date,"%m-%d-%Y %H:%M:%S.%f")

def get_value (row,metric,target):
    
    value1, value2 = None, None

    #GLOBAL - Total CPU utilization (all cores) (percentage)
    if metric == "system.cpu":
        #value1 = float(row[1]) + float(row[2]) + float(row[3]) + float(row[4]) + float(row[5])
        if target == "jetson":
            value1 = float(row[3])
        else:
            value1 = float(row[2]) 
    
    #GLOBAL - Physical RAM utilization (percentage)
    if metric == "system.ram":
        total = float(row[1]) + float(row[2]) + float(row[3]) + float(row[4])
        value1 = (float(row[2])/total) * 100 
        #value1 = float(row[2])

    #GLOBAL - Total bandwidth of all physical network interfaces (Kbps)
    # This does not include lo, VPNs, network bridges, IFB devices, bond interfaces, etc. 
    # Only the bandwidth of physical network interfaces is aggregated. 
    # Physical are all the network interfaces that are listed in /proc/net/dev, but do not exist in /sys/devices/virtual/net
    if metric == "system.net":
        value1 = float(row[1]) # received
        value2 = (float(row[2])*-1) # sent
    
    #GLOBAL - Total IP traffic in the system (Kbps)
    if metric == "system.ip":
        value1 = float(row[1]) # received
        value2 = (float(row[2])*-1) # sent

    #GLOBAL - GPU load (percentage)
    if metric == "tegrastat_tegrastats.gpu_load":
        value1 = float(row[1])

    #GLOBAL - The amount of traffic transferred by the network interface eth0 (Kbps)
    if metric == "net.eth0":
        value1 = float(row[1]) # received
        value2 = (float(row[2])*-1) # sent

    #GLOBAL - The number of packets transferred by the network interface eth0 (count)
    if metric == "net_packets.eth0":
        value1 = float(row[1]) # received
        value2 = (float(row[2])*-1) # sent
    
    #GLOBAL - The amount of traffic transferred by the network interface br_b2970c97f922 (Kbps)
    if metric == "net.br_b2970c97f922":
        value1 = float(row[1]) # received
        value2 = (float(row[2])*-1) # sent

    #GLOBAL - The number of packets transferred by the network interface br_b2970c97f922 (count)
    if metric == "net_packets.br_b2970c97f922":
        value1 = float(row[1]) # received
        value2 = (float(row[2])*-1) # sent

    #GLOBAL - IPv4 packets statistics for this host (count)
    if metric == "ipv4.packets":
        value1 = float(row[1]) # received
        value2 = (float(row[2])*-1) # sent

    #CONTAINER - Total physical CPU utilization (all cores) (percentage)
    if metric == "cpu":
        value1 = float(row[1]) + float(row[2]) 
    
    #CONTAINER - Total physical CPU utilization (percentage)
    if metric == "cpu_limit":
        value1 = float(row[1]) 
    
    #CONTAINER - Vitual RAM utilization (percentage)
    if metric == "mem_utilization":
        value1 = float(row[1])

    #CONTAINER - Vitual RAM utilization (MiB)
    if metric == "mem_usage":
        value1 = float(row[1])

    #CONTAINER - The amount of traffic transferred by the network interface eth0 (Kbps)
    if metric == "net_eth0":
        value1 = float(row[1])/1000 # received
        value2 = (float(row[2])*-1)/1000 # sent

    #CONTAINER - The number of packets transferred by the network interface eth0 (count)
    if metric == "net_packets_eth0":
        value1 = float(row[1]) # received
        value2 = (float(row[2])*-1) # sent

    #LATENCY - instante em que o frame da câmera/gravação foi capturado (milliseconds)
    if metric == "capture":
        value1 = get_datetime(row[0])
        #print("capture:",value1)

    #LATENCY - instante em que a mensagem para o Kafka é criada para enviar a placa do Módulo de Captura para o Módulo de Detecção (milliseconds)
    if metric == "send_detection":
        value1 = get_datetime(row[1])

    #LATENCY - instante em que a placa chega e fica disponível para uso no Módulo de Detecção (milliseconds)
    if metric == "arrive_detection":
        value1 = get_datetime(row[2])

    #LATENCY - instante em que a detecção de placas foi finalizada, ou seja, instante em que os recortes de placas foram de fato gerados (milliseconds)
    if metric == "detection":
        value1 = get_datetime(row[3])
        #print("detection:",value1)

    #LATENCY - instante em que a mensagem para o Kafka é criada para enviar a placa do Módulo de CDetecção para o Módulo de Filtragem (milliseconds)
    if metric == "send_filter":
        value1 = get_datetime(row[4])

    #LATENCY - instante em que a placa chega e fica disponível para uso no Módulo de Filtragem (milliseconds)
    if metric == "arrive_filter":
        value1 = get_datetime(row[5])

    #LATENCY - instante em que o modelo de qualidade finaliza a classificação da placa e o resultado da classe daquela placa fica disponível (milliseconds)
    if metric == "filter":
        value1 = get_datetime(row[6])

    #LATENCY - instante em que a mensagem para o Kafka é criada para enviar a placa do Módulo de Filtragem para o Modulo de Armazenamento - Nuvem (milliseconds)
    if metric == "send_storage":
        value1 = get_datetime(row[7])

    #LATENCY - instante em que a placa chega e fica disponível para uso no Módulo de Armazenamento - Nuvem (milliseconds)
    if metric == "arrive_storage":
        value1 = get_datetime(row[8])

    return value1, value2

def calculate_sample (array_values1, array_values2, metric):
    sample1, sample2 = None, None    
    if metric in traffic_metric_array:
        sample1 = np.median(np.array(array_values1))
        sample2 = np.median(np.array(array_values2))
    elif metric in metrics_latency_defined:
        sample1 = np.mean(np.array(array_values1))
    else:
        sample1 = np.median(np.array(array_values1))
    return sample1, sample2

def generate_samples (prefix_file_name,metric,target):
    samples1 = []
    samples2 = []
    #print()
    #print(prefix_file_name)
    for round in range(1, rounds+1):
        file_name = prefix_file_name+"_"+str(round)+".csv"
        file_exists = os.path.exists(file_name)        
        if file_exists:
            f = open(file_name, 'r') # opens the csv file
            try:                            
                reader = csv.reader(f,delimiter=',') #creates the reader object
                isHeader = True
                array_values1 = []
                array_values2 = []
                for row in reader:   # iterates the rows of the file in orders
                    if isHeader:
                        isHeader = False
                        continue
                    if row[1] != 'null':
                        value1,value2 = get_value(row, metric,target)                                                                       
                        array_values1.append(value1)
                        if metric in traffic_metric_array:
                            array_values2.append(value2)
            finally:
                f.close()
            sample1, sample2 = calculate_sample(array_values1, array_values2, metric)
            samples1.append(sample1)
            if metric in traffic_metric_array:
                samples2.append(sample2)
        else:
            print("File %s does not exist!" % (file_name))
    return samples1, samples2

def generate_latency_samples (prefix_file_name,dict_latency_samples,target): 
    for round in range(1, rounds+1):
        # print()
        # print(prefix_file_name)
        # print()
        # print(str(round))
        # print()
        file_name = prefix_file_name+"_"+str(round)+".csv"
        file_exists = os.path.exists(file_name)        
        if file_exists:
            f = open(file_name, 'r') # opens the csv file        
            try:                            
                reader = csv.reader(f,delimiter=',') #creates the reader object
                isHeader = True
                for metric_defined in metrics_latency_defined:
                    latency_samples[metric_defined] = []            
                for row in reader:   # iterates the rows of the file in orders                
                    if isHeader:
                        isHeader = False
                        continue
                    for metric_defined in metrics_latency_defined:
                        #print(metrics_latency_defined[metric_defined][0])
                        #print(metrics_latency_defined[metric_defined][1])
                        start,garbage = get_value(row, metrics_latency_defined[metric_defined][0],target)
                        end,garbage = get_value(row, metrics_latency_defined[metric_defined][1],target)
                        diff = end - start

                        # if metric_defined == "kafka_cap_det_delay":
                        #     print("Start:" + str(start))
                        #     print("End  :" + str(end))
                        #     print("Diff :" + str(diff))
                        #     print()
                        latency_samples[metric_defined].append(end-start)        
            finally:
                f.close()
            for metric_defined in metrics_latency_defined:
                sample1, sample2 = calculate_sample(latency_samples[metric_defined], [], metric_defined)
                dict_latency_samples[metric_defined].append(sample1)  
        else:
            print("File %s does not exist!" % (file_name))   

def generate_class_samples (prefix_file_name,dict_class_samples,target): 
    #print()
    #print(prefix_file_name)
    for round in range(1, rounds+1):
        file_name = prefix_file_name+"_"+str(round)+".txt"        
        file_exists = os.path.exists(file_name)
        if file_exists:
            with open(file_name) as f:
                try:            
                    fr = f.readlines()
                    frs = [f.split(": ") for f in fr]
                    for i, j in frs:
                        metric=i.lower().replace(" ","_")
                        value=int(j)
                        dict_class_samples[metric].append(value)
                finally:
                    f.close()
        else:
            print("File %s does not exist!" % (file_name))


def generate_stats (dict_samples1,samples1,dict_samples2,samples2,title_graph,xlabel,metric,module):
    
    rsamples1 = robjects.FloatVector(samples1)
    #print(samples1)
    test_wilcoxon = wilcoxon_test_one_sample(rsamples1)							
    error_max = test_wilcoxon[7][1]		
    median = test_wilcoxon[8][0]
    dict_samples1["samples"] = rsamples1
    dict_samples1["median"] = r.median(rsamples1)[0]
    dict_samples1["mean"] = r.mean(rsamples1)[0]
    dict_samples1["sd"] = r.sd(rsamples1)[0]
    dict_samples1["min"] = r.min(rsamples1)[0]
    dict_samples1["max"] = r.max(rsamples1)[0]
    dict_samples1["wilcoxon_test_median"] = median
    dict_samples1["wilcoxon_test_error"] = float(error_max)-float(median)

    if metric in traffic_metric_array:
        rsamples2 = robjects.FloatVector(samples2)
        test_wilcoxon = wilcoxon_test_one_sample(rsamples2)							
        error_max = test_wilcoxon[7][1]		
        median = test_wilcoxon[8][0]
        dict_samples2["samples"] = rsamples2
        dict_samples2["median"] = r.median(rsamples2)[0]
        dict_samples2["mean"] = r.mean(rsamples2)[0]
        dict_samples2["sd"] = r.sd(rsamples2)[0]
        dict_samples2["min"] = r.min(rsamples2)[0]
        dict_samples2["max"] = r.max(rsamples2)[0]
        dict_samples2["wilcoxon_test_median"] = median
        dict_samples2["wilcoxon_test_error"] = float(error_max)-float(median)

        # Histogram
        r.pdf("./figures/eda/"+module+"/hist_"+title_graph+"_sent.pdf")
        r.hist(rsamples2, main = title_graph+"sent", col="blue", xlab = xlabel, ylab = "Absolute Frequency")
        close_pdf()
        # Boxplots
        r.pdf("./figures/eda/"+module+"/box_"+title_graph+"_sent.pdf")
        r.boxplot(rsamples2, main = title_graph+"sent",col="lightblue", horizontal=True, las=1, xlab=xlabel)
        close_pdf()

        title_graph = title_graph + "_received"                        

    # Histogram
    r.pdf("./figures/eda/"+module+"/hist-"+title_graph+".pdf")
    r.hist(rsamples1, main = title_graph, col="blue", xlab = xlabel, ylab = "Absolute Frequency")
    close_pdf()
    # Boxplots
    r.pdf("./figures/eda/"+module+"/box-"+title_graph+".pdf")
    r.boxplot(rsamples1, main = title_graph,col="lightblue", horizontal=True, las=1, xlab=xlabel)
    close_pdf()

def generate_data_global():
    for target in target_array:
        global_samples[target] = {}
        for nservices in scenario_nservices[target]:
            global_samples[target][nservices] = {}
            if nservices > 1:
                label = "multiple_services"            
            else:
                label = "single_service"
            for metric in metrics_global[target]:
                global_samples[target][nservices][metric] = {}
                for frame_resolution in array_frame_resolution[label]:
                    global_samples[target][nservices][metric][frame_resolution] = {}
                    for time in array_time[label]:
                        global_samples[target][nservices][metric][frame_resolution][time] = {"samples1":{},"samples2":{}}
                        
                        # Generating samples

                        prefix_file_name = "./results_"+target+"/"+str(nservices)+"/global_"+metric+"_"+target+"_"+time+"_"+frame_resolution
                        samples1, samples2 = generate_samples(prefix_file_name,metric,target)   
                        
                        # Generating statistical data and EDA charts

                        title_graph = "global_"+metric+"_"+str(nservices)+"_"+target+"_"+time+"_"+frame_resolution
                        xlabel = "Values"
                        
                        generate_stats(
                            global_samples[target][nservices][metric][frame_resolution][time]["samples1"],samples1,
                            global_samples[target][nservices][metric][frame_resolution][time]["samples2"],samples2,
                            title_graph,xlabel,metric,"global")                     

                        # if metric == "net.eth0":
                        #     if frame_resolution == "1920_1080":
                        #         print()
                        #         print(metric + " " + target + " " + str(nservices)  + " " + frame_resolution + " " + time)
                        #         print()
                        #         print(global_samples[target][nservices][metric][frame_resolution][time]["samples2"])  
                    
                                  
def generate_data_container():
    for container in containers:
        container_samples[container] = {}
        for target in target_array:
            container_samples[container][target] = {}        
            for nservices in scenario_nservices[target]:
                container_samples[container][target][nservices] = {}
                if nservices > 1:
                    label = "multiple_services"            
                else:
                    label = "single_service"
                for metric in metrics_containers:
                    container_samples[container][target][nservices][metric] = {}                
                    for frame_resolution in array_frame_resolution[label]:
                        container_samples[container][target][nservices][metric][frame_resolution] = {}
                        for time in array_time[label]:
                            container_samples[container][target][nservices][metric][frame_resolution][time] = {}
                            for srv_index in range(1, nservices+1):
                                container_samples[container][target][nservices][metric][frame_resolution][time][srv_index] = {"samples1":{},"samples2":{}}                
                            
                                # Generating samples

                                prefix_file_name = "./results_"+target+"/"+str(nservices)+"/"+container+"-"+str(srv_index)+"_"+metric+"_SRV"+str(srv_index)+"_CAM"+str(srv_index)+"_"+target+"_"+time+"_"+frame_resolution
                                samples1, samples2 = generate_samples(prefix_file_name,metric,target)

                                # Generating statistical data and EDA charts

                                title_graph = container+"-"+str(srv_index)+"_"+metric+"_"+str(nservices)+"_SRV"+str(srv_index)+"_CAM"+str(srv_index)+"_"+target+"_"+time+"_"+frame_resolution
                                xlabel = "Values"
                                
                                generate_stats(
                                    container_samples[container][target][nservices][metric][frame_resolution][time][srv_index]["samples1"],samples1,
                                    container_samples[container][target][nservices][metric][frame_resolution][time][srv_index]["samples2"],samples2,
                                    title_graph,xlabel,metric,container)                     

                                #print(container_samples[container][target][nservices][metric][frame_resolution][time][srv_index]["samples1"])
                                #print(container_samples[container][target][nservices][metric][frame_resolution][time][srv_index]["samples2"])

def generate_data_latency():               
    for target in target_array:
        latency_samples[target] = {}
        for nservices in scenario_nservices[target]:
            latency_samples[target][nservices] = {}
            if nservices > 1:
                label = "multiple_services"            
            else:
                label = "single_service"
            for frame_resolution in array_frame_resolution[label]:
                latency_samples[target][nservices][frame_resolution] = {}
                for time in array_time[label]:
                    latency_samples[target][nservices][frame_resolution][time] = {}
                    for srv_index in range(1, nservices+1):
                        
                        latency_samples[target][nservices][frame_resolution][time][srv_index] = {}                           
                        
                        # Generating samples

                        prefix_file_name = "./results_"+target+"/"+str(nservices)+"/stats2_SRV"+str(srv_index)+"_CAM"+str(srv_index)+"_"+target+"_"+time+"_"+frame_resolution
                        
                        samples={}
                        for metric_defined in metrics_latency_defined:
                            samples[metric_defined] = []
                        generate_latency_samples(prefix_file_name,samples,target)

                        for metric_defined in metrics_latency_defined:
                            latency_samples[target][nservices][frame_resolution][time][srv_index][metric_defined] = {}
                            title_graph = "latency_"+metric_defined+"_"+str(nservices)+"_SRV"+str(srv_index)+"_CAM"+str(srv_index)+"_"+target+"_"+time+"_"+frame_resolution
                            xlabel = "Values"
                            generate_stats(
                            latency_samples[target][nservices][frame_resolution][time][srv_index][metric_defined],samples[metric_defined],
                            {},[],title_graph,xlabel,metric_defined,metric_defined)                     

                            # if frame_resolution == "1920_1080":
                            #     if time == "high":
                            #         if nservices == 1:
                            #             print()
                            #             print(metric_defined + " " + target + " " + str(nservices)  + " " + frame_resolution + " " + time)
                            #             print()

                            #             print(latency_samples[target][nservices][frame_resolution][time][srv_index][metric_defined])

def generate_data_classes():               
    for target in target_array:
        class_samples[target] = {}
        for nservices in scenario_nservices[target]:
            class_samples[target][nservices] = {}
            if nservices > 1:
                label = "multiple_services"            
            else:
                label = "single_service"
            for frame_resolution in array_frame_resolution[label]:
                class_samples[target][nservices][frame_resolution] = {}
                for time in array_time[label]:
                    class_samples[target][nservices][frame_resolution][time] = {}
                    for srv_index in range(1, nservices+1):
                        
                        class_samples[target][nservices][frame_resolution][time][srv_index] = {}                           
                        
                        # Generating samples

                        prefix_file_name = "./results_"+target+"/"+str(nservices)+"/stats1_SRV"+str(srv_index)+"_CAM"+str(srv_index)+"_"+target+"_"+time+"_"+frame_resolution
                        
                        samples={}
                        for metric in metrics_class:
                            samples[metric] = []
                        generate_class_samples(prefix_file_name,samples,target)       

                        for metric in metrics_class:
                            class_samples[target][nservices][frame_resolution][time][srv_index][metric] = {}
                            title_graph = "class_"+metric+"_"+str(nservices)+"_SRV"+str(srv_index)+"_CAM"+str(srv_index)+"_"+target+"_"+time+"_"+frame_resolution
                            xlabel = "Values"
                            generate_stats(
                            class_samples[target][nservices][frame_resolution][time][srv_index][metric],samples[metric],
                            {},[],title_graph,xlabel,metric,metric)                     

                            #print(metric)
                            print(class_samples[target][nservices][frame_resolution][time][srv_index][metric])

# Per Device - Metrics Global

def generate_charts_per_device_global():
    fig_num = 0
    width = 0.2  # the width of the bars
    opacity = 0.5
    error_config = {'ecolor': 'black'}
    vectors_mean = {}
    vectors_errors = {}

    fixed_frame_resolution="1920_1080"
    #fixed_frame_resolution="960_540"
    fixed_nservices=1
    fixed_time="high"

    y = np.arange(4)            
    metrics = metrics_global_defined_for_charts
    xlabel = "Percentage (%)"
    plt.figure(fig_num)
    fig, ax = plt.subplots()
    rects = []
    pos = y
    
    for metric in metrics: 
        vectors_mean[metric]=[]
        vectors_errors[metric]=[]        
        for target in target_array:                       
            if target == "jetson":
                for i in scenario_nservices["jetson"]:                    
                    vectors_mean[metric].append(round(global_samples[target][i][metric][fixed_frame_resolution][fixed_time]["samples1"]["wilcoxon_test_median"],0))
                    vectors_errors[metric].append(round(global_samples[target][i][metric][fixed_frame_resolution][fixed_time]["samples1"]["wilcoxon_test_error"],0))                   
            else:
                if metric != "tegrastat_tegrastats.gpu_load":
                    vectors_mean[metric].append(round(global_samples[target][fixed_nservices][metric][fixed_frame_resolution][fixed_time]["samples1"]["wilcoxon_test_median"],0))
                    vectors_errors[metric].append(round(global_samples[target][fixed_nservices][metric][fixed_frame_resolution][fixed_time]["samples1"]["wilcoxon_test_error"],0))
                else:
                    vectors_mean[metric].append(0)
                    vectors_errors[metric].append(0)
        rect = ax.barh(pos, vectors_mean[metric], width, alpha=opacity, xerr=vectors_errors[metric],error_kw=error_config)
        ax.bar_label(rect, padding=3)
        rects.append(rect)
        pos = pos + width
        
    fig.text(0.5, 0.01, xlabel, ha='center', fontsize=14)
    #fig.text(0.01, 0.5, "Edge Devices", va='center', rotation='vertical', fontsize=16)
    #ax.set_title("")
    ax.set_yticks(y + width)    
    ylabels=["Jetson 1 Srv.","Jetson 2 Srv.","Jetson 3 Srv.","RPI4"]    
    ax.set_yticklabels([re.sub("(.{7})", "\\1\n", label, 0, re.DOTALL) for label in ylabels],fontsize=14)
    ax.invert_yaxis()
    ax.set_xticks([20,40,60,80,100])
    ax.tick_params(labelsize=14)
    legend_classes = tuple([rect[0] for rect in rects])
    legend_titles = tuple([array_global_title[met] for met in metrics])
    ax.legend(legend_classes, legend_titles, bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=3, mode="expand",borderaxespad=0.,prop={'size':14})
    #ax.legend(legend_classes, legend_titles)

    plt.savefig("./figures/charts/global/per_device_global.pdf",format='pdf')

def generate_charts_per_device_per_resolution_global():
    fig_num = 0
    width = 0.2  # the width of the bars
    opacity = 0.5
    error_config = {'ecolor': 'black'}
    vectors_mean = {}
    vectors_errors = {}

    #fixed_frame_resolution="1920_1080"
    #fixed_frame_resolution="960_540"
    fixed_nservices=1
    #fixed_time="high"

    y = np.arange(2)            
    metrics = metrics_global_defined_for_charts
    xlabel = "Percentage (%)"
    plt.figure(fig_num)
    fig, axs = plt.subplots(3,2,figsize=(16, 12))    
    
    for index1 in range(0,3):
        fixed_frame_resolution=array_frame_resolution["single_service"][index1]
        for index2 in range(0,2):
            fixed_time=array_time["single_service"][index2]
            ax = axs[index1,index2]
            rects = []
            pos = y
            for metric in metrics: 
                vectors_mean[metric]=[]
                vectors_errors[metric]=[]        
                for target in target_array:                       
                    #print(latency_samples[target][fixed_nservices][fixed_frame_resolution][fixed_time][1].keys())
                    if target == "jetson":
                        vectors_mean[metric].append(round(global_samples[target][fixed_nservices][metric][fixed_frame_resolution][fixed_time]["samples1"]["wilcoxon_test_median"],0))
                        vectors_errors[metric].append(round(global_samples[target][fixed_nservices][metric][fixed_frame_resolution][fixed_time]["samples1"]["wilcoxon_test_error"],0))
                    else:
                        if metric != "tegrastat_tegrastats.gpu_load":
                            vectors_mean[metric].append(round(global_samples[target][fixed_nservices][metric][fixed_frame_resolution][fixed_time]["samples1"]["wilcoxon_test_median"],0))
                            vectors_errors[metric].append(round(global_samples[target][fixed_nservices][metric][fixed_frame_resolution][fixed_time]["samples1"]["wilcoxon_test_error"],0))
                        else:
                            vectors_mean[metric].append(0)
                            vectors_errors[metric].append(0)
                rect = ax.barh(pos, vectors_mean[metric], width, alpha=opacity, xerr=vectors_errors[metric],error_kw=error_config)
                ax.bar_label(rect, padding=3)
                rects.append(rect)
                pos = pos + width
            fig.text(0.5, 0.01, xlabel, ha='center', fontsize=14)
            ax.set_yticks(y + width)    
            ylabels=["Jetson 1 Srv.","RPI4"]    
            ax.set_yticklabels([re.sub("(.{7})", "\\1\n", label, 0, re.DOTALL) for label in ylabels],fontsize=14)
            ax.invert_yaxis()
            ax.set_title(fixed_frame_resolution + " - " + fixed_time + " traffic")
            ax.set_xticks([20,40,60,80,100])
            ax.tick_params(labelsize=14)
            legend_classes = tuple([rect[0] for rect in rects])
            legend_titles = tuple([array_global_title[met] for met in metrics])
            #ax.legend(legend_classes, legend_titles, bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=3, mode="expand",borderaxespad=0.,prop={'size':14})
            ax.legend(legend_classes, legend_titles)

    plt.savefig("./figures/charts/global/per_device_per_frame_reolution_global.pdf",format='pdf')

# Per Device - Per Container - Metrics Container

def generate_charts_per_device_per_container_metrics_container():
    
    fig_num = 0
    width = 0.2  # the width of the bars
    opacity = 0.5
    error_config = {'ecolor': 'black'}
    vectors_mean = {}
    vectors_errors = {}

    fixed_frame_resolution="1920_1080"
    #fixed_frame_resolution="960_540"
    fixed_nservices=1
    fixed_time="high"  

    y = np.arange(4)            
    metrics = metrics_containers         

    for metric in metrics:
        xlabel = array_metrics_title[metric]
        fig_num = fig_num + 1  
        plt.figure(fig_num)
        #fig, ax = plt.subplots(figsize=(16, 9))
        fig, ax = plt.subplots()
        rects = []
        pos = y
        if metric in traffic_metric_array:
            sample_index = "samples2"
        else:
            sample_index = "samples1"
        for container in containers:
            vectors_mean[container] = []
            vectors_errors[container] = []
            for target in target_array:                
                if target == "jetson":
                    for i in scenario_nservices["jetson"]:
                        vectors_mean[container].append(round(container_samples[container][target][i][metric][fixed_frame_resolution][fixed_time][i][sample_index]["wilcoxon_test_median"],2))
                        vectors_errors[container].append(round(container_samples[container][target][i][metric][fixed_frame_resolution][fixed_time][i][sample_index]["wilcoxon_test_error"],2))                        
                else:
                    vectors_mean[container].append(round(container_samples[container][target][fixed_nservices][metric][fixed_frame_resolution][fixed_time][1][sample_index]["wilcoxon_test_median"],2))
                    vectors_errors[container].append(round(container_samples[container][target][fixed_nservices][metric][fixed_frame_resolution][fixed_time][1][sample_index]["wilcoxon_test_error"],2))
            rect = ax.barh(pos, vectors_mean[container], width, alpha=opacity, xerr=vectors_errors[container],error_kw=error_config)
            ax.bar_label(rect, padding=3)
            rects.append(rect)
            pos = pos + width

        fig.text(0.5, 0.01, xlabel, ha='center', fontsize=14)
        ax.set_yticks(y + width)    
        ylabels=["Jetson 1 Srv.","Jetson 2 Srv.","Jetson 3 Srv.","RPI4"]    
        ax.set_yticklabels([re.sub("(.{7})", "\\1\n", label, 0, re.DOTALL) for label in ylabels],fontsize=14)
        ax.invert_yaxis()        
        ax.tick_params(labelsize=14)
        legend_classes = tuple([rect[0] for rect in rects])
        legend_titles = tuple([array_container_title[container] for container in containers])
        ax.legend(legend_classes, legend_titles)

        plt.savefig("./figures/charts/containers/per_device_"+metric+".pdf",format='pdf')

# Per Device - Metrics Latency

def generate_charts_per_device_metrics_latency():
    fig_num = 0
    width = 0.1  # the width of the bars
    opacity = 0.5
    error_config = {'ecolor': 'black'}
    vectors_mean = {}
    vectors_errors = {}

    fixed_frame_resolution="1920_1080"
    #fixed_frame_resolution="960_540"
    fixed_nservices=1
    fixed_time="high"

    y = np.arange(4)            
    metrics = metrics_latency_defined_for_charts
    xlabel = "Latency (ms)"
    plt.figure(fig_num)
    #fig, ax = plt.subplots(figsize=(16, 9))
    fig, ax = plt.subplots()
    rects = []
    pos = y
    
    for metric in metrics: 
        vectors_mean[metric]=[]
        vectors_errors[metric]=[]        
        for target in target_array:                       
            #print(latency_samples[target][fixed_nservices][fixed_frame_resolution][fixed_time][1].keys())
            if target == "jetson":
                for i in scenario_nservices["jetson"]:
                    #print(latency_samples[target][i][fixed_frame_resolution][fixed_time][1][metric])
                    vectors_mean[metric].append(round(latency_samples[target][i][fixed_frame_resolution][fixed_time][i][metric]["wilcoxon_test_median"],2))
                    vectors_errors[metric].append(round(latency_samples[target][i][fixed_frame_resolution][fixed_time][i][metric]["wilcoxon_test_error"],2))
                    # rect = ax.barh(pos, vectors_mean[metric], width, alpha=opacity, xerr=vectors_errors[metric],error_kw=error_config)
                    # ax.bar_label(rect, padding=3)
                    # rects.append(rect)
                    # pos = pos + width
            else:
                vectors_mean[metric].append(round(latency_samples[target][fixed_nservices][fixed_frame_resolution][fixed_time][1][metric]["wilcoxon_test_median"],2))
                vectors_errors[metric].append(round(latency_samples[target][fixed_nservices][fixed_frame_resolution][fixed_time][1][metric]["wilcoxon_test_error"],2))
        rect = ax.barh(pos, vectors_mean[metric], width, alpha=opacity, xerr=vectors_errors[metric],error_kw=error_config)
        ax.bar_label(rect, padding=3)
        rects.append(rect)
        pos = pos + width
    fig.text(0.5, 0.01, xlabel, ha='center', fontsize=14)
    #fig.text(0.01, 0.5, "Edge Devices", va='center', rotation='vertical', fontsize=16)
    #ax.set_title("")
    ax.set_yticks(y + width)    
    ylabels=["Jetson 1 Srv.","Jetson 2 Srv.","Jetson 3 Srv.","RPI4"]    
    ax.set_yticklabels([re.sub("(.{7})", "\\1\n", label, 0, re.DOTALL) for label in ylabels],fontsize=14)
    ax.invert_yaxis()
    #ax.set_xticks([200,400,600,800,1000,1200,1400])
    ax.tick_params(labelsize=14)
    legend_classes = tuple([rect[0] for rect in rects])
    legend_titles = tuple([array_latency_title[latency] for latency in metrics])
    #ax.legend(legend_classes, legend_titles, bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand",borderaxespad=0.,prop={'size':14})
    ax.legend(legend_classes, legend_titles)

    plt.savefig("./figures/charts/latency/per_device_latency.pdf",format='pdf')



generate_data_global()
generate_data_container()
generate_data_latency()
#generate_data_classes()

generate_charts_per_device_global()
generate_charts_per_device_per_resolution_global()
generate_charts_per_device_per_container_metrics_container()
generate_charts_per_device_metrics_latency()






