from cognit import device_runtime
from cognit.modules._logger import CognitLogger
import random
import sys
import time
import datetime
import os
import logging
import pickle
import configparser
import click


sys.path.append(".")

threshold_dict = { 
    "1001":  21.905754,
    "1002":  47.366278,
    "1003":  24.056425,
    "1004":  24.197845,
    "1030":  50.226909,
    "1031":  23.233456,
    "1032":  23.544794,
    "1033":  47.115531,
    "1034":  20.858517,
    "1038":  51.408055,
    "1039":  4.9611476,
    "1051":  47.1024,
    "1054":  5.1681335,
    "1058":  23.689708,
    "1059":  5.0577443,
    "1062":  4.6511411,
    "1063":  22.646405,
    "1064":  53.795752,
    "1072":  49.082198,
    "1081":  49.998705,
    "1086":  5.3496898,
    "1095":  4.9391767,
    "1101":  53.721154,
    "1103":  5.0153165,
    "1104":  44.630741,
    "1105":  5.40165,
    "1109":  20.825566,
    "1113":  47.079005,
    "1134":  44.91566,
    "1136":  50.250718,
    "1137":  5.4090267,
    "1139":  23.172123,
    "1160":  4.5717496,
    "1161":  51.045798,
    "1163":  4.7245781,
    "1169":  51.067682,
    "1171":  47.498432,
    "1180":  21.626183}

def cli(indicators: str):
    import subprocess
    import json
    import os
    if 'serverless' in os.environ['PWD']:
        from modules._logger import CognitLogger
    else:
        from cognit.modules._logger import CognitLogger

    cognit_logger = CognitLogger()
    cognit_logger.debug("# Calling /opt/smartcity_faas/call_sumo.sh {}".format(indicators))
    result = subprocess.run(["/opt/smartcity_faas/call_sumo.sh {}".format(indicators)], capture_output=True, text=True, shell=True).stdout.strip("\n")
    cognit_logger.debug(f"# result {result}")
    return result


def s3_put_file(bucket_name, target_key, file_name, access_key, secret_key):
    import boto3
    import os
    if 'serverless' in os.environ['PWD']:
        from modules._logger import CognitLogger
    else:
        from cognit.modules._logger import CognitLogger

    for library in ['boto3', 'botocore', 'urllib3']:
        logging.getLogger(library).setLevel(logging.INFO)

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
    import os
    if 'serverless' in os.environ['PWD']:
        from modules._logger import CognitLogger
    else:
        from cognit.modules._logger import CognitLogger

    for library in ['boto3', 'botocore', 'urllib3']:
        logging.getLogger(library).setLevel(logging.INFO)

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
        return True
    except Exception as e:
        if "An error occurred (NoSuchKey)" in str(e):
            cognit_logger.debug(f"# NoSuchKey")
            return False
        cognit_logger.error(f"# s3_get_file - An exception has occured: {str(e)}")
        raise Exception("In s3_get_file")


def congestion_trans(congestion):
    congestion_dict = {
            "LOW": {"scale": 0.5, "step_length": 1} , 
            "MEDIUM": {"scale": 1, "step_length": 1}, 
            "HIGH": {"scale": 2.0, "step_length": 5}
    }
    return congestion_dict[congestion]

def threshold(junction):
    return threshold_dict[junction]

def calculate_priority(junction, result):
    mean_timeLoss = float(result[1].removeprefix("result: "))
    cognit_logger.debug(f"# mean_timeLoss {mean_timeLoss} threshold(junction) {threshold(junction) }-> {mean_timeLoss > threshold(junction)}")
    return mean_timeLoss > threshold(junction)

def get_traffic_status(city, junction):
    if force_congestion:
        cognit_logger.debug(f"# Env-var force congestion set to {force_congestion}")
        return force_congestion
    else:
        cognit_logger.debug(f"# Getting traffic status for {city}/{junction}")
        result = None
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
            return "autumn"
        elif (mmdd >= "1201" and mmdd <= "1231") or (mmdd >= "0101" and mmdd <= "0229"):
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
    def test_aux():
        assert "spring" == season('0301')
        assert "spring" == season('0302')
        assert "spring" == season('0401')
        assert "spring" == season('0501')
        try:
            assert Exception("Month/date out of range") == season('0532'), "Date not valid"
        except Exception as e:
            print(f"Exception {e}")
            assert e == Exception("Month/date out of range")
        assert "workday" == weekday(9)
        assert "workday" == weekday(5)
        assert "weekend" == weekday(0)
        assert "weekend" == weekday(6)
        assert hourly_range(25) == "00-05"
        assert hourly_range(0) == "00-05"
        assert hourly_range(5) == "00-05"
        assert hourly_range(7) == "06-09"

    import datetime
    now = datetime.datetime.now()
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
    cognit_logger.debug(f"# calling s3_put_file {city}/{junction}/{filename}")
    result = s3_put_file('smartcity', f'{city}/{junction}/{filename}', f'/tmp/{city}_{junction}_{filename}', access_key, secret_key)


def faas_request(city, junction, requirements):

    import random
    try:
        # Instantiate a device Device Runtime
        cognit_logger.debug("# Using configuration cognit-ice.yml")
        my_device_runtime = device_runtime.DeviceRuntime("cognit-ice.yml")
        my_device_runtime.init(requirements)
        # Offload and execute a function

        start_time = time.perf_counter()

        congestion = get_traffic_status(city, junction)
        precalc_simulation_filename = get_precalc_simulation_filename(congestion)

        priority = None
        if cache_results:
            priority = get_precalc_priority(city, junction, precalc_simulation_filename)

        if not cache_results or priority is None:
            sumo_parameters = congestion_trans(congestion)
            cognit_logger.debug(f"# No precalculated priority, running simulation")
            ret_code, res, err = my_device_runtime.call(cli, f"Granada {junction} {sumo_parameters['scale']} {sumo_parameters['step_length']}")
            cognit_logger.debug(f"# Return code: {ret_code}")
            cognit_logger.debug(f"# Result: {res}")
            cognit_logger.debug(f"# Error: {err}")
            priority = calculate_priority(junction, res)
            cognit_logger.debug(f"# priority: {priority}")
            cognit_logger.debug(f"# Writing precalc simulation to /tmp/{city}_{junction}_{precalc_simulation_filename}")
            write_precalc_priority(city, junction, precalc_simulation_filename, priority)
        print(priority)
        end_time = time.perf_counter()
        cognit_logger.debug(f"# Execution time: {(end_time-start_time):.6f} seconds")

    except Exception as e:
        import traceback
        cognit_logger.error(traceback.format_exc())
        cognit_logger.error("# An exception has occured: " + str(e))
        print(traceback.format_exc())
        raise


def s3_get_buckets(bucket_name, access_key, secret_key):
    import boto3
    import os
    if 'serverless' in os.environ['PWD']:
        from modules._logger import CognitLogger
    else:
        from cognit.modules._logger import CognitLogger

    for library in ['boto3', 'botocore', 'urllib3']:
        logging.getLogger(library).setLevel(logging.INFO)

    MINIO_ENDPOINT = "http://s3.sovereignedge.eu"
    cognit_logger.debug(f"# s3_get_buckets")
    try:
        s3 = boto3.resource(
            "s3",
            endpoint_url="https://s3.sovereignedge.eu/",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        bucket = s3.Bucket(bucket_name)
        result = [bucket_object.key for bucket_object in bucket.objects.all()]
    except Exception as e:
        cognit_logger.error("# s3_get_buckets - An exception has occured: {str(e)}")
        return False

    cognit_logger.debug(f"# s3_get_buckets: {result}")
    return result

def get_env_var(name, required=False, default=None):
    if name in os.environ:
        return os.environ[name]
    elif required:
        raise Exception(f"Required environment variable {name} not provided")
    else:
        return default

def get_file_handler():

    # Set level
    file_handler = logging.FileHandler('/tmp/device_runtime.log')
    file_handler.setLevel(logging.DEBUG)

    # Set log format
    formatter = logging.Formatter("[%(asctime)5s] [%(levelname)-s] %(message)s")
    file_handler.setFormatter(formatter)

    return file_handler

def set_logging(level):
    if 'serverless' in os.environ['PWD']:
        from modules._logger import CognitLogger
    else:
        from cognit.modules._logger import CognitLogger

    logger = CognitLogger()
    logger.logger.removeHandler(logger.logger.handlers[0])
    logger.logger.addHandler(get_file_handler())
    logger.logger.setLevel(level)
    return logger


def main(config_file='cognit.properties'):
    global access_key, secret_key, cognit_logger, cache_results, force_congestion
    global cognit_logger 
    cognit_logger = set_logging(logging.DEBUG)
    cognit_logger.debug("# Running SmartCity FaaS")
    if not os.path.exists(config_file):
        cognit_logger.error("# File {config_file doesn't exist}")
        raise FileNotFoundError

    try:
        config = configparser.ConfigParser(allow_no_value=True, delimiters=('=', ':'),
                                   comment_prefixes=('#', '!'), inline_comment_prefixes=('#',))
        config.optionxform = str
        config.read(config_file, encoding='utf-8')

        access_key = config['default']['ACCESS_KEY_ID']
        secret_key = config['default']['SECRET_ACCESS_KEY']
        junction = config['default']['JUNCTION']
        city = config['default']['CITY']
        force_congestion = config['default']['FORCE_CONGESTION']

        cache_results_str = config['default']['CACHE_RESULTS']
        cache_results = cache_results_str.lower() in ['true', '1', 'yes'] if cache_results_str else None

        requirements = {}
        for key in config['requirements']:
            if not key in ['LATITUDE', 'LONGITUDE']:
                requirements[key] = config['requirements'][key]
                if key == 'PROVIDERS':
                    requirements[key] = requirements[key].split(',')

                elif requirements[key] == 'True':
                    requirements[key] = True
                elif requirements[key] == 'False':
                    requirements[key] = False

        if 'LATITUDE' in config['requirements'] and 'LONGITUDE' in config['requirements']:
            requirements['GEOLOCATION'] = {
                "latitude": float(config['requirements']['LATITUDE']),
                "longitude": float(config['requirements']['LONGITUDE'])
            }

        requirements['ID'] = f"{city}-{junction}"

        faas_request(city, junction, requirements)

    except Exception as e:
        import traceback
        print(traceback.format_exc()) 
        cognit_logger.error("# An exception has occured: " + str(e))
        exit(-1)



if __name__ == "__main__":

    @click.command()
    @click.option('--config_file', default='cognit.properties', help='Path to file with properties')
    def main_cli(config_file):
        main(config_file)

    main_cli()

