# This is needed to run the example from the cognit source code
# If you installed cognit with pip, you can remove this
from cognit import device_runtime
from cognit.modules._logger import CognitLogger
import random
import sys
import time


sys.path.append(".")


def cli(indicators: str):
    import subprocess
    return subprocess.run(["/opt/smartcity_faas/call_sumo_gr.sh {}".format(indicators)], capture_output=True, text=True, shell=True).stdout.strip("\n")


# Execution requirements, dependencies and policies
REQS_NEW = {
      "FLAVOUR": "SmartCity_bcn_V2",
      "MAX_FUNCTION_EXECUTION_TIME": 3.0,
      "MAX_LATENCY": 45,
      "MIN_ENERGY_RENEWABLE_USAGE": 75,
      "GEOLOCATION": "ACISA RIPOLLET 08291"
}

def faas_request():
    try:
        cognit_logger = CognitLogger()
        # Instantiate a device Device Runtime
        my_device_runtime = device_runtime.DeviceRuntime("./examples/cognit-ice.yml")
        my_device_runtime.init(REQS_NEW)
        # Offload and execute a function

        start_time = time.perf_counter()
        junction = random.randint(1001, 1004)
        return_code, result = my_device_runtime.call(cli, f"Granada {junction} -n CO2 CO NOx")
        print("Status code: " + str(return_code))
        print("Result: " + str(result))
        cognit_logger.info(f">>>>>>>> result {result}")
        end_time = time.perf_counter()
        print(f"Execution time: {(end_time-start_time):.6f} seconds")


    except Exception as e:
        print("An exception has occured: " + str(e))
        exit(-1)


if __name__ == "__main__":
    print("Running uc1.py")
    faas_request()


from locust import HttpUser, task, between, events
class UC1_Test(HttpUser):
    wait_time = between(1, 5)

    @task
    def run_faas(self):
        start_time = time.time()
        try:
            result = faas_request()
        except Exception as e:
            print(">>> An exception has occured: " + str(e))
            exit(-1)
        total_time = (time.time() - start_time) * 1000

        # Record the execution time as a custom event

        events.request.fire(
            request_type="Cognit remote call",
            name="UC1_FAAS",
            response_time=total_time,
            response_length=0,
            exception=result
        )
