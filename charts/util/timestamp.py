from datetime import datetime

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