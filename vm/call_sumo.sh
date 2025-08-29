#!/bin/bash
# Parameteres: $1: city
#              $2: junction code
#              $3: scale (i.e. congestion level, standard parameter for SUMO)
#              $4: step-length
cd /opt/smartcity_faas/model/$1/$2

echo  >> std_output.log
echo "#######################################################" >> std_output.log
echo "running call_sumo.sh $@" >> std_output.log
sumo -c osm.sumocfg --scale $3 --step-length $4 --random True  >> std_output.log 2>> std_error.log
cd ../../..
python parse_emission.py "$1" "$2"
