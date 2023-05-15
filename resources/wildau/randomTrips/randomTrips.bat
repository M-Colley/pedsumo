
python "%SUMO_HOME%\tools\randomTrips.py"  -n ../Netzmodell2.net.xml --seed 42 --fringe-factor 7 -p 1.850 -r osm.passenger.rou.xml -b 53990 -e 61000 --vehicle-class passenger --vclass passenger --prefix veh --min-distance 300 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --allow-fringe.min-length 1000 --lanes  -L -l --validate
