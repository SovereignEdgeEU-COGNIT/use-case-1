#!/bin/bash
# Parameteres: $1: junction code
cd /opt/smartcity_faas/model/$1/$2
sumo -c osm.sumocfg --emission-output output/my_emission_file.xml > std_output.log 2>std_error.log
cd ../../..
echo "parameters $@"
python parse_emission_gr.py "$@"
