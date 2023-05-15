import xml.etree.ElementTree as ET
import os

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


numberOfModfiedVehicles = 0

#Remove attributes from vehicles
for trip in root.iter('trip'):
    try:
        trip.attrib.pop('autonomous')
        trip.attrib.pop('ehmi')
        numberOfModfiedVehicles += 1
    except:
        pass

#Add schema annotation
treeRoot.attrib['xmlns:xsi'] = "http://www.w3.org/2001/XMLSchema-instance"

root.write('osm.passenger.trips.xml')

print("Total vehicles modifed: " + str(numberOfModfiedVehicles))

