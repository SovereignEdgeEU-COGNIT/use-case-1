# Cognit PoC
Create the following directory structure in the VM to be used to generate the FAAS image:  
* /opt/smartcity_faas/model
* /opt/smartcity_faas/model/Terrassa
* /opt/smartcity_faas/model/Terrassa/output
* /opt/smartcity_faas/model/Granada/1001..1004
* /opt/smartcity_faas/model/Granada/1001..1004/output

## Send files to the cognit serverless VM
rsync -avn examples/* administr4d0r@cognit.preprod.saturnocity.com:~/code/device-runtime-py/examples

## Send models to the Cognig FAAS Virtual machine
export VM_URI=root@2001:67c:22b8:1::c
rsync -avn vm/* [$VM_URI]:/opt/smartcity_faas --exclude README.md

## Calling Sumo
vm/model/call_sumo.sh -n {{ space separated list of indicators }}

