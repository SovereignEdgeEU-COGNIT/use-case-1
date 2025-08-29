# Cognit use case for Smartcities
This repository includes a device client configuration and code to validate and test how to leverage the cognit framework used from a device in the Edge, to make remote FaaS calls running a Sumo(Simulation of Urban MObility - https://eclipse.dev/sumo/) simulation, process the results and send them back to the calling device at the Edge.

This repository contains two main folders, `SmartCity_Faas` and `vm`.

## SmartCity_Faas
Shows the function we are using to call the Cognit framework from a device at the Edge. It is mostly based on the examples provided by the https://github.com/SovereignEdgeEU-COGNIT/device-runtime-py/tree/main/examples repository, from the developers of the device runtime for Cognit. Our code has some minor adaptations needed for our use case. The instructions to execute this code can be found in this link (https://github.com/SovereignEdgeEU-COGNIT/device-runtime-py/blob/main/examples/README.md)  
In this project we have been also doing performance tests, and for this reason we included a class to run performance tests, `class UC1_Test` in the `uc1_workload_gr_test_minimal_offload_sync_Locust.py` file.

Our function expects certain environment vars defined:
* `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: Credentials to access the DaaS. Required.
* `CITY`: City name. Used to compose the path where the SUMO model is stored. Required.
* `JUNCTION`: String with the junction code to simulate. Used to compose the path where the SUMO model is stored. Required
* `FORCE_CONGESTION`: Usually the congestion is a value stored in the DaaS by one process running in Saturno. This envvar is available to force a situation of congestion. Valida values are LOW, MEDIUM, HIGH. Not required
* `CACHE_RESULTS`: When true, the result of the simulation and its context is stored in the DaaS, so that it can be reused without running the simulation, if the context is the same. The context includes values as workday or weekend, season, hourly range, and level of congestion. When false, the precalculated values are not used, everytime there is a request the simulation is run and the resulting value is stored in the DaaS for future use.

## vm folder
The other one, **vm** is the stuff that we need deployed in the Cognit framework images used by the vm instances running the FaaS for our use case.
In the following section we will get into deeper detail about how to install the models to prepare the image:

* Create the folder `/opt/smartcity_faas/vm` in the VM with the serverless runtime.
* copy from this repository the folder `/opt/smartcity_faas/vm` into the serverless VM to the folder `/opt/smartcity_faas/vm`.

When finished, you should create a new image from the OpenNebula VM instance:
* In the Open Nebula management console, go to the VM  you are using and clic on it, got to the Storage tab and press the Action button Saveas, and set a name for the new image.
* Then go to the Templates - VM folder and select the template you are using for your FaaS instance, press Update, go to Storage tab and select the new image you just created, and press the button Update.


## OpenStreetMaps attribution
This repository includes OpenStreetMap data, under the folder vm/model.
Please see this copyright notice https://www.openstreetmap.org/copyright

## Installing the Sumo models in the image
Create the following directory structure in the VM to be used to generate the FAAS image:  
* /opt/smartcity_faas/model
* /opt/smartcity_faas/model/Granada/1001
* /opt/smartcity_faas/model/Granada/1030
* /opt/smartcity_faas/model/Granada/1054

  
Terrassa and Granada are some sample cities included in the model. In addition under Granada we create some junction models 1001, 1030, 1054. Each model is independent from the others.  
When the directory structure is ready, then copy the use-case-1/vm/model content to the /opt/smartcity_faas/model in the image.

## Installing the Sumo tool in the image
As the image is based upon OpenSuse, we are using zypper to deploy the products.
For Sumo, we need to add the corresponding repository:  
`zypper addrepo https://download.opensuse.org/repositories/home:behrisch/15.4/home:behrisch.repo`
And then, install the Sumo tool:  
```
zypper refresh
zypper install sumo
```
And add a new environment variable to the system profile:  
`export SUMO_HOME=/usr/share/sumo`

In addition, the scripts files:
- use-case-1/vm/call_sumo.sh
- use-case-1/vm/parse_emission.py

Need to be copied to the /opt/smartcity_faas folder on the image.

## Remote FaaS calls
In this section, we are detailing how  to make remote calls or the results obtained.  
In the remote call, the following parameters should be provided:
- city: folder corresponding to the city name, currently Terrasa or Granada
- junction: junction code in that city, which is a subfolder under the city folder.
- congestion level: 0.5(low), 1(medium), 2 (high)
- step-length: for low and medium congestion set to 1, for high congestion set to 5 so that the simulation doesn't take too much time

### Results
In this PoC we are using the timeLoss of the busses appearing in the simulation as the KPI returned to the FaaS. The Faas will compare the timeLoss with the pre calculated threshold to determine if the priority should be granted to each request.
