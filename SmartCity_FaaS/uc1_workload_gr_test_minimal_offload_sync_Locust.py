import time
import examples.uc1_workload_gr_test_minimal_offload_sync_FaaS as faas


from locust import HttpUser, task, between, events
class UC1_Test(HttpUser):
    wait_time = between(1, 5)

    @task
    def run_faas(self):
        start_time = time.time()
        try:
            result = faas.faas_request()
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


