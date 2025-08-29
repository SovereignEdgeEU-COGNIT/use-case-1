# This is needed to run the example from the cognit source code
# If you installed cognit with pip, you can remove this
from cognit import device_runtime
from cognit.modules._logger import CognitLogger
# import examples.offload_minio as minio
import random
import sys
import time
import datetime
import os
# from locust import HttpUser, task, between, events


sys.path.append(".")


def cli(indicators: str):
    import subprocess
    import json
    result = subprocess.run(["/opt/smartcity_faas/call_sumo_gr.sh {}".format(indicators)], capture_output=True, text=True, shell=True).stdout.strip("\n")
    # print(f">>> result {result}")
    return result.split(" - ")[0]


# Execution requirements, dependencies and policies
REQS_NEW = {
      "FLAVOUR": "SmartCity",
      "MAX_FUNCTION_EXECUTION_TIME": 3.0,
      "MAX_LATENCY": 45,
      "MIN_ENERGY_RENEWABLE_USAGE": 75,
      # "GEOLOCATION": "ACISA RIPOLLET 08291"
      # "GEOLOCATION": "IKERLAN ARRASATE/MONDRAGON 20500"
      "GEOLOCATION": {
          "latitude": 43.05,
          "longitude": -2.53
      }
}

def minio_list_buckets():
    try:
        MINIO_ENDPOINT = "http://192.168.120.100:9000" # TESTBED
        # MINIO_ENDPOINT = "http://127.0.0.1:9000" # LOCAL TESTS

        from modules._logger import CognitLogger
        cognit_logger = CognitLogger()
        cognit_logger.debug(f"#  [DR] Listing buckets in {MINIO_ENDPOINT}")

        from modules._minio_client import MinioClient
        minio_client = MinioClient(
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id="minio_user",
            aws_secret_access_key="minio_psw"
        )
        response = minio_client.list_buckets()
        return response
    except Exception as e:
        return [f"Error listing buckets: {str(e)}"]


def s3_put_file(bucket_name, target_key, file_name, access_key, secret_key):
    import boto3
    import logging
    import os
    if 'serverless' in os.environ['PWD']:
        from modules._logger import CognitLogger
    else:
        from cognit.modules._logger import CognitLogger

    for library in ['boto3', 'botocore', 'urllib3']:
        logging.getLogger(library).setLevel(logging.INFO)

    cognit_logger = CognitLogger()
    cognit_logger.debug(f"# s3_put_file")
    try:
        s3 = boto3.resource(
            "s3",
            endpoint_url="https://s3.sovereignedge.eu/",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        ) 
        cognit_logger.debug(f"# Calling s3.Object({bucket_name}, {target_key}, {file_name})")
        result = s3.Object(bucket_name, target_key).put(Body=open(file_name, 'rb'))
        cognit_logger.debug(f"# s3.Object result {result['ResponseMetadata']['HTTPStatusCode']}")
        return result['ResponseMetadata']['HTTPStatusCode']
    except Exception as e:
        cognit_logger.error("# An exception has occured: " + str(e))

def s3_get_file(bucket_name, target_key, file_name, access_key, secret_key):
    import boto3
    import logging
    import os
    if 'serverless' in os.environ['PWD']:
        from modules._logger import CognitLogger
    else:
        from cognit.modules._logger import CognitLogger

    for library in ['boto3', 'botocore', 'urllib3']:
        logging.getLogger(library).setLevel(logging.INFO)

    cognit_logger = CognitLogger()
    cognit_logger.debug(f"# s3_get_file({bucket_name}, {target_key}, {file_name})")
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url="https://s3.sovereignedge.eu/",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        cognit_logger.debug("# calling s3.get_object")
        result = s3.get_object(Bucket=bucket_name, Key=target_key)
        with open(file_name, 'wb') as file_dest:
            file_dest.write(result['Body'].read())
        # cognit_logger.debug(f"# result {result}")
        # cognit_logger.debug(f"# result {result['Body'].read()}")
        return True
    except Exception as e:
        if "An error occurred (NoSuchKey)" in str(e):
            cognit_logger.debug(f"# NoSuchKey")
            return False
        cognit_logger.error(f"# s3_get_file - An exception has occured: {str(e)}")
        raise Exception("In s3_get_file")


def congestion_trans(congestion):
    congestion_dict = {"LOW": 0.5 , "MEDIUM": 1.0, "HIGH": 2.0}
    return congestion_dict[congestion]


def get_traffic_status(city, junction):
    cognit_logger.debug(f"# Getting traffic status for {city}/{junction}")

    try:
        result = s3_get_file('smartcity', f'{city}/{junction}/traffic_status.txt', f'/tmp/{city}_{junction}_traffic_status.txt', access_key, secret_key)
        cognit_logger.debug(f"# s3_get_file result: {result}")
    except Exception as e:
        cognit_logger.debug(f"# Exception on FaaS call to s3_get_file")
        if "NoSuchKey) when calling the GetObject operation" in str(e):
            congestion = "MEDIUM"
            cognit_logger.debug(f"# No congestion data available. CONGESTION set to {congestion}")
            return congestion

    if result:
        with open(f'/tmp/{city}_{junction}_traffic_status.txt', 'r', encoding="ascii") as file_traffic_status:
            for line in file_traffic_status.read().splitlines():
                if "CONGESTION: " in line:
                    congestion = line.removeprefix("CONGESTION: ")
                elif "LAST_UPDATE: " in line:
                    last_update = line.removeprefix("LAST_UPDATE: ")
        cognit_logger.debug(f"# Traffic status: CONGESTION {congestion} LAST_UPDATE {last_update}")
    else:
        congestion = "MEDIUM"
        cognit_logger.debug(f"# No congestion data available. CONGESTION set to {congestion}")

    return congestion


def get_precalc_simulation_filename(traffic_congestion):
    def season(mmdd):
        if mmdd >= "0301" and mmdd <= "0531":
            return "spring"
        elif mmdd >= "0601" and mmdd <= "0831":
            return "summer"
        elif mmdd >= "0901" and mmdd <= "1130":
            return "autum"
        elif mmdd >= "1201" and mmdd <= "0229":
            return "winter"
        else:
            raise Exception("Month/date out of range")

    def weekday(day):
        if day >= 1 and day <= 5:
            return "workday"
        elif day == 0 or day == 6:
            return "weekend"

    def hourly_range(HH):
        ranges = [(0, 5), (6, 9), (9, 12), (13, 15), (16, 19), (20, 22), (23, 23)]
        for start, end in ranges:
            if HH >= start and HH <= end:
                return f"{start:02d}-{end:02d}"

    import datetime
    now = datetime.datetime.now()
    # assert "spring" == season('0301')
    # assert "spring" == season('0302')
    # assert "spring" == season('0401')
    # assert "spring" == season('0501')
    # try:
    #     assert Exception("Month/date out of range") == season('0532'), "Date not valid"
    # except Exception as e:
    #     print(f"Exception {e}")
    #     assert e == Exception("Month/date out of range")
    # assert "workday" == weekday(9)
    # assert "workday" == weekday(5)
    # assert "weekend" == weekday(0)
    # assert "weekend" == weekday(6)
    # assert hourly_range(25) == "00-05"
    # assert hourly_range(0) == "00-05"
    # assert hourly_range(5) == "00-05"
    # assert hourly_range(7) == "06-09"
    if traffic_congestion in ["LOW", "MEDIUM", "HIGH"]:
        filename = f"{season(now.strftime('%m%d'))}-{weekday(now.weekday())}-{hourly_range(now.hour)}-{traffic_congestion}.txt"
        return filename
    else:
        raise Exception("congestion doesn't have a valid value like LOW|MEDIUM|HIGH")



def get_precalc_priority(city, junction, filename):
    result = s3_get_file('smartcity', f'{city}/{junction}/{filename}', f'/tmp/{city}_{junction}_{filename}', access_key, secret_key)

    if result:
        with open(f'/tmp/{city}_{junction}_{filename}', 'r', encoding="ascii") as precalc_file:
            for line in precalc_file.read().splitlines():
                if "PRIORITY:" in line:
                    priority = line.removeprefix("PRIORITY:")
                elif "LAST_UPDATE:" in line:
                    last_update = line.removeprefix("LAST_UPDATE:")
        cognit_logger.debug(f"# Precalculated values: PRIORITY {priority} LAST_UPDATE {last_update}")
        return priority
    else:
        return None


def write_precalc_priority(city, junction, filename, priority):
    with open(f'/tmp/{city}_{junction}_{filename}', 'w', encoding="ascii") as precalc_file:
        precalc_file.write(f"PRIORITY:{priority}\n")
        current_datetime = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
        precalc_file.write(f"LAST_UPDATE::{current_datetime}\n")
    # ret_code, res, err = my_device_runtime.call(s3_put_file, 'smartcity', f'{city}/{junction}/{precalc_simulation_filename}', f'/tmp/{city}_{junction}_{precalc_simulation_filename}', access_key, secret_key)
    cognit_logger.debug(f"# calling s3_put_file {city}/{junction}/{filename}")
    result = s3_put_file('smartcity', f'{city}/{junction}/{filename}', f'/tmp/{city}_{junction}_{filename}', access_key, secret_key)


def faas_request(city, junction):

    import random
    try:
        cognit_logger = CognitLogger()
        # Instantiate a device Device Runtime
        my_device_runtime = device_runtime.DeviceRuntime("./examples/cognit-ice.yml")
        my_device_runtime.init(REQS_NEW)
        # Offload and execute a function

        start_time = time.perf_counter()
        # junction = random.randint(1001, 1004)

        congestion = get_traffic_status(city, junction)
        precalc_simulation_filename = get_precalc_simulation_filename(congestion)
        priority = get_precalc_priority(city, junction, precalc_simulation_filename)

        if priority is None:
            cognit_logger.debug("# No precalculated priority, running simulation")
            ret_code, res, err = my_device_runtime.call(cli, f"Granada {junction} {congestion_trans(congestion)} -n CO2 CO NOx")
            priority = bool(random.getrandbits(1))
            cognit_logger.debug(f"# Random priority(to be replaced): {priority}")
            cognit_logger.debug(f"# Return code: {ret_code}")
            cognit_logger.debug(f"# Result: {res}")
            # cognit_logger.debug(f"# Result CO2: {res['CO2']}")
            cognit_logger.debug(f"# Error: {err}")
            cognit_logger.debug(f"# Writing precalc simulation to /tmp/{city}_{junction}_{precalc_simulation_filename}")
            write_precalc_priority(city, junction, precalc_simulation_filename, priority)
        print(priority)
        end_time = time.perf_counter()
        cognit_logger.debug(f"# Execution time: {(end_time-start_time):.6f} seconds")
        
        # result = my_device_runtime.call(minio_list_buckets)
        # print(f">>> result {result}")
        # exit(0)



    except Exception as e:
        cognit_logger.error("# An exception has occured: " + str(e))
        import traceback
        cognit_logger.error(traceback.format_exc())
        exit(-1)

def s3_get_buckets(bucket_name, access_key, secret_key):
    import boto3
    import logging
    import os
    if 'serverless' in os.environ['PWD']:
        from modules._logger import CognitLogger
    else:
        from cognit.modules._logger import CognitLogger

    for library in ['boto3', 'botocore', 'urllib3']:
        logging.getLogger(library).setLevel(logging.INFO)

    MINIO_ENDPOINT = "http://s3.sovereignedge.eu"
    cognit_logger = CognitLogger()
    cognit_logger.debug(f"# s3_get_buckets")
    try:
        s3 = boto3.resource(
        # s3 = boto3.client(
            "s3",
            endpoint_url="https://s3.sovereignedge.eu/",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
            # endpoint_url="http://192.168.120.100:9000",
            # aws_access_key_id="minio_user",
            # aws_secret_access_key="minio_psw"
        )

        bucket = s3.Bucket(bucket_name)
        result = [bucket_object.key for bucket_object in bucket.objects.all()]
    except Exception as e:
        cognit_logger.error("# s3_get_buckets - An exception has occured: {str(e)}")
        return False

    cognit_logger.debug(f"# s3_get_buckets: {result}")
    # bucket = s3.list_buckets()
    # cognit_logger.debug(f"# s3_get_buckets: {bucket}")
    return result




if __name__ == "__main__":
    cognit_logger = CognitLogger()
    cognit_logger.debug("# Running SmartCity FaaS")
    try:
        access_key = os.environ['AWS_ACCESS_KEY_ID']
        secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
        junction = os.environ['JUNCTION']
        city = os.environ['CITY']
    except Exception as e:
        cognit_logger.error("# An exception has occured: " + str(e))
        exit(-1)

    faas_request(city, junction)

