import os
import shutil
import xml.etree.ElementTree as ET
import csv
import argparse
import sys

"""
This script is specifically made to quickly and comfortably convert all xml files in a folder
in the 'simulation-results' directory to csv files. This only works with the xml2csv.py script by SUMO (which is
located in your 'sumo' directory).
This is specifically made for the SumoWithAVs project. When executing this script, you will be asked to insert
the name of a folder located in 'simulation-results'. NAME OF FOLDER CANNOT CONTAIN ANY '(' or ')'.
BEFORE USING THIS SCRIPT, ADJUST pythonPath AND xml2csvPath AS IF YOU WERE USING THE TERMINAL(!!!):
"""

pythonPath = "python3"  # prompt to use Python on your computer in the command line
xml2csvPath = ""  # prompt to use xml2csv.py in your sumo folder on your computer as command line argument
automaticPathAdjust = True  # set to False, if you want the custom xml2csvPath above to count
custom_conversion = ["stats.xml", "most.stats.xml"]  # these will have their own converting process (without xml2csv.py)

###############################################################################
# automatically adjusts xml2csvPath to your operating system
path_set_successful: bool = True
if automaticPathAdjust:
    try:
        xml2csvPath = os.getenv("SUMO_HOME") + str("/tools/xml/xml2csv.py") if sys.platform.startswith("darwin") else str("\\tools\\xml\\xml2csv.py")
    except:
        path_set_successful = False
        print("xml2csvSWA: Could not find system path to SUMO_HOME.")

if not os.path.exists(xml2csvPath):
    path_set_successful = False
    print("xml2csvSWA: Could not find xml2csv.py file.")

if __name__ == "__main__" and path_set_successful:
    exclude_files = []  # these files will be excluded from converting to csv. Example: ['full.xml', 'ndump.xml']
    delete_after_convert = False  # if True, deletes original xml file after converting to cvs
    zip_folder_after_convert = False  # makes zip archive of folder in 'simulation-results after' converting files
    delete_original_folder_after_zip = True  # if True, deletes the folder (only if zip_folder_after_convert is True)

    # Stop here and do not change the following.

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-fn", "--foldername", action="store", dest="fn", default="",
                      help="folder name in simulation-results")

    args = arg_parser.parse_args()

    folderName = ""
    if args.fn == "":
        folderName = input("Enter name of folder in 'simulation-results': ")
    else:
        folderName = args.fn

    folderPath = "../simulation-results/" + folderName

    if not os.path.exists(folderPath):
        print("Not a correct folder name, aborting script. Make sure that the folder is located in 'simulation-results'.")
        exit()

    all_files = os.listdir(folderPath)
    xml_files = list(filter(lambda f: f.endswith('.xml'), all_files))

    if len(xml_files) == 0:
        print("No xml files in folder '" + folderName + "'.")


    # takes a file and converts it to csv using own method instead of xml2csv.py by SUMO (if xml2csv does not format it
    # correctly.
    def convert_to_csv(xml_file):
        if xml_file in ["stats.xml", "most.stats.xml"]: # works with SUMO 1.17
            print("Note: If custom conversion of stats.xml causes errors or does not work properly, "
                  "the simulation most likely ended with errors or SUMO has a new version of the stats.xml file. "
                  "Remove from custom_conversion list in the latter case.")
            stats_path = folderPath + "/" + xml_file
            tree = ET.parse(stats_path)
            root = tree.getroot()

            stats_row = [root[0].attrib.get('clockBegin'), root[0].attrib.get('clockEnd'), root[0].attrib.get('clockDuration'),
                        root[0].attrib.get('traciDuration'), root[0].attrib.get('realTimeFactor'), root[0].attrib.get('vehicleUpdatesPerSecond'),
                        root[0].attrib.get('personUpdatesPerSecond'), root[0].attrib.get('begin'), root[0].attrib.get('end'),
                        root[0].attrib.get('duration'),
                        root[1].attrib.get('inserted'), root[1].attrib.get('loaded'), root[1].attrib.get('running'), root[1].attrib.get('waiting'),
                        root[2].attrib.get('jam'), root[2].attrib.get('total'), root[2].attrib.get('wrongLane'), root[2].attrib.get('yield'),
                        root[3].attrib.get('collisions'), root[3].attrib.get('emergencyStops'),
                        root[4].attrib.get('jammed'), root[4].attrib.get('loaded'), root[4].attrib.get('running'),
                        root[5].attrib.get('abortWait'), root[5].attrib.get('total'), root[5].attrib.get('wrongDest'),
                        root[6].attrib.get('count'), root[6].attrib.get('departDelay'), root[6].attrib.get('departDelayWaiting'),
                        root[6].attrib.get('duration'), root[6].attrib.get('routeLength'), root[6].attrib.get('speed'),
                        root[6].attrib.get('timeLoss'), root[6].attrib.get('totalDepartDelay'), root[6].attrib.get('totalTravelTime'),
                        root[6].attrib.get('waitingTime'),
                        root[7].attrib.get('duration'), root[7].attrib.get('number'), root[7].attrib.get('routeLength'),
                        root[7].attrib.get('timeLoss'),
                        root[8].attrib.get('number'), root[9].attrib.get('number')
                        ]

            header = ["vehicles_inserted","vehicles_loaded","vehicles_running","vehicles_waiting","teleports_jam",
                    "teleports_total","teleports_wrongLane","teleports_yield","safety_collisions","safety_emergencyStops",
                    "persons_jammed","persons_loaded","persons_running","personTeleports_abortWait","personTeleports_total",
                    "personTeleports_wrongDest","vehicleTripStatistics_count","vehicleTripStatistics_departDelay",
                    "vehicleTripStatistics_departDelayWaiting","vehicleTripStatistics_duration","vehicleTripStatistics_routeLength",
                    "vehicleTripStatistics_speed","vehicleTripStatistics_timeLoss","vehicleTripStatistics_totalDepartDelay",
                    "vehicleTripStatistics_totalTravelTime","vehicleTripStatistics_waitingTime","pedestrianStatistics_duration",
                    "pedestrianStatistics_number","pedestrianStatistics_routeLength","pedestrianStatistics_timeLoss",
                    "rideStatistics_number","transportStatistics_number"]

            with open(folderPath + "/" + "stats.csv", 'w') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(header)
                writer.writerow(stats_row)


    for xmlFile in xml_files:
        if xmlFile not in exclude_files:
            print("Converting " + xmlFile + "...")
            path_to_xml_file = folderPath + "/" + xmlFile
            if xmlFile in custom_conversion:
                convert_to_csv(xmlFile)
            else:
                os.system(pythonPath + " " + xml2csvPath + " " + path_to_xml_file)
            if delete_after_convert:
                os.remove(path_to_xml_file)

    print("Finished!")

    if len(exclude_files) != 0:
        print("Files excluded from converting to csv: " + str(exclude_files))

    if delete_after_convert:
        print("Also, deleted all converted xml files.")
    if zip_folder_after_convert:
        shutil.make_archive(folderPath, 'zip', folderPath)
        zip_message = "Made zip archive of '" + folderName + "'."
        if delete_original_folder_after_zip:
            shutil.rmtree(folderPath)
            zip_message += " (And deleted original folder.)"
        print(zip_message)
