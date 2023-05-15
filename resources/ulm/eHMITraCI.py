#!/usr/bin/env python

import os
import sys
import optparse
import xml.etree.ElementTree as ET
import collections
from random import random
import math

# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary  # Checks for the binary in environ vars
import traci


def get_options():
    opt_parser = optparse.OptionParser()
    opt_parser.add_option("--nogui", action="store_true",
                          default=False, help="run the commandline version of sumo")
    options, args = opt_parser.parse_args()
    return options


def create_vehicle_dictionary():
    dict = {}

    # Load file, script must me in the same directory
    file_path = os.path.abspath(os.path.dirname(__file__))

    # Get the tree structure
    # root = ET.parse(file_path + '\\osm.passenger.trips.xml')
    root = ET.parse("UlmCity\\osm.passenger.trips.xml")

    # Generate dictionary
    for trip in root.iter('trip'):
        dict[trip.attrib["id"]] = (trip.attrib["autonomous"], trip.attrib["ehmi"])

    return dict


def create_ped_list():
    list = []

    # Load file, script must me in the same directory
    file_path = os.path.abspath(os.path.dirname(__file__))

    # Get the tree structure
    # root = ET.parse(file_path + '\\osm.passenger.trips.xml')
    root = ET.parse("UlmCity\\osm.pedestrian.trips.xml")

    # Generate dictionary
    for trip in root.iter('person'):
        list.append(trip.attrib["id"])

    return list


# contains TraCI control loop
def run():
    crossings_cases = collections.defaultdict(list)

    print("Preparing crossing cases")  # We need to precalculate the crossing scenarios. Since python is starting a single thread we are not able to compare every vehicle with every pedestrian during runtime.
    for car in autonomousDictionary.items():
        for ped in pedestrianList:
            if car[1][0] == "true":  # If vehicle is autonomous. To check if it hast a eHMI check car[1][1] == "true"
                if random() > 0.5:  # Pedestrian will cross with a chance of 50% if a AV is aproaching
                    crossings_cases[ped].append(car[0])
    print("Finished preparing crossing cases")

    parametrized_vehicles = list()
    parametrized_peds = list()

    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()  # Step ahead in simulation

        people = traci.person.getIDList()  # Retrieve all persons
        vehicle = traci.vehicle.getIDList()  # Retrieve all vehicles

        people = list(set(people) - set(parametrized_peds))  # Only add parameter to new pedestrian
        vehicle = list(set(vehicle) - set(parametrized_vehicles))  # Only add parameter to new vehicles

        for vehicleID in vehicle:
            vehicle_information = autonomousDictionary.get(vehicleID)
            traci.vehicle.setParameter(vehicleID, "autonomous", vehicle_information[0])  # Attach parameters
            traci.vehicle.setParameter(vehicleID, "ehmi", vehicle_information[1])  # Attach parameters
            parametrized_vehicles.append(vehicleID)

        for pedID in people:  # Check the pedestrians that got added in this simulation step
            parametrized_peds.append(pedID)
            string_val = ""
            for vehID in crossings_cases[pedID]:
                string_val += vehID + " "
            traci.person.setParameter(pedID, "junctionModel.ignoreIDs", string_val)  # Add their precalculated foes to the simulation

        '''
        Maybe this is useful code.
        
        #for personID in people:
            #if traci.person.getVehicle(personID) == "":  # Filter out pedestrians
                #pedPos = traci.person.getPosition(personID)
                #for vehicleID in parametrized_vehicles:
                    #vehPos = traci.vehicle.getPosition(vehicleID)
                    #if math.sqrt(math.pow(pedPos[0] - vehPos[0], 2) + math.pow(pedPos[1] - vehPos[1], 2)) < 100: #if distance is lower than 100 meters
                        #traci.person.setParameter(personID, "junctionModel.ignoreIDs", vehicleID)

                #print(traci.person.getParameter("ped2", "junctionModel.ignoreIDs")) #get the Ignore Parameter
                #traci.person.setParameter("ped2", "junctionModel.ignoreIDs", "veh47") # With this line Ped2 is stealing the foe of veh47
                
                --- Information retrieval 
                #print(personID)
                #print(traci.person.getLaneID(personID))
                #print(traci.person.getNextEdge(personID))
                #print(traci.person.getWaitingTime(personID))
                #nextEdge = traci.person.getNextEdge(personID) + "_0"
                #laneID = traci.person.getLaneID(personID)
                #print("PersonID: " + str(traci.edge.getLastStepPersonIDs(traci.person.getNextEdge(personID))));
                #print("Routes" + str(traci.lane.getIDList()))
                #pedPos = traci.person.getPosition("personID")
                #vehPos = traci.vehicle.getPosition("veh47")
                #math.sqrt(math.pow(pedsPos[0] - veh47Pos[0], 2) + math.pow(pedsPos[1] - veh47Pos[1], 2))
                #print("Distance: " + str(math.sqrt(math.pow(pedsPos[0] - veh47Pos[0], 2) + math.pow(pedsPos[1] - veh47Pos[1], 2))))
                
                --- Get the next Edge the problem with this is that the vehicle is already on the crossing when the foe is detected since the simulation can only output the current foe and the last edge.
                --- This leads to the problem that with traci you are not able to find the point in the simulation where a pedestrian should cross the street. Or in other words: You will find out that the ped should steal the foe if its already too late.
                try:
                    foes1 = traci.lane.getFoes(nextEdge, laneID)
                    if len(foes1) != 0:
                        print(f"Foes1 Edge -> Lane: %s" % (foes1,))
                except traci.exceptions.TraCIException as e:
                    print("Foes1: " + str(e))
                try:
                    foes2 = traci.lane.getFoes(laneID, nextEdge)
                    if len(foes2) != 0:
                        print(f"Foes2 Lane -> Edge: %s" % (foes2,))
                except traci.exceptions.TraCIException as e:
                    print("Foes2: " + str(e))
        '''
        step += 1
    traci.close()
    sys.stdout.flush()


# main entry point
if __name__ == "__main__":

    # create vehicle dictionary
    autonomousDictionary = create_vehicle_dictionary()
    # create pedestrian list
    pedestrianList = create_ped_list()

    options = get_options()

    # check binary
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')

    # traci starts sumo as a subprocess and then this script connects and runs
    traci.start([sumoBinary, "-c", "UlmCity\\osm.sumocfg",
                 "--tripinfo-output", "UlmCity\\tripinfo.xml"])
    run()
