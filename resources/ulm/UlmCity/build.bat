python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml --fringe-factor 1 -p 0.312883 -o osm.pedestrian.trips.xml -e 3600 -r osm.pedestrian.rou.xml --vehicle-class pedestrian --pedestrians --prefix ped --max-distance 2000
python "%SUMO_HOME%\tools\randomTrips.py" -n osm.net.xml --fringe-factor 5 -p 0.556445 -o osm.passenger.trips.xml -e 3600 --vehicle-class passenger --vclass passenger --prefix veh --min-distance 300 --trip-attributes "departLane=\"best\"" --fringe-start-attributes "departSpeed=\"max\"" --allow-fringe.min-length 1000 --lanes --validate
