from locust import task, between, events, HttpUser
import time
import uc1_faas


class UC1_Test(HttpUser):
    wait_time = between(1, 5)

    @task
    def run_faas(self):
        start_time = time.perf_counter()
        try:
            result = uc1_faas.main()
            # time.sleep(10)
            total_time = (time.perf_counter() - start_time) * 1000
            # Record the execution time as a custom event

            events.request.fire(
                request_type="Cognit remote call",
                name="UC1_FAAS",
                response_time=total_time,
                response_length=0,
                exception=result
            )

        except Exception as e:
            total_time = (time.perf_counter() - start_time) * 1000
            events.request.fire(
                request_type="Cognit remote call",
                name="UC1_FAAS",
                response_time=total_time,
                response_length=0,
                exception=e
            )
            # print(">>> An exception has occured: " + str(e))
            # exit(-1)


