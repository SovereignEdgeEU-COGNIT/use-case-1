# This is needed to run the example from the cognit source code
# If you installed cognit with pip, you can remove this
import sys
import time
import random
from cognit.modules._logger import CognitLogger

sys.path.append(".")


from cognit import (
    EnergySchedulingPolicy,
    FaaSState,
    ServerlessRuntimeConfig,
    ServerlessRuntimeContext,
)

from cognit.models._serverless_runtime_client import (
    ExecReturnCode
)

from locust import HttpUser, task, between, events

def sum(a: int, b: int):
    return a + b

def func_calling_func(a: int, b: int):
    return sum(a, b)

def cli_test(msg: str):
    import subprocess

    return subprocess.run(["echo", msg], capture_output=True, text=True, shell=True).stdout.strip("\n")

def cli(indicators: str):
    import subprocess

    return subprocess.run(["/opt/smartcity_faas/call_sumo_gr.sh {}".format(indicators)], capture_output=True, text=True, shell=True).stdout.strip("\n")

def remote_call():
    cognit_logger = CognitLogger()
    # Configure the Serverless Runtime requeriments

    cognit_logger.info(">>>>>>>> Initiating remote call")
    sr_conf = ServerlessRuntimeConfig()
    sr_conf.name = "Example Serverless Runtime"
    sr_conf.scheduling_policies = [EnergySchedulingPolicy(50)]
    sr_conf.faas_flavour = "SmartCity"


    # Request the creation of the Serverless Runtime to the COGNIT Provisioning Engine
    try:
        # Set the COGNIT Serverless Runtime instance based on 'cognit.yml' config file
        # (Provisioning Engine address and port...)
        my_cognit_runtime = ServerlessRuntimeContext(config_path="./examples/cognit.yml")
        # Perform the request of generating and assigning a Serverless Runtime to this Serverless Runtime context.
        ret = my_cognit_runtime.create(sr_conf)
    except Exception as e:
        print("Error in config file content: {}".format(e))
        exit(1)


    # Wait until the runtime is ready

    # Checks the status of the request of creating the Serverless Runtime, and sleeps 1 sec if still not available.
    while my_cognit_runtime.status != FaaSState.RUNNING:
        time.sleep(1)

    print("COGNIT Serverless Runtime ready!")

    # Example offloading a function call to the Serverless Runtime

    # call_sync sendsto execute sync.ly to the already assigned Serverless Runtime.
    # First argument is the function, followed by the parameters to execute it.
    junction = random.randint(1001, 1004)
    for i in range(100):
        result = my_cognit_runtime.call_sync(cli, f"Granada {junction} -n CO2 CO NOx")
        cognit_logger.info(f">>>>>>>> result {result}")
        # print(result)
        if result.ret_code == ExecReturnCode.ERROR:
            print(i)
            time.sleep(1)
        else:
            break

    cognit_logger.info(">>>>>>>> Offloaded function result {result.res}")
    # print("Offloaded function result", result)
    # print("\n\033[92mresult.res {}\033[0m\n".format(result.res))

    # This sends a request to delete this COGNIT context.
    if result.ret_code == ExecReturnCode.SUCCESS:
        my_cognit_runtime.delete()
        # print("COGNIT Serverless Runtime deleted!")
        cognit_logger.info("COGNIT Serverless Runtime deleted!")
        return None
    else:
        # RED='\033[0;31m'
        # NC='\033[0m'
        # print(f"\n{RED}COGNIT EXECUTION FAILED{NC}\n")
        cognit_logger.error("COGNIT EXECUTION FAILED")
        return Exception

class UC1_Test(HttpUser):
    wait_time = between(1, 5)

    @task
    def run_faas(self):
        start_time = time.time()
        result = remote_call()
        total_time = (time.time() - start_time) * 1000

        # Record the execution time as a custom event

        events.request.fire(
            request_type="Cognit remote call",
            name="UC1_FAAS",
            response_time=total_time,
            response_length=0,
            exception=result
        )