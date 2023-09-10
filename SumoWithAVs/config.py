#!/usr/bin/env python
import os

sumocfgPath = os.path.join("..", "resources", "testNetwork", "BasicConfig.sumocfg") # default path used for simulation. Has to be .sumocfg.

resultsFolderPath = os.path.join("..", "simulation-results") # path where simulation results are stored. Do not change unnecessarily.

# Add other scenarios to list: [Name of scenario, path to .sumocfg of scenario, path to where tripinfo.xml should be generated]
scenarios = [["Small_Test_Network", os.path.join("..", "resources", "testNetwork", "BasicConfig.sumocfg")],
             ["Ingolstadt", os.path.join("..", "resources", "ingolstadt", "simulation", "24h_sim.sumocfg")],
             ["Ulm", os.path.join("..", "resources", "ulm", "UlmCity", "osm.sumocfg")],
             ["Bologna_small", os.path.join("..", "resources", "bologna", "run.sumocfg")],
             ["Wildau", os.path.join("..", "resources", "wildau", "randomTrips", "output_configuration_randomTrips.sumocfg")],
             ["Monaco", os.path.join("..", "resources", "monaco", "scenario", "most.sumocfg")],
             ["Manhattan", os.path.join("..", "resources", "manhattan", "manhattan.sumocfg")]
             ]


sumo_GuiOn = False  # turns sumo's own gui on or off (True = on)
guiOn = True  # turns configuration gui before the simulation and simulation gui on or off (True = on)
visualization_shown = False  # turns on visual display of statistics during simulation

#multithreading - ONLY set one of the following booleans to True if you use multithreading
multithreading_rerouting_active = False
rerouting_threads = 1
multithreading_routing_active = False
routing_threads = 1

update_delay = 50  # delay after which gui updates data or terminal outputs simulation step
run_sim_until_step = -1  # Specified timestep until the simulation will run. Default should always be -1.
                        # Overwrites last timestep in sumocfg if not -1. Higher timestep may not be supported by scenario.

convert_to_csv_after_sim = True  # automatically converts result folder content to csv after simulation if True

# The following variables decide if the appropriate result file will be written or not (after the simulation)
outputFilesActive = True # If false, turns off all following output files:

statsOutput = True
summaryOutput = True
tripinfoOutput = True
vehroutesOutput = True
personsummaryOutput = True
fullOutput = False
ndumpOutput = False
fcdOutput = False
queueOutput = False
edgedataOutput = False
lanedataOutput = False
lanechangeOutput = False
amitranOutput = False
linkOutput = False
personinfoOutput = False

av_density = 0.5    # density of autonomous vehicles compared to total amount of vehicles: 0 <= av_d <= 1
ehmi_density = 0.2  # density of autonomous vehicles with ehmi compared to density of avs: 0 <= ehmi <= 1

# colors for altered pedestrians, avs and ehmis in sumo gui for visual clarity
default_pedestrian_color = (0, 0, 255, 255)         # blue
altered_pedestrian_color = (255, 255, 255, 255)     # white
av_color = (255, 0, 0, 255)                         # red
ehmi_color = (0, 0, 255, 255)                       # blue

est_walking_speed = 1.0                             # unit in meter / second
driver_reaction_time = 0.5                          # unit in seconds

# dfv = defiance_factor_value
base_automated_vehicle_defiance = 0.4

ehmi_dfv = 1.3                      # pedestrians are more likely to cross when confronted with an ehmi

walking_pedestrian_dfv = 1.2        # momentum encourages more dangerous crossings

group_size_dfv_two_to_three = 1.2   # being in a group increases crossing probability
group_size_dfv_over_three = 1.4

# ttc = time to collision
ttc_lower_extreme_time = 1.0        # time in seconds under which the extreme dfv is used
ttc_lower_bound_time = 3.0          # time in seconds under which the lower bound value is used
ttc_upper_bound_time = 6.0          # time in seconds over which the upper bound value is used
ttc_dfv_under_lower_extreme = 0.01  # dfv for extremely low ttc
ttc_dfv_under_lower_bound = 0.1     # "usually pedestrians do not cross when TTC is below 3s"
ttc_dfv_over_upper_bound = 3.0      # "and very likely cross when it is higher than 7s"
ttc_base_at_lower_bound = 0.2       # values used for linear increase between lower and upper bound
ttc_base_at_upper_bound = 2.0

waiting_time_accepted_value = 28
waiting_time_dfv_under_accepted_value = 1.0   # suggestion: linear increase
waiting_time_dfv_over_accepted_value_increase_per_second = 0.0494

neutral_street_width = 7.0          # germany standard for two lanes (each lane being 3.5m)

child_age = 14                      # up to what age pedestrians define someone as a child
girl_present_dfv = 0.85
boy_present_dfv = 0.9

smombie_dfv = 1.5
smombie_start_age = 8
smombie_peak_age = 16
smombie_end_age = 50
smombie_chance_at_start_age = 0.02  # assumption: linear increase between age 8 and 16
smombie_chance_at_peak_age = 0.1    # with the peak chance at age 16
smombie_chance_at_end_age = 0.01    # and linear decrease between age 16 and 50
smombie_base_chance = 0.01          # base chance for all other ages

# https://www.sciencedirect.com/science/article/abs/pii/S000145752200077X?via%3Dihub
small_vehicle_size = 1.3 * 1.35     # height * width in meters for an ElectraMeccanica Solo
neutral_vehicle_size = 1.4 * 1.8    # height * width in meters for a VW Scirocco 3
large_vehicle_size = 2.0 * 2.0      # height * width in meters for a Hummer H2
small_vehicle_size_dfv = 1.3
neutral_vehicle_size_dfv = 1.0      # linear decrease/increase to large/small size
large_vehicle_size_dfv = 0.7

# https://doi.org/10.1016/j.trf.2009.02.003
lane_low_occupancy_rate = 0.02      # occupancy rate in (length of all vehicles) / (street length)
lane_high_occupancy_rate = 0.1      # e.g.: 0.1 means 10% of the street length is filled with vehicles
low_occupancy_rate_dfv = 1.2
high_occupancy_rate_dfv = 0.8       # linear increase with decreasing occupancy rate (between high and low)

male_gender_dfv = 1.8
female_gender_dfv = 1.0
other_gender_dfv = 1.4

impaired_vision_dfv = 1.2
healthy_vision_dfv = 1.0

gender_dfvs = {"male": male_gender_dfv, "female": female_gender_dfv, "other": other_gender_dfv}
vision_dfvs = {"impaired": impaired_vision_dfv, "healthy": healthy_vision_dfv}

attribute_dict = {}     # existing attributes
                        # ([attribute name, relative occurance, defiance factor], [...], ...)
attribute_dict["gender"] = (["male", 0.475, 1.8], ["female", 0.475, 1.0], ["other", 0.05, 1.4])
attribute_dict["vision"] = (["impaired", 0.02, 1.2], ["healthy", 0.98, 1.0])
# [age, number in population, dfv]
attribute_dict["age"] = ([6, 863000, 0.6], [7, 810000, 0.65], [8, 802000, 0.7], [9, 775000, 0.75],
                         [10, 774000, 0.8], [11, 757000, 0.85], [12, 774000, 0.9], [13, 763000, 0.95],
                         [14, 781000, 1.0], [15, 775000, 1.05], [16, 760000, 1.1], [17, 769000, 1.15],
                         [18, 788000, 1.2], [19, 795000, 1.2], [20, 822000, 1.2], [21, 855000, 1.2],
                         [22, 907000, 1.2], [23, 926000, 1.2], [24, 953000, 1.2], [25, 997000, 1.2],
                         [26, 991000, 1.2], [27, 975000, 1.2], [28, 987000, 1.2], [29, 1014000, 1.2],
                         [30, 1029000, 1.2], [31, 1062000, 1.19], [32, 1153000, 1.18], [33, 1138000, 1.17],
                         [34, 1162000, 1.16], [35, 1136000, 1.15], [36, 1116000, 1.14], [37, 1081000, 1.13],
                         [38, 1072000, 1.12], [39, 1073000, 1.11], [40, 1090000, 1.10], [41, 1079000, 1.09],
                         [42, 1082000, 1.08], [43, 1029000, 1.07], [44, 1013000, 1.06], [45, 1001000, 1.05],
                         [46, 980000, 1.04], [47, 954000, 1.03], [48, 963000, 1.02], [49, 968000, 1.01],
                         [50, 1043000, 1.0], [51, 1141000, 0.99], [52, 1179000, 0.98], [53, 1261000, 0.97],
                         [54, 1315000, 0.96], [55, 1343000, 0.95], [56, 1374000, 0.94], [57, 1372000, 0.93],
                         [58, 1392000, 0.92], [59, 1373000, 0.91], [60, 1323000, 0.9], [61, 1297000, 0.89],
                         [62, 1246000, 0.88], [63, 1203000, 0.87], [64, 1128000, 0.86], [65, 1092000, 0.85],
                         [66, 1053000, 0.84], [67, 1010000, 0.83], [68, 982000, 0.82], [69, 940000, 0.81],
                         [70, 929000, 0.80], [71, 899000, 0.79], [72, 887000, 0.78], [73, 846000, 0.77],
                         [74, 760000, 0.76], [75, 702000, 0.75], [76, 598000, 0.74], [77, 515000, 0.73],
                         [78, 672000, 0.72], [79, 665000, 0.71], [80, 625000, 0.70], [81, 773000, 0.69],
                         [82, 736000, 0.68], [83, 688000, 0.67], [84, 600000, 0.66], [85, 517000, 0.65],
                         [86, 455000, 0.64], [87, 391000, 0.63], [88, 320000, 0.62], [89, 221000, 0.61],
                         [90, 187000, 0.6], [91, 158000, 0.6], [92, 136000, 0.6], [93, 104000, 0.6],
                         [94, 79000, 0.6], [95, 55000, 0.6], [96, 40000, 0.6], [97, 28000, 0.6],
                         [98, 18000, 0.6], [99, 12000, 0.6])
# add more attributes: attribute_dict["attribute_category"] = (["attribute_name", likelihood to be applied, effect on respect for priority], [...])

# do not change these
scenario_dict = {}
for elem in scenarios:
    scenario_dict[elem[0]] = elem[1]


ped_attribute_dict = {} #dictionary with pedestrians and their assigned attributes
avs = set()
ehmi = set()
