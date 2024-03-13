#!/usr/bin/env python
from datetime import datetime
import datetime as dt
import time
import os
import random
import sys
import argparse
import time
import csv
from enum import IntEnum
import config as cf
import xml2csvSWA
# only import if available
import importlib.util
try:
  from transformers import pipeline
except:
  pipeline = None

# we need to import some python modules from the $SUMO_HOME/tools directory
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
from sumolib import checkBinary     # Checks for the binary in environ vars
import traci


results_folder_for_next_sim = ""    # path to created folder for results of next simulation


def get_options():
    """
    Command line options using the argparse library
    """
    default_value = 0.0
    default_step_size = 0.1
    arg_parser = argparse.ArgumentParser()
    loop_group = arg_parser.add_argument_group("loop options")
    arg_parser.add_argument("--nogui", action="store_true", default=False, help="run the commandline version of sumo")
    arg_parser.add_argument("-v", "--verbosity", dest="verbosity", type=str, default="normal",
                            choices=("none", "sparse", "normal", "verbose"),
                            help="verbosity of the command line output. Options are none, sparse, normal (default) and "
                                 "verbose")
    arg_parser.add_argument("--scenario", dest="scenario", type=str,
                            choices=cf.scenario_dict.keys(),
                            help="default = Small_Test_Network. Defines the scenario you want to simulate. "
                                 "Choices are: " + str(list(cf.scenario_dict.keys())))
    arg_parser.add_argument("--scenario_path", dest="scenario_path", type=str,
                            help="Alternative to --scenario: defines the path to the .sumocfg you want to simulate. "
                                 "Value should be an existing path to a valid .sumocfg file.")
    arg_parser.add_argument("--time_steps", dest="time_steps", type=int,
                            help="Defines the amount of seconds simulated, after which the simulation will terminate. "
                                 "Does not equal real time seconds. A value of 3600 would mean that one hour would get "
                                 "simulated.")
    arg_parser.add_argument("--routing-threads", dest="routing_threads", type=str,
                            help="Activates routing multithreading. Needs number of cores to utilize.")
    arg_parser.add_argument("--rerouting-threads", dest="rerouting_threads", type=str,
                            help="Activates rerouting multithreading. Needs number of cores to utilize.")
    loop_group.add_argument("-l", "--loop", action="store_true", dest="loop", default=False,
                            help="run the simulation multiple times in a row, looping through av_density, ehmi_density "
                                 "and base_automated_vehicle_defiance.")
    loop_group.add_argument("--av_step_size", dest="av_step_size", type=float, default=default_step_size,
                            choices=FloatRange(0.0, 1.0),
                            help="default = " + str(default_step_size) + ". Only useful when the --loop option is set. "
                                 "Defines the step size for the density of automated vehicles in the loop. "
                                 "Value should be between 0.0 and 1.0 as float. "
                                 "Setting this value to exactly 0.0 disables looping over av_density instead. ")
    loop_group.add_argument("--ehmi_step_size", dest="ehmi_step_size", type=float, default=default_step_size,
                            choices=FloatRange(0.0, 1.0),
                            help="default = " + str(default_step_size) + ". Only useful when the --loop option is set. "
                                 "Defines the step size for the density of automated vehicles with ehmi in the loop. "
                                 "Value should be between 0.0 and 1.0 as float. "
                                 "Setting this value to exactly 0.0 disables looping over ehmi_density instead. ")
    loop_group.add_argument("--defiance_step_size", dest="defiance_step_size", type=float, default=default_step_size,
                            choices=FloatRange(0.0, 1.0),
                            help="default = " + str(default_step_size) + ". Only useful when the --loop option is set. "
                                 "Defines the step size for the base automated vehicle defiance in the loop."
                                 "Value should be between 0.0 and 1.0 as float."
                                 "Setting this value to exactly 0.0 disables looping over this variable instead.")

    loop_group.add_argument("--density", dest="start_density", type=float, default=default_value,
                            choices=FloatRange(0.0, 1.0),
                            help="default = " + str(default_value) + ". "
                                 "Only useful when combined with the --loop option. Defines the lower bound for the "
                                 "used av_density in the loop. Value should be between 0.0 and 1.0 as float.")
    loop_group.add_argument("--defiance", dest="start_defiance", type=float, default=default_value,
                            choices=FloatRange(0.0, 1.0),
                            help="default = " + str(default_value) + ". "
                                 "Only useful when combined with the --loop option. Defines the lower bound for the "
                                 "used base_automated_vehicle_defiance in the loop. "
                                 "Value should be between 0.0 and 1.0 as float.")
    loop_group.add_argument("--ehmi", dest="start_ehmi", type=float, default=default_value,
                            choices=FloatRange(0.0, 1.0),
                            help="default = " + str(default_value) + ". "
                                 "Only useful when combined with the --loop option."
                                 "Defines the lower bound for the used ehmi_density in the loop."
                                 "Value should be between 0.0 and 1.0 as float.")
    arg_parser.add_argument("--prob_computation", dest="prob_computation", type=str, default="normal", 
                            choices=("normal", "llm"), help="Method to determine the probability for a pedestrian to cross. Options are normal (default) and llm.")
    arg_parser.add_argument("--transformers_model", dest="transformers_model", type=str, default="declare-lab/flan-alpaca-large",
                            help="Allows to specify which transformers model to use. Only relevant if prob_computation is set to llm. "
                            "Attention: Make sure that your hardware supports the model and that the model is supported by the transformers pipeline method.")


    args = arg_parser.parse_args()

    if (args.loop is False) and ((id(args.start_density) != id(default_value))
                                 or (id(args.start_defiance) != id(default_value))
                                 or (id(args.start_ehmi) != id(default_value))
                                 or (id(args.av_step_size) != id(default_step_size))
                                 or (id(args.ehmi_step_size) != id(default_step_size))
                                 or (id(args.defiance_step_size) != id(default_step_size))):
        arg_parser.error("--loop is required when setting loop specific variables such as "
                         "--density, --defiance or --av_step_size")
    return args


class Verbosity(IntEnum):
    NONE = 0
    SPARSE = 1
    NORMAL = 2
    VERBOSE = 3


class FloatRange(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return self.start <= other <= self.end

    def __contains__(self, item):
        return self.__eq__(item)

    def __iter__(self):
        yield self

    def __repr__(self):
        return '[{0},{1}]'.format(self.start, self.end)


def generate_pedestrian_attributes(ped_id: str):
    """
    Generates an entry in the ped_attribute_dict for the given pedestrian.
    This entry is another dictionary, mapping attribute categories to randomly selected attributes.
    The attributes to choose from are defined in the attribute_dict in config.py

    :param ped_id: pedestrian id obtained from traci.person.getIDList()
    """
    ped_dict_entry = {}
    attribute_defiance_factor = 1.0
    # iterate through every attribute category
    for attribute_category in cf.attribute_dict:
        attribute_probabilities = []
        attribute_choices = []
        # add each attribute with its corresponding probability to the list of choices
        for attribute in cf.attribute_dict[attribute_category]:
            attribute_probabilities.append(attribute[1])
            attribute_choices.append(attribute)
            # choose an attribute and add it to the attribute dictionary
        chosen_attribute = random.choices(attribute_choices, attribute_probabilities)
        attribute_defiance_factor *= chosen_attribute[0][2]
        ped_dict_entry[attribute_category] = chosen_attribute[0][0]
    ped_dict_entry["attribute_defiance_factor"] = attribute_defiance_factor
    # add dictionary for pedestrian to the ped_attribute_dict (containing attribute information for all pedestrians)
    cf.ped_attribute_dict[ped_id] = ped_dict_entry


def create_incoming_lanes_dictionary() -> dict[str, set[str]]:
    """
    Creates a dictionary containing a set of all incoming lanes into each unprioritized crossing in the simulation.
    """
    cross_dict = {}
    internal_foes_dict = {}

    # get all lanes
    for lane in traci.lane.getIDList():
        # filter for crossings
        if ("c" in lane) and ("cluster" not in lane):
            internal_foes_dict[lane] = traci.lane.getInternalFoes(lane)
    if verbosity >= Verbosity.VERBOSE:
        print("internal foes dict: " + str(internal_foes_dict))

    # iterate through all lanes
    for lane in traci.lane.getIDList():
        # for each lane get all successors
        for successor_tuple in traci.lane.getLinks(lane):
            # filter for unprioritized crossings only
            if successor_tuple[5] == 'M':
                internal_successor = successor_tuple[4]
                if internal_successor != '':
                    # look if successor is an internal foe of a crossing
                    for crossing in internal_foes_dict:
                        if internal_successor in internal_foes_dict.get(crossing):
                            # add original lane to value set of the crossing
                            cross_dict.setdefault(crossing, set()).add(lane)

    return cross_dict


def adjust_newly_added_entities(vehicles: set[str], last_step_vehicles: set[str], avs: set[str], ehmi: set[str],
                                pedestrians: set[str], last_step_pedestrians: set[str]):
    """
    Randomly declares vehicles added in the current simulation step as either av, av with ehmi or normal.
    Dependent on av_density and ehmi_density defined in config.py
    Also generates custom attributes to each newly added pedestrian.

    :param vehicles: set of all vehicles existing in the current step of the simulation
    :param last_step_vehicles: set of all vehicles existing in the prior simulation step
    :param avs: set of all vehicles declared as avs
    :param ehmi: set of all vehicles declared as ehmi
    :param pedestrians: set of all pedestrians existing in the current step of the simulation
    :param last_step_pedestrians: set of all pedestrians existing in the prior simulation step
    """
    # iterate through vehicles added in current step
    for new_vehicle in (set(vehicles) - last_step_vehicles):
        # with a chance of <av_density>, "mark" vehicle as av
        if random.random() <= av_density:
            avs.add(new_vehicle)
            # with a chance of <ehmi_density>, additionally "mark" vehicle as ehmi
            if random.random() <= ehmi_density:
                ehmi.add(new_vehicle)
                traci.vehicle.setColor(new_vehicle, cf.ehmi_color)
            else:
                traci.vehicle.setColor(new_vehicle, cf.av_color)

    # iterate through pedestrians added in current step
    for new_pedestrian in (set(pedestrians) - last_step_pedestrians):
        generate_pedestrian_attributes(new_pedestrian)


def find_pedestrians_about_to_enter_unprioritized_crossing(pedestrians: set[str], waiting_pedestrians: dict[str, int],
                                                           crossing_waiting_dict: dict[str, set[str]]):
    """
    Finds all pedestrians whose next edge is an unprioritized crossing and adds them to the crossing_waiting_dict:
    A dictionary mapping each crossing with waiting pedestrians to a set of the pedestrian IDs of those pedestrians.
    Additionally, adds found pedestrians to the waiting_pedestrians dictionary, mapping the pedestrian ID to their
    respective waiting time at their current crossing. Initialized with a waiting time of 0.

    :param pedestrians: set of all pedestrians existing in the current step of the simulation
    :param waiting_pedestrians: dictionary mapping pedestrian ID to their waiting time
    :param crossing_waiting_dict: dictionary mapping crossings to a set of the waiting pedestrian's IDs
    """
    # loop through all pedestrians not known to be about to cross
    not_waiting_pedestrians = set(pedestrians) - set(waiting_pedestrians.keys())
    for pedestrian in not_waiting_pedestrians:
        # filters for pedestrians about to enter a crossing
        next_edge = traci.person.getNextEdge(pedestrian)
        if next_edge + "_0" in crossing_dict:
            crossing_waiting_dict.setdefault(next_edge, set()).add(pedestrian)
            waiting_pedestrians[pedestrian] = 0


def reset_crossed_pedestrians(waiting_pedestrians: dict[str, int], crossing_waiting_dict: dict[str, set[str]]):
    """
    Looks through waiting_pedestrians for pedestrians no longer about to enter an unprioritized crossing and
    removes them from waiting_pedestrians and crossing_waiting_dict.
    Additionally, resets changes made to those pedestrians.

    :param waiting_pedestrians: dictionary mapping pedestrian ID to their waiting time
    :param crossing_waiting_dict: dictionary mapping crossings to a set of the waiting pedestrian's IDs
    """
    for pedestrian in waiting_pedestrians.copy():
        # if pedestrian is no longer about to enter crossing
        next_edge = traci.person.getNextEdge(pedestrian)
        if next_edge + "_0" not in crossing_dict:
            # remove said pedestrian from all waiting lists
            del(waiting_pedestrians[pedestrian])
            for crossing in crossing_waiting_dict:
                if pedestrian in crossing_waiting_dict[crossing]:
                    crossing_waiting_dict[crossing].remove(pedestrian)
            # reset changed attributes
            traci.person.setColor(pedestrian, cf.default_pedestrian_color)
            traci.person.setParameter(pedestrian, "junctionModel.ignoreTypes", "")


def increment_pedestrian_waiting_time(waiting_pedestrians: dict[str, int]):
    """
    Increments waiting time for each waiting pedestrian by 1.

    :param waiting_pedestrians: dictionary mapping pedestrian ID to their waiting time
    """
    for pedestrian in waiting_pedestrians:
        waiting_pedestrians[pedestrian] += 1


def get_general_defiance_factors(crossing_waiting_dict: dict[str, set[str]], crossing: str, closest_vehicle_total: str,
                                 lowest_ttc_total: float, group_size: int, ehmi: set[str], incoming_lanes: set[str]) \
        -> dict[str, float]:
    """
    Calculates all general defiance factors applicable to every pedestrian waiting at the same crossing and returns
    them in a dictionary.

    :param crossing_waiting_dict: dictionary mapping crossings to a set of the waiting pedestrian's IDs
    :param crossing: string ID of the current crossing
    :param closest_vehicle_total: string ID of the closest vehicle to the crossing across all incoming lanes
    :param lowest_ttc_total: lowest time to collision of every approaching vehicle
    :param group_size: number of waiting pedestrians at the current crossing
    :param ehmi: set of all vehicles declared as ehmi
    :param incoming_lanes: set of all incoming lanes into the crossing
    """
    group_size_defiance_factor = get_group_size_defiance_factor(group_size)
    ttc_defiance_factor = get_time_to_collision_defiance_factor(lowest_ttc_total)
    ehmi_defiance_factor = get_ehmi_defiance_factor(closest_vehicle_total, ehmi)
    street_width_defiance_factor = get_street_width_defiance_factor(crossing)
    child_present_defiance_factor = get_child_present_defiance_factor(crossing_waiting_dict[crossing])
    vehicle_size_defiance_factor = get_vehicle_size_defiance_factor(closest_vehicle_total)
    occupancy_rate_defiance_factor = get_road_occupancy_defiance_factor(incoming_lanes)

    return {"group_size_defiance_factor": group_size_defiance_factor,
            "ttc_defiance_factor": ttc_defiance_factor,
            "ehmi_defiance_factor": ehmi_defiance_factor,
            "street_width_defiance_factor": street_width_defiance_factor,
            "child_present_defiance_factor": child_present_defiance_factor,
            "vehicle_size_defiance_factor": vehicle_size_defiance_factor,
            "occupancy_rate_defiance_factor": occupancy_rate_defiance_factor
            }


def get_individual_defiance_factors(pedestrian: str, waiting_pedestrians: dict[str, int]) -> dict[str, float]:
    """
    Calculates all defiance factors that are individual to each pedestrian and returns them in a dictionary.

    :param pedestrian: string ID of the current pedestrian
    :param waiting_pedestrians: dictionary mapping pedestrian ID to their waiting time
    """
    ped_speed_defiance_factor = get_ped_speed_defiance_factor(pedestrian)
    smombie_defiance_factor = get_smombie_defiance_factor(pedestrian)
    waiting_time_defiance_factor = get_waiting_time_defiance_factor(waiting_pedestrians[pedestrian])

    return {"ped_speed_defiance_factor": ped_speed_defiance_factor,
            "smombie_defiance_factor": smombie_defiance_factor,
            "waiting_time_defiance_factor": waiting_time_defiance_factor,
            "attribute_defiance_factor": cf.ped_attribute_dict[pedestrian]["attribute_defiance_factor"]}


def get_waiting_time_defiance_factor(waiting_time: int) -> float:
    """
    Calculates and returns the waiting time defiance factor for the given waiting time.
    Data taken from https://ieeexplore.ieee.org/document/5625157

    :param waiting_time: amount of time in seconds the pedestrian is waiting at the crossing
    """
    if waiting_time <= cf.waiting_time_accepted_value:
        return cf.waiting_time_dfv_under_accepted_value
    else:
        return 1.0 + (waiting_time - cf.waiting_time_accepted_value) \
               * cf.waiting_time_dfv_over_accepted_value_increase_per_second


def get_smombie_defiance_factor(pedestrian: str) -> float:
    """
    Dependent on age, randomly decides whether a pedestrian is distracted by a smartphone or not.
    If a pedestrian is deemed as distracted, this function returns the smombie defiance factor.

    :param pedestrian: string ID of the current pedestrian
    """
    pedestrian_age = cf.ped_attribute_dict[pedestrian]["age"]
    distraction_chance = cf.smombie_base_chance
    # pedestrian age between start and peak age -> linear increase in chance with growing age
    if cf.smombie_start_age <= pedestrian_age <= cf.smombie_peak_age:
        distraction_chance = cf.smombie_chance_at_start_age + (pedestrian_age - cf.smombie_start_age) \
                             * (cf.smombie_chance_at_peak_age - cf.smombie_chance_at_start_age) \
                             / (cf.smombie_peak_age - cf.smombie_start_age)
    # pedestrian age between peak and end age -> linear decrease in chance with growing age
    elif cf.smombie_peak_age <= pedestrian_age <= cf.smombie_end_age:
        distraction_chance = cf.smombie_chance_at_peak_age - (pedestrian_age - cf.smombie_peak_age) \
                             * (cf.smombie_chance_at_peak_age - cf.smombie_chance_at_end_age) \
                             / (cf.smombie_end_age - cf.smombie_peak_age)
    if random.random() <= distraction_chance:   # pedestrian is distracted with smartphone
        return cf.smombie_dfv
    else:                                       # pedestrian isn't distracted
        return 1.0


def get_child_present_defiance_factor(present_pedestrians: set[str]) -> float:
    """
    Calculates and returns the defiance factor for a child being present at the crossing.
    Data taken from http://eprints.lincoln.ac.uk/id/eprint/3790/2/Pfeffer_Fagbemi_Stennet_corrected_preprint_copy.pdf

    :param present_pedestrians: set of pedestrian string IDs of pedestrians waiting at the crossing
    """
    for pedestrian in present_pedestrians:
        # if pedestrian is a child according to the age specified in config.py
        if cf.ped_attribute_dict[pedestrian]["age"] <= cf.child_age:
            # child is male
            if cf.ped_attribute_dict[pedestrian]["gender"] == "male":
                return cf.boy_present_dfv
            # child is female
            elif cf.ped_attribute_dict[pedestrian]["gender"] == "female":
                return cf.girl_present_dfv
            else:   # child is neither male nor female
                return (cf.boy_present_dfv + cf.girl_present_dfv) / 2
    return 1.0      # no child present


def get_ehmi_defiance_factor(closest_vehicle_total: str, ehmi: set[str]) -> float:
    """
    Checks if the closest vehicle to the crossing has an ehmi equipped.
    Returns the ehmi defiance factor accordingly.
    Inspired by https://dl.acm.org/doi/fullHtml/10.1145/3491102.3517571

    :param closest_vehicle_total: vehicle string ID of the closest vehicle to the crossing
    :param ehmi: set of all vehicles declared as ehmi
    """

    if closest_vehicle_total == "":
        return 1.0
    else:
        if closest_vehicle_total in ehmi:
            return cf.ehmi_dfv
        else:
            return 1.0


def get_ped_speed_defiance_factor(pedestrian: str) -> float:
    """
    Returns the walking pedestrian defiance factor as defined in config.py if the given pedestrian is currently moving.

    :param pedestrian: string ID of the current pedestrian
    """
    ped_speed = traci.person.getSpeed(pedestrian)
    if ped_speed > 0.6:     # pedestrian is still walking
        return cf.walking_pedestrian_dfv
    else:
        return 1.0


def get_street_width_defiance_factor(crossing: str) -> float:
    """
    Calculates the street width at the given crossing and compares it to the configured neutral street width.
    Returns the street width defiance factor. Increasing with narrower streets, decreasing with wider streets.
    Inspired by https://ieeexplore.ieee.org/abstract/document/8667866

    :param crossing: string ID of the current crossing
    """
    crossing_length = traci.lane.getLength(crossing + "_0")
    width_factor_to_neutral = crossing_length / cf.neutral_street_width     # in germany most streets are 3.5m wide
    return 1 / width_factor_to_neutral                                      # 3.5m -> 2.0   14m -> 0.5


def get_vehicle_size_defiance_factor(closest_vehicle: str) -> float:
    """
    Calculates the front area of the closest approaching vehicle and compares it to the configured expected vehicle
    sizes (small, neutral and large). Returns the vehicle size defiance factor, increasing with the approaching
    vehicle being smaller than the configured neutral vehicle size and decreasing with larger vehicles.
    Inspired by https://www.sciencedirect.com/science/article/abs/pii/S000145752200077X?via%3Dihub

    :param closest_vehicle: vehicle string ID of the closest vehicle to the crossing
    """
    vehicle_front_area = traci.vehicle.getWidth(closest_vehicle) * traci.vehicle.getHeight(closest_vehicle)
    area_difference_to_neutral = abs((cf.neutral_vehicle_size - vehicle_front_area))
    if vehicle_front_area < cf.neutral_vehicle_size:                        # vehicle is smaller than neutral
        if vehicle_front_area <= cf.small_vehicle_size:                     # vehicle is smaller than small vehicles
            return cf.small_vehicle_size_dfv
        else:                                                               # vehicle is between small and neutral
            return cf.neutral_vehicle_size_dfv + area_difference_to_neutral \
                   * (cf.small_vehicle_size_dfv - cf.neutral_vehicle_size_dfv) \
                   / abs((cf.neutral_vehicle_size - cf.small_vehicle_size))
    elif vehicle_front_area > cf.neutral_vehicle_size:                      # vehicle is larger than neutral
        if vehicle_front_area >= cf.large_vehicle_size:                     # vehicle is larger than large vehicles
            return cf.large_vehicle_size_dfv
        else:                                                               # vehicle is between neutral and large
            return cf.neutral_vehicle_size_dfv - area_difference_to_neutral \
                   * (cf.large_vehicle_size_dfv - cf.neutral_vehicle_size_dfv) \
                   / abs((cf.neutral_vehicle_size - cf.large_vehicle_size))
    else:                                                                   # vehicle size is exactly neutral
        return cf.neutral_vehicle_size_dfv


def get_road_occupancy_defiance_factor(incoming_lanes: set[str]) -> float:
    """
    Calculates the average vehicle occupancy rate of all incoming lanes into the crossing.
    By comparing that value to the configured expected occupancy rates and defined in config.py and assuming linear
    increase and decrease, the road occupancy defiance factor is calculated and returned.

    :param incoming_lanes: set of string IDs of all incoming lanes
    """
    sum_of_occupancy_rates = 0.0
    for incoming_lane in incoming_lanes:
        sum_of_occupancy_rates += traci.lane.getLastStepOccupancy(incoming_lane)
    avg_occupancy_rate = sum_of_occupancy_rates / len(incoming_lanes)
    if avg_occupancy_rate <= cf.lane_low_occupancy_rate:                    # occupancy rate low
        return cf.low_occupancy_rate_dfv
    elif avg_occupancy_rate >= cf.lane_high_occupancy_rate:                 # occupancy rate high
        return cf.high_occupancy_rate_dfv
    else:                                                                   # occupancy rate between low and high
        return cf.high_occupancy_rate_dfv + (avg_occupancy_rate - cf.lane_low_occupancy_rate) \
               * (cf.low_occupancy_rate_dfv - cf.high_occupancy_rate_dfv) \
               / (cf.lane_high_occupancy_rate - cf.lane_low_occupancy_rate)


def get_group_size_defiance_factor(group_size: int) -> float:
    """
    Calculates and return the group size defiance factor dependent on the amount of pedestrians currently waiting to
    cross the crossing.
    Ref https://dl.acm.org/doi/pdf/10.1145/3473856.3474004 , https://dl.acm.org/doi/fullHtml/10.1145/3491102.3517571
    and https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=5625157

    :param group_size: amount of pedestrians waiting to cross at the crossing
    """
    if group_size == 1:
        return 1.0
    elif 2 <= group_size <= 3:
        return cf.group_size_dfv_two_to_three
    else:
        return cf.group_size_dfv_over_three


def get_time_to_collision_defiance_factor(lowest_ttc_total: float) -> float:
    """
    Calculates and returns the defiance factor for the time to collision with the closest vehicle.
    Ref https://ieeexplore.ieee.org/abstract/document/8667866 and https://dl.acm.org/doi/pdf/10.1145/3313831.3376197

    :param lowest_ttc_total: lowest time in seconds of all incoming vehicles to reach the crossing
    """

    if lowest_ttc_total <= cf.ttc_lower_extreme_time:   # ttc below lower extreme
        return cf.ttc_dfv_under_lower_extreme
    elif lowest_ttc_total <= cf.ttc_lower_bound_time:   # ttc below lower bound
        return cf.ttc_dfv_under_lower_bound
    elif lowest_ttc_total >= cf.ttc_upper_bound_time:   # ttc above upper bound
        return cf.ttc_dfv_over_upper_bound
    else:                                               # ttc between lower and upper bound
        # increases linearly between lower and upper bound
        return cf.ttc_base_at_lower_bound + (lowest_ttc_total - cf.ttc_lower_bound_time) \
               * ((cf.ttc_base_at_upper_bound - cf.ttc_base_at_lower_bound)
                  / (cf.ttc_upper_bound_time - cf.ttc_lower_bound_time))


def check_for_dangerous_situation(closest_vehicle: str) -> bool:
    """
    Calculates the minimal stopping distance of the given vehicle, assuming the reaction time as configured in
    config.py and the driver breaking with maximum breaking power after said reaction time.
    If this calculated distance is lower than the actual distance to the crossing, we evaluate the current situation
    as dangerous and True is returned. In all other cases False is returned.

    :param closest_vehicle: vehicle string ID of the closest vehicle to the crossing
    """
    speed = traci.vehicle.getSpeed(closest_vehicle)
    reaction_distance = speed * cf.driver_reaction_time
    breaking_distance = pow(speed, 2) / (2 * traci.vehicle.getEmergencyDecel(closest_vehicle))
    stopping_distance = reaction_distance + breaking_distance

    lane = traci.vehicle.getLaneID(closest_vehicle)
    distance_to_crossing = traci.lane.getLength(lane) - traci.vehicle.getLanePosition(closest_vehicle)
    if stopping_distance >= distance_to_crossing:
        return True
    else:
        return False

def generate_prompt_for_crossing_decision(pedestrian: str, waiting_pedestrians: dict[str, int], present_pedestrians: set[str], crossing: str, closest_vehicle: str, group_size: int, lowest_ttc_total: float, ehmi: set[str]) -> str:
    """
    Defines the prompt to send to the model.
    """

    prompt = "You are a pedestrian. You are standing at a street with some automated vehicles trying to decide whether you will cross it. " 
	
	
    prompt_age = "You are " +  str(cf.ped_attribute_dict[pedestrian]["age"]) + " years old. "
    prompt_gender = "You are " +  str(cf.ped_attribute_dict[pedestrian]["gender"]) + ". "
    prompt_waiting_time = "You have been waiting for " + str(round(waiting_pedestrians[pedestrian], 4)) + " seconds. "
	
    isDistracted = True if random.random() <= cf.smombie_base_chance else False
    if isDistracted:
        prompt_distracted = "You are distracted by your smartphone. "
    else:
        prompt_distracted = "You are not distracted by your smartphone. "

    if get_child_present_defiance_factor(present_pedestrians) == 1.0:
        prompt_child_present = "There are no children in your vicinity. "
    else:
        prompt_child_present = "There are children in your vicinity. "
		
		
    if get_ehmi_defiance_factor(closest_vehicle, ehmi) == 1.0:
        prompt_ehmi = "The approaching automated vehicle has an interface attached that communicates with you. "
    else:
        prompt_ehmi = "The approaching automated vehicle does not have an interface attached that communicates with you. "
	
    if get_ped_speed_defiance_factor(pedestrian) == 1.0:
        prompt_walking = "You are not walking. "
    else:
        prompt_walking = "You are walking. "
	
	
    prompt_street_width = "The street is " + str(round(traci.lane.getLength(crossing + "_0"), 4)) + " meters wide. "
    prompt_vehicle_size= "The vehicle has a front area of " + str(traci.vehicle.getWidth(closest_vehicle) * traci.vehicle.getHeight(closest_vehicle)) + " square meter. "
    prompt_group_size = "You are in a group of " + str(group_size) + " people. "
    prompt_ttc = "The time until the vehicle is where you are is approximately " + str(round(lowest_ttc_total, 4)) + " seconds. "

    prompt_instruction = "Instruction: Determine the hypothetical probability for you to cross in this scenario. Give a numeric value in the range of 0.0 (not going to cross at all) to 1.0 (definitely crossing). Your answer MUST be a single numerical value, no text. Only provide the first five digits. Do NOT add text."

    combined_prompt = prompt + prompt_age + prompt_gender + prompt_waiting_time + prompt_distracted + prompt_child_present + prompt_ehmi + prompt_walking + prompt_street_width + prompt_vehicle_size + prompt_group_size + prompt_ttc + prompt_instruction

    return combined_prompt


# contains TraCI control loop
def run():
    step = 0
    crossing_waiting_dict = {}
    last_step_vehicles = set()
    last_step_pedestrians = set()
    waiting_pedestrians = {}
    avs = set()
    ehmi = set()

    if options.prob_computation == "llm":  
        print("LLM is used for computation of probabilities to cross")
        print("The chosen LLM model is: " +options.transformers_model)
        # load model only if that method is chosen
        # potential choices: declare-lab/flan-alpaca-xl, declare-lab/flan-alpaca-gpt4-xl
        transformers_spec = importlib.util.find_spec("transformers")
        found_transformers = transformers_spec is not None
        model = pipeline(model=options.transformers_model, device=0)
        
    random.seed(42)

    global results_folder_for_next_sim
    #probabilities_file = open(results_folder_for_next_sim + '/probabilities-' + results_folder_for_next_sim.rsplit('/', 1)[-1] + '.csv', 'w', newline='')
    # this replaces platform-dependent variant above
    file_name = "probabilities-{}.csv".format(os.path.basename(results_folder_for_next_sim))
    file_path = os.path.join(results_folder_for_next_sim, file_name)
    probabilities_file = open(file_path, 'w', newline='')

    probabilities_writer = csv.writer(probabilities_file, delimiter=';')
    probabilities_header = ['timestamp', 'step', 'scenario', 'pedestrianID', 'crossingID', 'final_crossing_probability',
                            'effective_final_crossing_probability', 'crossing_decision', 'dangerous_situation',
                            'waiting_time', 'pedestrian_location_x', 'pedestrian_location_y',
                            'closest_vehicle_location_x', 'closest_vehicle_location_y', 'av_density', 'ehmi_density',
                            'base_automated_vehicle_defiance', 'driver_reaction_time', 'group_size_dfv_two_to_three',
                            'group_size_dfv_over_three', 'ehmi_dfv', 'ttc_lower_extreme_time', 'ttc_lower_bound_time',
                            'ttc_upper_bound_time', 'ttc_dfv_under_lower_extreme', 'ttc_dfv_under_lower_bound',
                            'ttc_dfv_over_upper_bound', 'ttc_base_at_lower_bound', 'ttc_base_at_upper_bound',
                            'waiting_time_dfv_under_twenty_eight',
                            'waiting_time_dfv_over_twenty_eight_increase_per_second', 'neutral_street_width',
                            'girl_present_dfv', 'boy_present_dfv', 'child_age', 'smombie_dfv', 'smombie_start_age',
                            'smombie_peak_age', 'smombie_end_age', 'smombie_chance_at_start_age',
                            'smombie_chance_at_peak_age', 'smombie_chance_at_end_age', 'smombie_base_chance',
                            'small_vehicle_size', 'neutral_vehicle_size', 'large_vehicle_size',
                            'small_vehicle_size_dfv', 'neutral_vehicle_size_dfv', 'large_vehicle_size_dfv',
                            'lane_low_occupancy_rate', 'lane_high_occupancy_rate', 'low_occupancy_rate_dfv',
                            'high_occupancy_rate_dfv', 'gender', 'gender_dfv', 'vision', 'vision_dfv', 'age', 'age_dfv',
                            'group_size_defiance_factor', 'ttc_defiance_factor', 'ehmi_defiance_factor',
                            'street_width_defiance_factor', 'child_present_defiance_factor',
                            'vehicle_size_defiance_factor', 'occupancy_rate_defiance_factor',
                            'ped_speed_defiance_factor', 'smombie_defiance_factor', 'waiting_time_defiance_factor',
                            'attribute_defiance_factor', 'probability_estimation_method']
    probabilities_writer.writerow(probabilities_header)

    sim_start_time = time.perf_counter()

    crossing_incidents = 0

    while traci.simulation.getTime() <= cf.run_sim_until_step:      # start of the main simulation loop

        if cf.guiOn:
            if check_gui():
                break
            update_general_numbers(len(avs), len(ehmi))

        traci.simulationStep()  # Step ahead in simulation

        if not cf.guiOn and traci.simulation.getTime() % cf.update_delay == 0 and verbosity >= Verbosity.NORMAL:
            print("-----------------------------------------------")
            print("Simulation step: " + str(step + 1))

        vehicles = traci.vehicle.getIDList()                        # list of all vehicles currently simulated
        pedestrians = traci.person.getIDList()                      # list of all pedestrians currently simulated

        increment_pedestrian_waiting_time(waiting_pedestrians)

        # determine terminated vehicles and pedestrians
        terminated_vehicles = last_step_vehicles - set(vehicles)
        terminated_pedestrians = last_step_pedestrians - set(pedestrians)

        # remove pedestrians that left the simulation from ped_attribute_dict
        for terminated_pedestrian in terminated_pedestrians:
            del cf.ped_attribute_dict[terminated_pedestrian]

        # remove vehicles that left the simulation from avs and ehmi
        avs = avs - terminated_vehicles
        ehmi = ehmi - terminated_vehicles

        adjust_newly_added_entities(vehicles, last_step_vehicles, avs, ehmi, pedestrians, last_step_pedestrians)

        find_pedestrians_about_to_enter_unprioritized_crossing(pedestrians, waiting_pedestrians, crossing_waiting_dict)

        # iterate through each unprioritized crossing with pedestrians about to cross
        for crossing in crossing_waiting_dict:
            closest_vehicles_dict = {}      # dict with entries for vehID, distance and ttc for each lane
            closest_vehicle_total = ""
            lowest_ttc_total = 100          # default generic high number
            av_crossing_scenario = False
            est_time_needed_to_cross = traci.lane.getLength(crossing + "_0") / cf.est_walking_speed
            # iterate through all incoming lanes into crossing
            for incoming_lane in crossing_dict[crossing + "_0"]:
                closest_vehicle = ""
                furthest_distance_from_start_of_lane = 0
                # find vehicle closest to crossing
                for vehicle in traci.lane.getLastStepVehicleIDs(incoming_lane):
                    distance_from_start_of_lane = traci.vehicle.getLanePosition(vehicle)
                    if distance_from_start_of_lane > furthest_distance_from_start_of_lane:
                        furthest_distance_from_start_of_lane = distance_from_start_of_lane
                        closest_vehicle = vehicle
                # add the closest vehicle to dict
                if closest_vehicle != "":
                    distance = traci.lane.getLength(incoming_lane) - furthest_distance_from_start_of_lane
                    if traci.vehicle.getSpeed(closest_vehicle) != 0:
                        ttc = distance / traci.vehicle.getSpeed(closest_vehicle)
                        if ttc < lowest_ttc_total:
                            lowest_ttc_total = ttc
                            closest_vehicle_total = closest_vehicle
                        closest_vehicles_dict[incoming_lane] = {"vehicle": closest_vehicle,
                                                                "distance": distance,
                                                                "ttc": ttc}
                    else:                               # prevent division by 0, car standing still
                        lowest_ttc_total = 10.0
                        closest_vehicle_total = closest_vehicle
                        closest_vehicles_dict[incoming_lane] = {"vehicle": closest_vehicle,
                                                                "distance": distance,
                                                                "ttc": 10.0}    # car standing still -> no collision
                    if verbosity >= Verbosity.VERBOSE:
                        print("current lane: " + str(incoming_lane))
                        print("veh distance in sec: " + str(closest_vehicles_dict[incoming_lane]["ttc"]))
                        print("time needed to cross :" + str(est_time_needed_to_cross))

                    # if pedestrian can't usually cross
                    if closest_vehicles_dict[incoming_lane]["ttc"] < est_time_needed_to_cross:
                        if closest_vehicle in avs:
                            av_crossing_scenario = True
                        else:
                            av_crossing_scenario = False
                            break

            # pedestrian wouldn't cross the street in a normal sumo simulation and the closest vehicle is an av
            if av_crossing_scenario:
                group_size = len(crossing_waiting_dict[crossing])   # number of pedestrians waiting at the crossing
                incoming_lanes = crossing_dict[crossing + "_0"]     # list of relevant lanes

                # general defiance factors only have to be calculated once per crossing, as they are independent of
                # the individual pedestrians wanting to cross
                general_defiance_factors = get_general_defiance_factors(crossing_waiting_dict, crossing,
                                                                        closest_vehicle_total, lowest_ttc_total,
                                                                        group_size, ehmi, incoming_lanes)
                # look at each waiting pedestrian individually
                for pedestrian in crossing_waiting_dict[crossing]:
                    # skip pedestrians that have already decided to cross in an earlier simulation step, but have yet
                    # to step on the crossing itself
                    if traci.person.getColor(pedestrian) == cf.altered_pedestrian_color:
                        continue
                    # calculate all defiance factors individual for the person thinking about crossing the road
                    individual_defiance_factors = get_individual_defiance_factors(pedestrian, waiting_pedestrians)
                    # calculate the probability for the pedestrian to decide to cross the road
                    crossing_probability = -1.0						
                    if options.prob_computation == "normal":
                        crossing_probability = base_automated_vehicle_defiance \
                                           * general_defiance_factors["group_size_defiance_factor"] \
                                           * general_defiance_factors["ttc_defiance_factor"] \
                                           * general_defiance_factors["ehmi_defiance_factor"] \
                                           * general_defiance_factors["street_width_defiance_factor"] \
                                           * general_defiance_factors["child_present_defiance_factor"] \
                                           * general_defiance_factors["vehicle_size_defiance_factor"] \
                                           * general_defiance_factors["occupancy_rate_defiance_factor"] \
                                           * individual_defiance_factors["ped_speed_defiance_factor"] \
                                           * individual_defiance_factors["smombie_defiance_factor"] \
                                           * individual_defiance_factors["waiting_time_defiance_factor"] \
                                           * individual_defiance_factors["attribute_defiance_factor"]
                    elif options.prob_computation == "llm":
                        if not found_transformers:
                            print("You have chosen method llm but transformers is not available, aborting.")
                            sys.exit()
                        combined_prompt = generate_prompt_for_crossing_decision(pedestrian, waiting_pedestrians, crossing_waiting_dict[crossing], 
                        crossing, closest_vehicle_total, group_size, lowest_ttc_total, ehmi)
                        print("The combined_prompt is \"" + combined_prompt + "\"")
                        output = model(combined_prompt, max_length=128, do_sample=True)
                        print("The model output is \"" + output[0]['generated_text'] + "\"")
                        try:
                            crossing_probability = float(output[0]['generated_text'])
                        except ValueError:
                            print("LLM did not deliver a float - using traditional method")
                            # TODO duplicate code --> cleanup
                            crossing_probability = base_automated_vehicle_defiance \
                                           * general_defiance_factors["group_size_defiance_factor"] \
                                           * general_defiance_factors["ttc_defiance_factor"] \
                                           * general_defiance_factors["ehmi_defiance_factor"] \
                                           * general_defiance_factors["street_width_defiance_factor"] \
                                           * general_defiance_factors["child_present_defiance_factor"] \
                                           * general_defiance_factors["vehicle_size_defiance_factor"] \
                                           * general_defiance_factors["occupancy_rate_defiance_factor"] \
                                           * individual_defiance_factors["ped_speed_defiance_factor"] \
                                           * individual_defiance_factors["smombie_defiance_factor"] \
                                           * individual_defiance_factors["waiting_time_defiance_factor"] \
                                           * individual_defiance_factors["attribute_defiance_factor"]
                    if verbosity >= Verbosity.NORMAL:
                        print("++++++++++")
                        print("The calculated probability for " + pedestrian
                              + " to cross the crossing " + crossing + " is: "
                              + str(crossing_probability))
                    current_random = random.random()
                    if verbosity >= Verbosity.VERBOSE:
                        print("The dice rolled: " + str(current_random))
                    if current_random <= crossing_probability:
                        crossing_decision = 'cross'
                    else:
                        crossing_decision = 'not_cross'
                    if crossing_probability > 1.0:
                        effective_crossing_probability = 1.0
                    else:
                        effective_crossing_probability = crossing_probability

                    if crossing_decision == "cross":
                        dangerous_situation = check_for_dangerous_situation(closest_vehicle_total)
                    else:
                        dangerous_situation = False

                    try:
                        entry = [datetime.now(), step, scenario, pedestrian, crossing, round(crossing_probability, 4),
                                 round(effective_crossing_probability, 4), crossing_decision, dangerous_situation,
                                 waiting_pedestrians[pedestrian], round(traci.person.getPosition(pedestrian)[0]),
                                 round(traci.person.getPosition(pedestrian)[1]),
                                 round(traci.vehicle.getPosition(closest_vehicle_total)[0]),
                                 round(traci.vehicle.getPosition(closest_vehicle_total)[1]), av_density, ehmi_density,
                                 base_automated_vehicle_defiance, cf.driver_reaction_time,
                                 cf.group_size_dfv_two_to_three, cf.group_size_dfv_over_three, cf.ehmi_dfv,
                                 cf.ttc_lower_extreme_time, cf.ttc_lower_bound_time, cf.ttc_upper_bound_time,
                                 cf.ttc_dfv_under_lower_extreme, cf.ttc_dfv_under_lower_bound,
                                 cf.ttc_dfv_over_upper_bound, cf.ttc_base_at_lower_bound, cf.ttc_base_at_upper_bound,
                                 cf.waiting_time_dfv_under_accepted_value,
                                 cf.waiting_time_dfv_over_accepted_value_increase_per_second, cf.neutral_street_width,
                                 cf.girl_present_dfv, cf.boy_present_dfv, cf.child_age, cf.smombie_dfv,
                                 cf.smombie_start_age, cf.smombie_peak_age, cf.smombie_end_age,
                                 cf.smombie_chance_at_start_age, cf.smombie_chance_at_peak_age,
                                 cf.smombie_chance_at_end_age, cf.smombie_base_chance, cf.small_vehicle_size,
                                 cf.neutral_vehicle_size, cf.large_vehicle_size, cf.small_vehicle_size_dfv,
                                 cf.neutral_vehicle_size_dfv, cf.large_vehicle_size_dfv, cf.lane_low_occupancy_rate,
                                 cf.lane_high_occupancy_rate, cf.low_occupancy_rate_dfv, cf.high_occupancy_rate_dfv,
                                 cf.ped_attribute_dict[pedestrian]["gender"],
                                 cf.gender_dfvs[cf.ped_attribute_dict[pedestrian]["gender"]],
                                 cf.ped_attribute_dict[pedestrian]["vision"],
                                 cf.vision_dfvs[cf.ped_attribute_dict[pedestrian]["vision"]],
                                 cf.ped_attribute_dict[pedestrian]["age"],
                                 cf.attribute_dict["age"][cf.ped_attribute_dict[pedestrian]["age"] - 6][2],
                                 round(general_defiance_factors["group_size_defiance_factor"], 4),
                                 round(general_defiance_factors["ttc_defiance_factor"], 4),
                                 general_defiance_factors["ehmi_defiance_factor"],
                                 round(general_defiance_factors["street_width_defiance_factor"], 4),
                                 general_defiance_factors["child_present_defiance_factor"],
                                 round(general_defiance_factors["vehicle_size_defiance_factor"], 4),
                                 round(general_defiance_factors["occupancy_rate_defiance_factor"], 4),
                                 individual_defiance_factors["ped_speed_defiance_factor"],
                                 individual_defiance_factors["smombie_defiance_factor"],
                                 round(individual_defiance_factors["waiting_time_defiance_factor"], 4),
                                 round(individual_defiance_factors["attribute_defiance_factor"], 4),
                                 options.prob_computation]
                        probabilities_writer.writerow(entry)
                    except:
                        print("Error: probabilities.csv row not written.")

                    # Count up numbers in gui.py
                    crossing_incidents += 1
                    if cf.guiOn:
                        crossed = False
                        if crossing_decision == 'cross':
                            crossed = True
                        #gui.current_crossing_events += 1
                        gui.gndr_check(cf.ped_attribute_dict[pedestrian]["gender"], crossed)
                        gui.vision_check(cf.ped_attribute_dict[pedestrian]["vision"], crossed)
                        gui.age_check(cf.ped_attribute_dict[pedestrian]["age"], crossed)
                        gui.crossing_check(crossing)

                    if current_random <= crossing_probability:
                        if verbosity >= Verbosity.SPARSE:
                            print(pedestrian + " decided to cross " + crossing)
                        if verbosity >= Verbosity.NORMAL:
                            print("They were waiting for: " + str(waiting_pedestrians[pedestrian])
                                  + " seconds to cross.")
                            print("Factors influencing the decision in value:")
                            print("Group size: " + str(general_defiance_factors["group_size_defiance_factor"]))
                            print("Time to collision: " + str(general_defiance_factors["ttc_defiance_factor"]))
                            print("Ehmi: " + str(general_defiance_factors["ehmi_defiance_factor"]))
                            print("Street width: " + str(general_defiance_factors["street_width_defiance_factor"]))
                            print("Child present: " + str(general_defiance_factors["child_present_defiance_factor"]))
                            print("Vehicle size: " + str(general_defiance_factors["vehicle_size_defiance_factor"]))
                            print("Road occupancy rate: "
                                  + str(general_defiance_factors["occupancy_rate_defiance_factor"]))
                            print("Walking momentum: " + str(individual_defiance_factors["ped_speed_defiance_factor"]))
                            print("Distracted with smartphone: "
                                  + str(individual_defiance_factors["smombie_defiance_factor"]))
                            print("Waiting time: " + str(waiting_pedestrians[pedestrian]) + " -> "
                                  + str(individual_defiance_factors["waiting_time_defiance_factor"]))
                            print("Total factor from attributes: "
                                  + str(individual_defiance_factors["attribute_defiance_factor"]))
                            print("    Gender: " + str(cf.ped_attribute_dict[pedestrian]["gender"]))
                            print("    Age: " + str(cf.ped_attribute_dict[pedestrian]["age"]))
                            print("    Vision: " + str(cf.ped_attribute_dict[pedestrian]["vision"]))

                        try:
                            traci.person.setColor(pedestrian, cf.altered_pedestrian_color)
                            vehicle_types = traci.vehicletype.getIDList()
                            # make pedestrian ignore all vehicles in the simulation (break traffic rules)
                            traci.person.setParameter(pedestrian, "junctionModel.ignoreTypes", " ".join(vehicle_types))
                        except traci.TraCIException as e:
                            print("something went wrong when trying to change " + pedestrian + ": " + repr(e))
                            crossing_waiting_dict[crossing].remove(pedestrian)
                            break

        reset_crossed_pedestrians(waiting_pedestrians, crossing_waiting_dict)

        last_step_vehicles = set(vehicles)          # save current vehicles for the next simulation step
        last_step_pedestrians = set(pedestrians)    # save current pedestrians for the next simulation step

        step += 1

    sim_end_time = time.perf_counter()
    time_elapsed = int(sim_end_time - sim_start_time)
    print("Simulation " + get_current_simulation_name() + " lasted " + str(dt.timedelta(seconds=time_elapsed)) + " and " + str(crossing_incidents) + " crossing incidents occured.")
    probabilities_file.close()
    end_simulation()


# ends current simulation properly
def end_simulation():
    traci.close()
    if not options.loop:
        cf.run_sim_until_step = -1
    if cf.guiOn:
        gui.close_gui()
    global results_folder_for_next_sim
    if cf.convert_to_csv_after_sim:
        try:
            os_arg = xml2csvSWA.pythonPath + " xml2csvSWA.py -fn " + results_folder_for_next_sim.rsplit('/', 1)[-1]
            os.system(os_arg)
        except:
            print("Converting result folder content to csv failed. You may have to adjust paths in xml2csvSWA.py.")
    results_folder_for_next_sim = ""
    sys.stdout.flush()


def get_current_simulation_name() -> str:
    """
    Gets current name of the simulation by path. If no name is found
    returns empty string.

    """
    for elem in cf.scenarios:
        if elem[1] == cf.sumocfgPath:
            return elem[0]
    return ""


# creates new folder for results in next simulation
def get_new_results_folder():
    #data_output_path = cf.resultsFolderPath + "/" + get_current_simulation_name() + "-avd" + str(cf.av_density) + "-ed" + str(cf.ehmi_density) + "-" + time.strftime("%Y%m%d-%H%M%S")
    #data_output_path = os.path.join(cf.resultsFolderPath,"{}-avd{}-ed{}-{}".format(get_current_simulation_name(), av_density, ehmi_density, time.strftime("%Y%m%d-%H%M%S")))
    data_output_path = os.path.join(cf.resultsFolderPath, "{}-avd{:.3f}-ed{:.3f}-dss{:.3f}-{}".format(get_current_simulation_name(), av_density, ehmi_density, defiance_step_size, time.strftime("%Y%m%d-%H%M%S")))

    if not os.path.exists(data_output_path):
        os.makedirs(data_output_path)
        return data_output_path
    else:
        return ""


def generate_start_config(sumo_binary: str) -> list[str]:
    """
    Appends all start arguments as defined in config.py and their respective file locations to a list of strings.
    This list is then returned and used to start traci with the appropriate start arguments.

    :param sumo_binary: string with information about the binary (sumo or sumo-gui)
    """
    traci_start_config = [sumo_binary, "-c", cf.sumocfgPath]
    if cf.outputFilesActive:
        if cf.statsOutput:
            traci_start_config.append("--statistic-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "stats.xml"))

        if cf.tripinfoOutput:
            traci_start_config.append("--tripinfo-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "tripinfo.xml"))

        if cf.personsummaryOutput:
            traci_start_config.append("--person-summary-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "personsummary.xml"))

        if cf.summaryOutput:
            traci_start_config.append("--summary")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "summary.xml"))

        if cf.vehroutesOutput:
            traci_start_config.append("--vehroute-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "vehroutes.xml"))

        if cf.fcdOutput:
            traci_start_config.append("--fcd-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "fcd.xml"))

        if cf.fullOutput:
            traci_start_config.append("--full-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "full.xml"))

        if cf.queueOutput:
            traci_start_config.append("--queue-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "queue.xml"))

        if cf.edgedataOutput:
            traci_start_config.append("--edgedata-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "edgedata.xml"))

        if cf.lanedataOutput:
            traci_start_config.append("--lanedata-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "lanedata.xml"))

        if cf.lanechangeOutput:
            traci_start_config.append("--lanechange-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "lanechange.xml"))

        if cf.amitranOutput:
            traci_start_config.append("--amitran-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "amitran.xml"))

        if cf.ndumpOutput:
            traci_start_config.append("--ndump")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "ndump.xml"))

        if cf.linkOutput:
            traci_start_config.append("--link-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "link.xml"))

        if cf.personinfoOutput:
            traci_start_config.append("--personinfo-output")
            traci_start_config.append(os.path.join(results_folder_for_next_sim, "personinfo.xml"))

    if cf.multithreading_rerouting_active:
        traci_start_config.append("--device.rerouting.threads")
        traci_start_config.append(str(cf.rerouting_threads))
    elif cf.multithreading_routing_active:
        traci_start_config.append("--routing-threads")
        traci_start_config.append(str(cf.routing_threads))

    traci_start_config.append("--start")
    traci_start_config.append("--quit-on-end")

    return traci_start_config


# runs gui during simulation
def check_gui():
    choice = gui.run_gui()
    match choice:
        case 'closed':
            end_simulation()
            sys.exit()
        case 'stop':
            return True

    gui.current_traci_step = traci.simulation.getTime()


# updates information data for gui during simulation
def update_general_numbers(av_num, ehmi_num):
    if int(traci.simulation.getTime()) % cf.update_delay == 0:
        gui.total_vehicles = traci.vehicle.getIDCount()
        gui.total_pedestrians = len(traci.person.getIDList())
        gui.total_av = av_num
        gui.total_ehmi = ehmi_num


# start cgui
def start_cgui():
    while True:
        choice = gui.run_cgui()
        match choice:
            case 'sim_start':
                init_sim()
            case 'closed':
                sys.exit()
            case 'restart':
                gui.close_cgui()


# initialize simulation
def init_sim():

    if not cf.sumo_GuiOn or options.nogui:
        sumo_binary = checkBinary('sumo')
    else:
        sumo_binary = checkBinary('sumo-gui')

    global scenario

    if options.scenario:
        cf.sumocfgPath = cf.scenario_dict[options.scenario]
        scenario = options.scenario
    else:
        scenario = cf.sumocfgPath

    if options.scenario_path:
        cf.sumocfgPath = options.scenario_path
        scenario = options.scenario_path

    if options.routing_threads and options.rerouting_threads:
        sys.exit("Can only choose either routing or rerouting as multithread options.")

    if options.routing_threads:
        cf.multithreading_routing_active = True
        cf.routing_threads = options.routing_threads
    elif options.rerouting_threads:
        cf.multithreading_rerouting_active = True
        cf.rerouting_threads = options.rerouting_threads

    global av_density
    global ehmi_density
    global defiance_step_size
    global base_automated_vehicle_defiance

    # define relevant parameters depending on the use of the loop parameter
    if options.loop:
        av_density = options.start_density
        base_automated_vehicle_defiance = options.start_defiance
        ehmi_density = options.start_ehmi
        av_step_size = options.av_step_size
        ehmi_step_size = options.ehmi_step_size
        defiance_step_size = options.defiance_step_size
    else:
        av_density = cf.av_density
        ehmi_density = cf.ehmi_density
        defiance_step_size = 0
        base_automated_vehicle_defiance = cf.base_automated_vehicle_defiance

    # create new folder and save path to put results into folder later. If folder with
    # same name exists -> interrupt initialization
    global results_folder_for_next_sim
    results_folder_for_next_sim = get_new_results_folder()
    if results_folder_for_next_sim == "":
        return

    traci_start_config = generate_start_config(sumo_binary)

    traci.start(traci_start_config)

    if cf.run_sim_until_step == -1:
        cf.run_sim_until_step = 3600 # if no last timestep is found anywhere, run until step 3600 if not stopped

    if options.time_steps:
        cf.run_sim_until_step = options.time_steps

    global verbosity
    match options.verbosity:
        case "none":
            verbosity = Verbosity.NONE
        case "sparse":
            verbosity = Verbosity.SPARSE
        case "normal":
            verbosity = Verbosity.NORMAL
        case "verbose":
            verbosity = Verbosity.VERBOSE

    global crossing_dict
    crossing_dict = create_incoming_lanes_dictionary()
    if verbosity >= Verbosity.VERBOSE:
        print("crossing dict: " + str(crossing_dict))


    if options.loop:
        while av_density <= 1.0:
            while ehmi_density <= 1.0:
                while base_automated_vehicle_defiance <= 1.0:
                    if av_density == options.start_density \
                            and base_automated_vehicle_defiance == options.start_defiance \
                            and ehmi_density == options.start_ehmi:
                        run()
                    else:
                        results_folder_for_next_sim = get_new_results_folder()
                        traci_start_config = generate_start_config(sumo_binary)
                        traci.start(traci_start_config)
                        run()
                    if defiance_step_size == 0.0:
                        break
                    base_automated_vehicle_defiance += defiance_step_size
                base_automated_vehicle_defiance = options.start_defiance
                if ehmi_step_size == 0.0:
                    break
                ehmi_density += ehmi_step_size
            ehmi_density = options.start_ehmi
            base_automated_vehicle_defiance = options.start_defiance
            if av_step_size == 0.0:
                break
            av_density += av_step_size
    else:
        run()


def prepare_sim():
    if cf.guiOn and not options.nogui:
        import gui
        start_cgui()
    else:
        init_sim()


# main entry point
if __name__ == "__main__":
    # disable GUI if command line arguments are used
    if len(sys.argv) > 1:
        cf.guiOn = False
        cf.visualization_shown = False

    options = get_options()

    prepare_sim()
