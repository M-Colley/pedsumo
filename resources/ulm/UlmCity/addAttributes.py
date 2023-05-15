import xml.etree.ElementTree as ET
import os
import sys
import math

percentageOfTags = int(sys.argv[1])
applyingEHMI = sys.argv[2]

if(percentageOfTags < 0 or percentageOfTags > 100):
    print("Error: An Error occured for argv[1]. You must insert a value in the intervall of [0, 100] for the percentage")
    exit()

if(applyingEHMI != "true" and applyingEHMI != "false"):
    print("Error: An Error occured for argv[2]. You must insert a boolean [true, false] for the appliance of eHMIs")
    exit()

#Load file, script must me in the same directory
file_path = os.path.abspath(os.path.dirname(__file__))

#Get the tree structure
root = ET.parse(file_path + '\\osm.passenger.trips.xml')
treeRoot = root.getroot()

#Count vehicles
numberOfVehicles = 0

for trip in root.iter('trip'):
    numberOfVehicles += 1

print("Total vehicles found: " + str(numberOfVehicles))

numberOfAutonomousVehicles = numberOfVehicles * (percentageOfTags/100)
numberOfAutonomousVehicles = math.floor(numberOfAutonomousVehicles)
numberOfNotAutonomousVehicles = numberOfVehicles - numberOfAutonomousVehicles

AutonomousCount = 1
notAutonomousCount = 1
 
#This forloop checks if the ratio of autonomous or notautonomous cas is lower then the destination ratio
#If based on if the ratio is undersatisfied or oversatisified the loop adds autonomous vehicles
for trip in root.iter('trip'):
    if(AutonomousCount * numberOfNotAutonomousVehicles < notAutonomousCount * numberOfAutonomousVehicles):
        AutonomousCount = AutonomousCount + 1
        trip.attrib['autonomous'] = 'true'
        if(applyingEHMI == 'true'):
            trip.attrib['ehmi'] = applyingEHMI
    else:
        notAutonomousCount = notAutonomousCount + 1
        trip.attrib['autonomous'] = 'false'
        if(applyingEHMI == 'true'):
            trip.attrib['ehmi'] = applyingEHMI

#Add schema annotation
treeRoot.attrib['xmlns:xsi'] = "http://www.w3.org/2001/XMLSchema-instance"

root.write('osm.passenger.trips.xml')

print("Total vehicles modifed: " + str(numberOfVehicles))