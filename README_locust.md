# Running locust

## Install locust
pip3 install locust

## Send locust files
rsync -avn locust/* administr4d0r@cognit.preprod.saturnocity.com:~/code/locust --exclude=__pycache__

## Running locust
locust -f ~/code/locust/first_test.py --host https://dummy.com -u 10 -r 1 -t 1m

## Running multiple tests in locust
locust -f /home/user/Files/locustfile1.py, /home/user/Files/locustfile2.py, /home/user/Files/locustfile3.py

or

locust -f ~/code/locust  --host https://dummy.com -u 10 -r 1 -t 1m

## Running remote FAAS calls workloads using locust
(serverless-env) administr4d0r@cognit:~/code/device-runtime-py$ locust -f examples/uc1_workload_gr_test_minimal_offload_sync.py --host https://dummy.com -u 1 -r 1 -t 3m

## Configure Locust as a service
Prepare the file: /etc/systemd/system/locust.service  
```
[Unit]
Description=Locust integration with serverless FAAS

[Service]
User=administr4d0r
WorkingDirectory=/home/administr4d0r/code/device-runtime-py
ExecStart=/home/administr4d0r/code/device-runtime-py/serverless-env/bin/python -m locust -f examples/uc1_workload_gr_test_minimal_offload_sync.py --host https://dummy.com -u 1 -r 1 -t 3m

[Install]
WantedBy=multi-user.target
```

And enable and run the new service:  
```
sudo systemctl daemon-reload
sudo systemctl start locust
```

To check the logs:
`journalctl -u locust.service  -f  |ccze -A`
