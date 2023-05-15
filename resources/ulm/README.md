# sumo-ehmi

SUMO (https://www.eclipse.org/sumo/) -based simulation to investigate effect of eHMI.

## Contents

This repository contains a simulation of the city of Ulm. In the folder UlmCity you can find the two scripts addAttribute.py and removeAttributes.py. With these scripts the percentage of autonomous vehicles can be defined.

The repository can be imported as a Pycharm project.

The simulation with TraCI connection can be started with the eHMITraCI.py script in the main folder.

The simulation allows to set a probability of a crossing event with a vehicle for each pedestrian based on whether that vehicle is autonomous or has an ehmi or not. The corresponding probability can be set in line 72.
If you want an example in the current setting, in simulation step ~90 pedestrian (ped2) meets AV (veh47) and steals the foe with 50% probability.

## Useful Links

Pedestrian Interaction with (Autonomous) Vehicles:
https://github.com/eclipse/sumo/issues/7717

Isssue: Manipulation of jmIgnoreJunctionFoeProb during the runtime in TraCI
https://github.com/eclipse/sumo/issues/10427

Issue: Manipulation of jmIgnoreJunctionFoeProb during the runtime in TraCI
https://github.com/eclipse/sumo/issues/10427
_This will be implemented in SUMO 14.0_

TraCI Documentation:
https://sumo.dlr.de/docs/TraCI.html

TraCI Python Documentation:
https://sumo.dlr.de/pydoc/traci.html

## Compability

The simulation was tested on Windows 10 and SUMO v11, SUMO v12, SUMO v13.
Note that you have to set the Windows PATH manually for SUMO and SUMO GUI.
You will also need a working install of the latest Python version.
