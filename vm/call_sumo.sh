#!/bin/bash

cd /opt/smartcity_faas/model/Terrassa
sumo -c test.sumocfg --emission-output output/my_emission_file.xml > std_output.log 2>std_error.log
cd ../..
python parse_emission.py "$@"
