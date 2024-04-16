 #Some library missing to run python files
 sudo zypper install python-xml
 #STEPS
 #map.osm (download from Open Street Maps export)
 # test.net.xml (Converted with sumo tool netconvert)
netconvert --osm-files map.osm -o test.net.xml

#test.rou.xml demand generation with randomtrips.py
python randomTrips.py -n test.net.xml -r test.rou.xml -e 50 -l

#test.sumocfg simulation file (contains test.rou.xml and test.net.xml) generated manually

#Simulations from CLI
#emission
sumo -c test.sumocfg --emission-output my_emission_file.xml

#position dump file
sumo -c test.sumocfg --netstate-dump  my_dump_file.xml


