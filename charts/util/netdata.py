from timestamp import get_datetime

def get_value (row,metric):
    
    value1, value2 = None, None

    #GLOBAL - Total CPU utilization (all cores) (percentage)
    if metric == "system.cpu":
        #value1 = float(row[1]) + float(row[2]) + float(row[3]) + float(row[4]) + float(row[5])
        #if target == "jetson":
        #    value1 = float(row[3])
        #else:
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