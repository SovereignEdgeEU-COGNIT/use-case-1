# Cognit use case for Smartcities
This repository includes in it's current state the proof of concept prepared to validate and test how to leverage the cognit framework used from a device in the Edge, to make remote FaaS calls running a Sumo(Simulation of Urban MObility - https://eclipse.dev/sumo/) simulation, process the results and send them back to the calling device at the Edge.

This repository contains two main folders. One of them, **examples**, shows an example about how to call the Cognit framework from a device at the Edge. It is mostly based on the examples provided by the https://github.com/SovereignEdgeEU-COGNIT/device-runtime-py/tree/main/examples repository, from the developers of the device runtime for Cognit. Our code has some minor adaptations needed for our use case. The instructions to execute this code can be found in this link (https://github.com/SovereignEdgeEU-COGNIT/device-runtime-py/blob/main/examples/README.md)
In this PoC we have been also doing some performance tests, and for this reason we included:
- A class to run performance tests, `class UC1_Test` in the `use-case-1/examples/uc1_workload_gr_test_minimal_offload_sync.py` file, and 
- a random selection of junctions between 1001 and 1004 for Granada

The other one, **vm** is the stuff that we need deployed in the Cognit framework images that will be spinned up when a FaaS request is sent to the Coggnit framework.
In the following section we will get into deeper detail about how to install the models to prepare the image.

## Installing the Sumo models in the image
Create the following directory structure in the VM to be used to generate the FAAS image:  
* /opt/smartcity_faas/model
* /opt/smartcity_faas/model/Terrassa
* /opt/smartcity_faas/model/Terrassa/output
* /opt/smartcity_faas/model/Granada/1001..1004
* /opt/smartcity_faas/model/Granada/1001..1004/output
Terrassa and Granada are some sample cities included in the model. In addition under Granada we create some junction models 1001 to 1004. Each model is independent from the others. For the final scope of the project, there will be a bigger set of junctions in the model.
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
- use-case-1/vm/call_sumo_gr.sh
- use-case-1/vm/parse_emission_gr.py

Need to be copied to the /opt/smartcity_faas folder on the image.

## Remote FaaS calls
In this section, we are detailing how  to make remote calls or the results obtained.  
In the remote call, the following parameters should be provided:
- city: folder corresponding to the city name, currently Terrasa or Granada
- junction: junction code in that city, which is a subfolder under the city folder.
- environmental indicators: "-n" followed by a list of environmental indicators, i.e. -n CO2 CO NOx

### Results
In this PoC we are returning the aggregated values from the simulation for the environmental indicators passed as parameters, as a map, where the environmental indicator is the key and the aggregated result as a value.



