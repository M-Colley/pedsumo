#!/usr/bin/env python
import config as cf
import PySimpleGUI
import matplotlib.pyplot as plt


#############################################
# these are the size parameters for all three GUI windows
cGUI_size_x: int = 800 if sys.platform.startswith("darwin") else 1000
cGUI_size_y: int = 600 if sys.platform.startswith("darwin") else 800

GUI_size_x: int = 500  # default = 500
GUI_size_y: int = 1040  # default = 840

dv_size_x: int = 12  # default = 12
dv_size_y: int = 5  # default = 5

#############################################

cgui = None
gui = None

numeric_error_msg = ""

# variables from config.py that will be added to the cgui to be adjustable there. Must also be included in
# the adjust_config_value function to work.
adjustable_config_values = ["av_density", "ehmi_density", "base_automated_vehicle_defiance",
                            "ehmi_dfv", "group_size_dfv_two_to_three",
                            "group_size_dfv_over_three", "ttc_lower_extreme_time", "ttc_lower_bound_time",
                            "ttc_upper_bound_time", "ttc_dfv_under_lower_extreme", "ttc_dfv_under_lower_bound",
                            "ttc_dfv_over_upper_bound", "ttc_base_at_lower_bound", "ttc_base_at_upper_bound", "waiting_time_accepted_value",
                            "waiting_time_dfv_under_accepted_value", "waiting_time_dfv_over_accepted_value_increase_per_second",
                            "small_vehicle_size", "neutral_vehicle_size", "large_vehicle_size", "small_vehicle_size_dfv",
                            "neutral_vehicle_size_dfv", "large_vehicle_size_dfv", "lane_low_occupancy_rate", "lane_high_occupancy_rate",
                            "low_occupancy_rate_dfv", "high_occupancy_rate_dfv",
                            "child_age", "girl_present_dfv", "boy_present_dfv",
                            "smombie_dfv", "smombie_start_age", "smombie_peak_age", "smombie_end_age",
                            "smombie_chance_at_start_age", "smombie_chance_at_peak_age", "smombie_chance_at_end_age",
                            "smombie_base_chance", "male_gender_dfv", "female_gender_dfv",
                            "other_gender_dfv", "impaired_vision_dfv", "healthy_vision_dfv", "walking_pedestrian_dfv",
                            "est_walking_speed", "neutral_street_width"]

recent_sim_msg = ""  # log message from the most recent sim, displayed in the cgui
current_sim = ""  # current running scenario. "" if simulation inactive.
current_traci_step = 0

current_crossing_events = 0

number_of_people = 0

women_crossed = 0
men_crossed = 0
other_crossed = 0

women_ncrossed = 0
men_ncrossed = 0
other_ncrossed = 0

healthy_vision_crossed = 0
impaired_vision_crossed = 0

healthy_vision_ncrossed = 0
impaired_vision_ncrossed = 0

ages = list()

crossingIDs = list()

total_vehicles = 0
total_pedestrians = 0

total_av = 0
total_ehmi = 0

PySimpleGUI.set_options(font=("Arial Bold", 14))

visualized_file = ""

num_of_loops: int = 0
loop_data: list = [] # saves configuration of each run in a loop
in_loop: bool = False # True if in a simulation loop with several simulations

def gndr_check(gndr: str, crossed: bool) -> None:
    """
    Counts up gender data during simulation for information output on gui.

    :param gndr: the gender of the person ("male" or "female" or "other")
    :param crossed: if person crossed or did not cross
    """

    global men_ncrossed
    global men_crossed
    global women_ncrossed
    global women_crossed
    global other_ncrossed
    global other_crossed
    if gndr == "male":
        if crossed:
            men_crossed += 1
        else:
            men_ncrossed += 1
    elif gndr == "female":
        if crossed:
            women_crossed += 1
        else:
            women_ncrossed += 1
    else:
        if crossed:
            other_crossed += 1
        else:
            other_ncrossed += 1


def vision_check(vis: str, crossed: bool) -> None:
    """
    Counts up vision data during simulation for information output on gui.

    :param vis: visual health of person ("healthy" or "impaired")
    :param crossed: if person crossed or did not cross
    """

    global healthy_vision_ncrossed
    global healthy_vision_crossed
    global impaired_vision_ncrossed
    global impaired_vision_crossed
    if vis == "healthy":
        if crossed:
            healthy_vision_crossed += 1
        else:
            healthy_vision_ncrossed += 1
    else:
        if crossed:
            impaired_vision_crossed += 1
        else:
            impaired_vision_ncrossed += 1


# add age to event list ages
def age_check(age: int, crossed: bool):
    """
    Adds age to event list 'ages'.

    :param age: Age of person.
    :param crossed: If person crossed or did not cross.
    """

    for elem in ages:
        if elem[0] == age:
            if crossed:
                elem[1] += 1
            else:
                elem[2] += 1
            return True

    if crossed:
        ages.append([age, 1, 0])
    else:
        ages.append([age, 0, 1])


def sort_ages() -> None:
    """
    Sorts 'ages' list.
    """

    global ages
    ages.sort(key=lambda x: x[1])


def crossing_check(crossingID):
    """
    Adds crossing event to 'crossingIDs' list.

    :param crossingID: ID of crossing.
    """

    for elem in crossingIDs:
        if elem[0] == crossingID:
            elem[1] += 1
            return True

    crossingIDs.append([crossingID, 1])


def sort_crossingIDs():
    """
    Sorts 'crossingIDs' list.
    """

    global crossingIDs
    crossingIDs.sort(key=lambda x: x[1])


def reset_numbers() -> None:
    """
    Resets numbers back to default that were used as information output during simulation.
    """


    global recent_sim_msg
    recent_sim_msg = ""
    global current_traci_step
    current_traci_step = 0
    global current_crossing_events
    current_crossing_events = 0
    global number_of_people
    number_of_people = 0
    global women_crossed
    women_crossed = 0
    global men_crossed
    men_crossed = 0
    global other_crossed
    other_crossed = 0
    global women_ncrossed
    women_ncrossed = 0
    global men_ncrossed
    men_ncrossed = 0
    global other_ncrossed
    other_ncrossed = 0
    global healthy_vision_crossed
    healthy_vision_crossed = 0
    global impaired_vision_crossed
    impaired_vision_crossed = 0
    global healthy_vision_ncrossed
    healthy_vision_ncrossed = 0
    global impaired_vision_ncrossed
    impaired_vision_ncrossed = 0
    global ages
    ages = list()
    global crossingIDs
    crossingIDs = list()
    global total_pedestrians
    total_pedestrians = 0
    global total_vehicles
    total_vehicles = 0
    global total_av
    total_av = 0
    global total_ehmi
    total_ehmi = 0


def __total_events_text() -> str:
    """
    Returns total events string for simulation gui ( 'crossed_count/not_crossed_count' )
    """

    return str(women_crossed + men_crossed + other_crossed) + "/" + str(women_ncrossed + men_ncrossed + other_ncrossed)


def div(numerator: int, denominator: int) -> int:
    """
    Divides two variables, if divided by 0 -> returns 0

    :param numerator: Numerator.
    :param denominator: Denominator.
    """

    if denominator != 0:
        return round(numerator/denominator, 2)
    else:
        return 0


def __create_crossing_data_array() -> list:
    """
    Returns list with information to display during simulation.
    """

    crossed_total = women_crossed+men_crossed+other_crossed
    ncrossed_total = women_ncrossed+men_ncrossed+other_ncrossed

    return [["Total", crossed_total, ncrossed_total, div(crossed_total, crossed_total + ncrossed_total)],
            ["Men", men_crossed, men_ncrossed, div(men_crossed, men_ncrossed + men_crossed)],
            ["Women", women_crossed, women_ncrossed, div(women_crossed, women_ncrossed + women_crossed)],
            ["Non-binary", other_crossed, other_ncrossed, div(other_crossed, other_ncrossed + other_crossed)],
            ["Healthy Vision", healthy_vision_crossed, healthy_vision_ncrossed, div(healthy_vision_crossed, healthy_vision_ncrossed + healthy_vision_crossed)],
            ["Impaired Vision", impaired_vision_crossed, impaired_vision_ncrossed, div(impaired_vision_crossed, impaired_vision_ncrossed + impaired_vision_crossed)]]


def __create_gui() -> PySimpleGUI.Window:
    """
    Creates GUI to run during the simulation. Do not call this function outside of this file.
    """

    global women_crossed
    global women_ncrossed
    global men_crossed
    global men_ncrossed
    global other_crossed
    global other_ncrossed
    global healthy_vision_crossed
    global healthy_vision_ncrossed
    global impaired_vision_ncrossed
    global impaired_vision_crossed

    reset_numbers()

    timeStep = PySimpleGUI.Text("Timestep: " + str(current_traci_step) + " (Update delay: " + str(cf.update_delay) + " steps)", key='-timestep-')

    total_pedestrians_t = PySimpleGUI.Text("Pedestrians: " + str(total_pedestrians), key='-tp-')
    total_vehicles_t = PySimpleGUI.Text("Vehicles: " + str(total_vehicles) + "  (of which AVs: " + str(total_av) + "/AVs with eHMI: " + str(total_ehmi) + ")", key='-v-')

    global ages
    age_table = PySimpleGUI.Table(values=ages, headings=["Age", "Times crossed", "Times not crossed"],
                                     auto_size_columns=False,
                                     display_row_numbers=False,
                                     justification='center', key='-ags-',
                                     selected_row_colors='red on yellow',
                                     enable_events=False,
                                     expand_x=True,
                                     expand_y=True,
                                     enable_click_events=False)

    # table that shows data about crossings
    global crossingIDs
    crossing_table = PySimpleGUI.Table(values=crossingIDs, headings=["CrossingID", "Event Count"],
                                     auto_size_columns=False,
                                     display_row_numbers=False,
                                     justification='center', key='-cr-',
                                     selected_row_colors='red on yellow',
                                     enable_events=False,
                                     expand_x=True,
                                     expand_y=True,
                                     enable_click_events=False)

    # table that shows data about how many individuals crossed/did not cross
    crossing_data_table = PySimpleGUI.Table(values=__create_crossing_data_array(),
                                            headings=["Category", "Crossed", "Not Crossed", "Ratio (Crossed)"],
                                            auto_size_columns=False,
                                            display_row_numbers=False,
                                            justification='center', key='-cdt-',
                                            selected_row_colors='red on yellow',
                                            enable_events=False,
                                            expand_x=True,
                                            expand_y=True,
                                            enable_click_events=False
                                            )

    guiPauseButton = PySimpleGUI.Button('Pause', button_color='Orange', key='Pause')
    guiStopButton = PySimpleGUI.Button('Stop', button_color='Green')
    guiQuitButton = PySimpleGUI.Button('Quit Application', button_color='Black')

    gui_layout = [[timeStep],
                  [total_pedestrians_t],
                  [total_vehicles_t],
                  [PySimpleGUI.Text()],
                  [crossing_data_table],
                  [age_table],
                  [crossing_table],
                  [PySimpleGUI.Text()],
                  [guiPauseButton, guiStopButton, guiQuitButton],
                  ]

    return PySimpleGUI.Window("Simulating " + current_sim + "|Ends at " + str(cf.run_sim_until_step) +
                              "|Runs left after this: " + str(num_of_loops), gui_layout, size=(GUI_size_x, GUI_size_y), resizable=True)


def __create_cgui() -> PySimpleGUI.Window:
    """
    Creates config GUI to run prior to the simulation.
    """

    choose_scenario_table = list()

    for elem in cf.scenarios:
        choose_scenario_table.append(elem[0])

    cguiScenTable = PySimpleGUI.Table(values=choose_scenario_table, headings=[""],
                                      auto_size_columns=True,
                                      display_row_numbers=False,
                                      justification='center', key='-selectedscen-',
                                      selected_row_colors='red on yellow',
                                      enable_events=True,
                                      expand_x=True,
                                      expand_y=True,
                                      enable_click_events=True,
                                      num_rows=7)

    cguiTableName = PySimpleGUI.Text("Scenarios:")

    cguiStartButton = PySimpleGUI.Button('Start Simulation', button_color='Green', key='ss')
    cguiQuitButton = PySimpleGUI.Button('Quit Application', button_color='Black')

    cguiUpdateDelayText = PySimpleGUI.Text('Gui update delay (increase for better performance)          ')
    cguiUpdateDelayInput = PySimpleGUI.InputText(str(cf.update_delay), key='-ud-')

    cguiLastTimeStepInput = PySimpleGUI.InputText(key='-lts-')
    cguiLastTimeStepText = PySimpleGUI.Text('Timestep number up to which the simulation should run.\n' +
                                          'Scenario may not support higher last step.')

    adjust_values_column = PySimpleGUI.Column(extend_cgui_with_adjustable_values(), scrollable=True, vertical_scroll_only=True, expand_x=True, element_justification="l")

    switch_button = PySimpleGUI.Checkbox("Data Visualization during Simulation", default=cf.visualization_shown, key='sb')
    sumogui_button = PySimpleGUI.Checkbox("SUMO's GUI", default=cf.sumo_GuiOn,
                                         key='sgui')
    convert_xml_button = PySimpleGUI.Checkbox("Convert xml to csv after simulation", default=cf.convert_to_csv_after_sim,
                                         key='cxml')

    cguiNumberOfLoopsText = PySimpleGUI.Text('How many runs of this configuration?')
    cguiNumberOfLoopsInput = PySimpleGUI.InputText(default_text=1, key='-loop-')
    cguiCurrentLoopsNumber = PySimpleGUI.Text('Currently added: ' + str(num_of_loops), key='-num_loops-')
    cguiAddLoopButton = PySimpleGUI.Button('Add Configuration to Loop')

    global numeric_error_msg

    cgui_layout = [[cguiTableName],
                   [cguiScenTable],
                   [cguiStartButton, cguiQuitButton],
                   [PySimpleGUI.Text()],
                   [switch_button, sumogui_button, convert_xml_button],
                   [cguiAddLoopButton, cguiCurrentLoopsNumber],
                   [cguiNumberOfLoopsText, cguiNumberOfLoopsInput],
                   [PySimpleGUI.Text()],
                   [cguiUpdateDelayText, cguiUpdateDelayInput],
                   [cguiLastTimeStepText, cguiLastTimeStepInput],
                   [PySimpleGUI.Text()],
                   [PySimpleGUI.Text(numeric_error_msg + "Adjust config values. Must be numbers.")],
                   [adjust_values_column],
                   ]

    numeric_error_msg = ""

    global recent_sim_msg
    window_msg = recent_sim_msg

    return PySimpleGUI.Window('Configurations' + window_msg, cgui_layout, size=(cGUI_size_x, cGUI_size_y), resizable=True)


def extend_cgui_with_adjustable_values():
    """
    Returns list of elements to add to cGUI layout.
    """

    global adjustable_config_values
    new_layout_text = list()

    for elem in adjustable_config_values:
        if elem == "av_density":
            new_layout_text.append([PySimpleGUI.Text("Base:", justification="center", text_color="Black")])
        elif elem == "group_size_dfv_two_to_three":
            new_layout_text.append([PySimpleGUI.Text("\nGroup Size:", justification="center", text_color="Black")])
        elif elem == "ttc_lower_extreme_time":
            new_layout_text.append([PySimpleGUI.Text("\nTime To Collision:", justification="center", text_color="Black")])
        elif elem == "waiting_time_accepted_value":
            new_layout_text.append([PySimpleGUI.Text("\nWaiting Time:", justification="center", text_color="Black")])
        elif elem == "small_vehicle_size":
            new_layout_text.append([PySimpleGUI.Text("\nVehicle Size:", justification="center", text_color="Black")])
        elif elem == "lane_low_occupancy_rate":
            new_layout_text.append([PySimpleGUI.Text("\nOccupancy:", justification="center", text_color="Black")])
        elif elem == "child_age":
            new_layout_text.append([PySimpleGUI.Text("\nChildren:", justification="center", text_color="Black")])
        elif elem == "smombie_dfv":
            new_layout_text.append([PySimpleGUI.Text("\nSmombies:", justification="center", text_color="Black")])
        elif elem == "male_gender_dfv":
            new_layout_text.append([PySimpleGUI.Text("\nGender:", justification="center", text_color="Black")])
        elif elem == "impaired_vision_dfv":
            new_layout_text.append([PySimpleGUI.Text("\nDisability:", justification="center", text_color="Black")])
        elif elem == "walking_pedestrian_dfv":
            new_layout_text.append([PySimpleGUI.Text("\nOther:", justification="center", text_color="Black")])

        new_layout_text.append([PySimpleGUI.Text(pad(adjust_config_value(elem, 'text', 0)), justification="l"), PySimpleGUI.InputText(key=elem, default_text=adjust_config_value(elem, 'get', 0))])
    return new_layout_text


def pad(text: str) -> str:
    """
    Pads a string to a specific number of characters (with " ")

    :param text: String to be padded.
    """

    string_goal_size_text = adjust_config_value('smombie_chance_at_start_age', 'text', 0) # change this if needed
    string_goal_size = len(string_goal_size_text)
    string_current_size = len(text)
    padding_length = string_goal_size - string_current_size
    for i in range(padding_length):
        text += " "
    return text


def run_gui():
    """
    Runs GUI during simulation.
    """

    global gui
    global current_traci_step
    if gui is not None:
        gui.Element('-timestep-').update(
            "Timestep: " + str(current_traci_step) + " (Update delay: " + str(cf.update_delay) + " steps)")
    if gui is None:
        gui = __create_gui()
    elif int(current_traci_step) % cf.update_delay == 0:
        gui.Element('-cdt-').update(values=__create_crossing_data_array())
        sort_ages()
        gui.Element('-ags-').update(values=ages)
        sort_crossingIDs()
        gui.Element('-cr-').update(values=crossingIDs)
        gui.Element('-tp-').update("Pedestrians: " + str(total_pedestrians))
        gui.Element('-v-').update("Vehicles: " + str(total_vehicles) + "  (AVs: " + str(total_av) + "/eHMI: " + str(total_ehmi) + ")")

        if cf.visualization_shown:
            vis_results()

    event, values = gui.read(timeout=1)

    if event == PySimpleGUI.WINDOW_CLOSED or event == 'Quit Application':
        gui.close()
        gui = None
        return 'closed'
    elif event == 'Stop':
        close_gui()
        return 'stop'
    elif event == 'Pause':
        gui.Element('Pause').update('Continue')
        while True:
            event, values = gui.read()
            if event == 'Pause':
                gui.Element('Pause').update('Pause')
                break
            elif event == 'Stop':
                close_gui()
                return 'stop'
            elif event == PySimpleGUI.WINDOW_CLOSED or event == 'Quit Application':
                gui.close()
                gui = None
                return 'closed'


def close_gui() -> None:
    """
    Closes GUI running during simulation.
    """

    global gui
    global current_traci_step
    global current_sim
    global recent_sim_msg
    if gui != None:
        gui.close()
        gui = None
        recent_sim_msg = " (" + str(current_sim) + " stopped at " + str(current_traci_step) + ")"
        current_sim = ""


def run_cgui() -> str:
    """
    Runs config GUI that is displayed prior to the simulation.
    """
    global in_loop
    global current_sim
    global numeric_error_msg
    global num_of_loops
    global cgui
    if cgui is None:
        cgui = __create_cgui()

    while True:
        event, values = cgui.read(timeout=5)

        cgui.Element('-num_loops-').update('Currently added: ' + str(num_of_loops))

        if num_of_loops != 0:
            cgui.Element('ss').update("Start Loop")
        else:
            cgui.Element('ss').update('Start Simulation')

        # get next config in loop data
        if event == 'ss' and not in_loop and len(loop_data) != 0 or len(loop_data) != 0 and in_loop:
            if not in_loop:
                if values['sb']:
                    cf.visualization_shown = True
                else:
                    cf.visualization_shown = False
                if values['sgui']:
                    cf.sumo_GuiOn = True
                else:
                    cf.sumo_GuiOn = False
                if values['cxml']:
                    cf.convert_to_csv_after_sim = True
                else:
                    cf.convert_to_csv_after_sim = False

            current_run_config = loop_data[0]
            current_sim = current_run_config[0]
            cf.sumocfgPath = current_run_config[1]
            cf.update_delay = current_run_config[2]
            cf.run_sim_until_step = current_run_config[3]
            for i, elem in enumerate(adjustable_config_values):
                adjust_config_value(elem, 'adjust', current_run_config[4 + i])
            loop_data.pop(0)
            num_of_loops = num_of_loops - 1
            if num_of_loops == 0:
                in_loop = False # Set in loop to False to prevent entering this if clause
            else:
                in_loop = True # Set to True after starting loop so it automatically enters this if clause

            close_cgui()
            return 'sim_start'

        # add config to loop data if button is pressed
        if event == "Add Configuration to Loop" and values['-selectedscen-'] != '':
            try:
                for i in range(int(values['-loop-'])):
                    num_of_loops += 1
                    run_configuration = list()
                    run_configuration.append(cf.scenarios[values['-selectedscen-'][0]][0])
                    run_configuration.append(cf.scenarios[values['-selectedscen-'][0]][1])
                    run_configuration.append(int(values['-ud-']))
                    run_configuration.append(int(values['-lts-']))
                    for elem in adjustable_config_values:
                        run_configuration.append(values[elem])
                    loop_data.append(run_configuration)
            except:
                numeric_error_msg = "(!ERROR: all values must be numeric!) "
                return 'restart'

        if event == PySimpleGUI.WINDOW_CLOSED or event == 'Quit Application':
            close_cgui()
            return 'closed'

        # start simulation and adjust all given values
        if event == 'ss' and values['-selectedscen-'] != '' and num_of_loops == 0:
            if values['sb']:
                cf.visualization_shown = True
            else:
                cf.visualization_shown = False
            if values['sgui']:
                cf.sumo_GuiOn = True
            else:
                cf.sumo_GuiOn = False
            if values['cxml']:
                cf.convert_to_csv_after_sim = True
            else:
                cf.convert_to_csv_after_sim = False


            if values['-ud-'] != '':
                try:
                    cf.update_delay = int(values['-ud-'])
                except:
                    pass

            if values['-lts-'] != '':
                try:
                    cf.run_sim_until_step = int(values['-lts-'])
                except:
                    pass

            for i in range(len(adjustable_config_values)):
                if "interrupt" == str(adjust_config_value(adjustable_config_values[i], 'adjust', values[adjustable_config_values[i]])):
                    numeric_error_msg = "(!ERROR: all values must be numeric!) "
                    return 'restart'

            if values['-selectedscen-']:
                current_sim = cf.scenarios[values['-selectedscen-'][0]][0]
                cf.sumocfgPath = cf.scenarios[values['-selectedscen-'][0]][1]
                close_cgui()
                return 'sim_start'


def close_cgui() -> None:
    """
    Closes config GUI.
    """

    global cgui
    if not (cgui == None):
        cgui.close()
        cgui = None


def get_scenario_name(path: str) -> str:
    """
    Returns name of scenario with given path.
    """

    for elem in cf.scenarios:
        if elem[1] == path:
            return elem[0]
    return ""


def get_avg_of_age_crossings(start_age: int, end_age: int) -> float:
    """
    This function return the average amount of disrespect cases of an age group towards AVs.

    :param start_age: Starting age of age group.
    :param end_age: Ending age of age group.
    """

    crossing_cases: int = 0
    num_of_ages: int = end_age - start_age + 1

    i = 0
    while start_age + i != end_age + 1:
        for elem in ages:
            if elem[0] == start_age + i:
                crossing_cases += elem[1]
                break
        i += 1

    return float(crossing_cases/num_of_ages)


def vis_results():
    """
    Visualizes current data during simulation.
    """

    figure = plt.figure("Crossed Events", figsize=(dv_size_x, dv_size_y))

    plt.subplot(1, 2, 1)

    plt.bar('men', men_crossed, color='blue')
    plt.bar('women', women_crossed, color='pink')
    plt.bar('other', other_crossed, color='green')
    plt.bar('healthy_vis', healthy_vision_crossed, color='orange')
    plt.bar('impaired_vis', impaired_vision_crossed, color='yellow')

    plt.ylabel("y-axis: Count")
    plt.xlabel("x-axis: Group")
    plt.title('Attribute Distribution')

    plt.subplot(1, 2, 2)

    plt.bar('6-10', get_avg_of_age_crossings(6, 10), color='black')
    plt.bar('11-20', get_avg_of_age_crossings(11, 20), color='black')
    plt.bar('21-30', get_avg_of_age_crossings(21, 30), color='black')
    plt.bar('31-40', get_avg_of_age_crossings(31, 40), color='black')
    plt.bar('41-50', get_avg_of_age_crossings(41, 50), color='black')
    plt.bar('51-60', get_avg_of_age_crossings(51, 60), color='black')
    plt.bar('61-70', get_avg_of_age_crossings(61, 70), color='black')
    plt.bar('71-80', get_avg_of_age_crossings(71, 80), color='black')
    plt.bar('81-90', get_avg_of_age_crossings(81, 90), color='black')
    plt.bar('91-99', get_avg_of_age_crossings(91, 99), color='black')

    plt.ylabel("y-axis: Average Count")
    plt.xlabel("x-axis: Age Range")
    plt.title('Age Distribution')

    plt.tight_layout()

    plt.ion()
    plt.show()


# adjusts given value in config when simulation is started
# action: either 'get' (gets value), 'adjust' (adjusts value) or 'text' (gets text to show in GUI)
# new_value is only important for 'adjust'
def adjust_config_value(elem: str, action: str, new_value):
    """
    Gets value or adjusts value or gets text depending on action and element.

    :param elem: String that contains element.
    :param action: Action that is executed ('get' or 'adjust' or 'text')
    :param new_value: New value if 'adjust' action is chosen. If not, give random number.
    """

    int_value = False

    # convert these values to int or float
    match elem:
        case "waiting_time_accepted_value":
            int_value = True
        case "smombie_start_age":
            int_value = True
        case "smombie_peak_age":
            int_value = True
        case "smombie_end_age":
            int_value = True

    if new_value != '':
        try:
            if int_value:
                new_value = int(new_value)
            else:
                new_value = float(new_value)
            match elem:

                case "av_density":
                    match action:
                        case 'get':
                            return cf.av_density
                        case 'adjust':
                            cf.av_density = new_value
                        case 'text':
                            return "automated vehicle (AV) density (0.0 <= x <= 1.0)                                       "

                case "ehmi_density":
                    match action:
                        case 'get':
                            return cf.ehmi_density
                        case 'adjust':
                            cf.ehmi_density = new_value
                        case 'text':
                            return "AVs with eHMI density (0.0 <= x <= 1.0)                                                      "

                case "est_walking_speed":
                    match action:
                        case 'get':
                            return cf.est_walking_speed
                        case 'adjust':
                            cf.est_walking_speed = new_value
                        case 'text':
                            return "estimated walking speed (m/s) (x > 0.0)                                               "

                case "base_automated_vehicle_defiance":
                    match action:
                        case 'get':
                            return cf.base_automated_vehicle_defiance
                        case 'adjust':
                            cf.base_automated_vehicle_defiance = new_value
                        case 'text':
                            return "base defiance value (DFV) for priority of AVs (x >= 0.0)                           "

                case "ehmi_dfv":
                    match action:
                        case 'get':
                            return cf.ehmi_dfv
                        case 'adjust':
                            cf.ehmi_dfv = new_value
                        case 'text':
                            return "base DFV to defy priority of AVs with eHMI (x >= 0.0)                               "

                case "walking_pedestrian_dfv":
                    match action:
                        case 'get':
                            return cf.walking_pedestrian_dfv
                        case 'adjust':
                            cf.walking_pedestrian_dfv = new_value
                        case 'text':
                            return "pedestrian-already-walking DFV (x >= 0.0)                                          "

                case "group_size_dfv_two_to_three":
                    match action:
                        case 'get':
                            return cf.group_size_dfv_two_to_three
                        case 'adjust':
                            cf.group_size_dfv_two_to_three = new_value
                        case 'text':
                            return "DFV for groups of two or three (x >= 0.0)                                               "

                case "group_size_dfv_over_three":
                    match action:
                        case 'get':
                            return cf.group_size_dfv_over_three
                        case 'adjust':
                            cf.group_size_dfv_over_three = new_value
                        case 'text':
                            return "DFV for groups of more than three (x >= 0.0)                                         "

                case "ttc_lower_extreme_time":
                    match action:
                        case 'get':
                            return cf.ttc_lower_extreme_time
                        case 'adjust':
                            cf.ttc_lower_extreme_time = new_value
                        case 'text':
                            return "time to collision (TTC) in seconds under which extreme DFV is used (x >= 0.0)       "

                case "ttc_lower_bound_time":
                    match action:
                        case 'get':
                            return cf.ttc_lower_bound_time
                        case 'adjust':
                            cf.ttc_lower_bound_time = new_value
                        case 'text':
                            return "TTC in seconds under which the lower bound DFV is used (x >= 0.0)                        "

                case "ttc_upper_bound_time":
                    match action:
                        case 'get':
                            return cf.ttc_upper_bound_time
                        case 'adjust':
                            cf.ttc_upper_bound_time = new_value
                        case 'text':
                            return "TTC in seconds over which the upper bound DFV is used (x >= 0.0)                          "

                case "ttc_dfv_under_lower_extreme":
                    match action:
                        case 'get':
                            return cf.ttc_dfv_under_lower_extreme
                        case 'adjust':
                            cf.ttc_dfv_under_lower_extreme = new_value
                        case 'text':
                            return "DFV for extremely low TTC (x >= 0.0)                                                                              "

                case "ttc_dfv_under_lower_bound":
                    match action:
                        case 'get':
                            return cf.ttc_dfv_under_lower_bound
                        case 'adjust':
                            cf.ttc_dfv_under_lower_bound = new_value
                        case 'text':
                            return "DFV if TTC is under lower bound (x >= 0.0)                                                                    "

                case "ttc_dfv_over_upper_bound":
                    match action:
                        case 'get':
                            return cf.ttc_dfv_over_upper_bound
                        case 'adjust':
                            cf.ttc_dfv_over_upper_bound = new_value
                        case 'text':
                            return "DFV if TTC is over upper bound (x >= 0.0)                                                                      "

                case "ttc_base_at_lower_bound":
                    match action:
                        case 'get':
                            return cf.ttc_base_at_lower_bound
                        case 'adjust':
                            cf.ttc_base_at_lower_bound = new_value
                        case 'text':
                            return "value from lower bound for linear increase (x >= 0.0)                                                   "

                case "ttc_base_at_upper_bound":
                    match action:
                        case 'get':
                            return cf.ttc_base_at_upper_bound
                        case 'adjust':
                            cf.ttc_base_at_upper_bound = new_value
                        case 'text':
                            return "value from upper bound for linear increase (x >= value above)                                   "

                case "waiting_time_accepted_value":
                    match action:
                        case 'get':
                            return cf.waiting_time_accepted_value
                        case 'adjust':
                            cf.waiting_time_accepted_value = new_value
                        case 'text':
                            return "accepted waiting time value (seconds) (x >= 0)                                                    "

                case "waiting_time_dfv_under_accepted_value":
                    match action:
                        case 'get':
                            return cf.waiting_time_dfv_under_accepted_value
                        case 'adjust':
                            cf.waiting_time_dfv_under_accepted_value = new_value
                        case 'text':
                            return "DFV if waiting time is under accepted value (x >= 0.0)                                         "

                case "waiting_time_dfv_over_accepted_value_increase_per_second":
                    match action:
                        case 'get':
                            return cf.waiting_time_dfv_over_accepted_value_increase_per_second
                        case 'adjust':
                            cf.waiting_time_dfv_over_accepted_value_increase_per_second = new_value
                        case 'text':
                            return "DFV if waiting time is above accepted value (linear increase) (x >= 0.0)            "

                case "small_vehicle_size":
                    match action:
                        case 'get':
                            return cf.small_vehicle_size
                        case 'adjust':
                            cf.small_vehicle_size = new_value
                        case 'text':
                            return "vehicle size that is considered small (m^2 of the front) (x >= 0.0)                            "

                case "neutral_vehicle_size":
                    match action:
                        case 'get':
                            return cf.neutral_vehicle_size
                        case 'adjust':
                            cf.neutral_vehicle_size = new_value
                        case 'text':
                            return "vehicle size that is considered neutral (m^2 of the front) (x >= small vehicle size)"

                case "large_vehicle_size":
                    match action:
                        case 'get':
                            return cf.large_vehicle_size
                        case 'adjust':
                            cf.large_vehicle_size = new_value
                        case 'text':
                            return "vehicle size that is considered large (m^2 of the front) (x >= neutral vehicle size) "

                case "small_vehicle_size_dfv":
                    match action:
                        case 'get':
                            return cf.small_vehicle_size_dfv
                        case 'adjust':
                            cf.small_vehicle_size_dfv = new_value
                        case 'text':
                            return "small vehicle size DFV (x >= 0.0)                                               "

                case "neutral_vehicle_size_dfv":
                    match action:
                        case 'get':
                            return cf.neutral_vehicle_size_dfv
                        case 'adjust':
                            cf.neutral_vehicle_size_dfv = new_value
                        case 'text':
                            return "neutral vehicle size DFV (x >= 0.0)"

                case "large_vehicle_size_dfv":
                    match action:
                        case 'get':
                            return cf.large_vehicle_size_dfv
                        case 'adjust':
                            cf.large_vehicle_size_dfv = new_value
                        case 'text':
                            return "large vehicle size DFV (x >= 0.0)                                                "

                case "lane_low_occupancy_rate":
                    match action:
                        case 'get':
                            return cf.lane_low_occupancy_rate
                        case 'adjust':
                            cf.lane_low_occupancy_rate = new_value
                        case 'text':
                            return "low occupancy rate in (length of all vehicles)/(street length) (1.0 >= x >= 0.0)         "

                case "lane_high_occupancy_rate":
                    match action:
                        case 'get':
                            return cf.lane_high_occupancy_rate
                        case 'adjust':
                            cf.lane_high_occupancy_rate = new_value
                        case 'text':
                            return "high occupancy rate (0.1 means 10% of street is filled with vehs) (1.0 >= x >= 0.0)"

                case "low_occupancy_rate_dfv":
                    match action:
                        case 'get':
                            return cf.low_occupancy_rate_dfv
                        case 'adjust':
                            cf.low_occupancy_rate_dfv = new_value
                        case 'text':
                            return "low occupancy rate DFV (linear decrease to value below) (x >= 0.0)                        "

                case "high_occupancy_rate_dfv":
                    match action:
                        case 'get':
                            return cf.high_occupancy_rate_dfv
                        case 'adjust':
                            cf.high_occupancy_rate_dfv = new_value
                        case 'text':
                            return "high occupancy rate DFV (x >= 0.0)                                                                              "

                case "neutral_street_width":
                    match action:
                        case 'get':
                            return cf.neutral_street_width
                        case 'adjust':
                            cf.neutral_street_width = new_value
                        case 'text':
                            return "street width that is considered neutral (x >= 0.0)                                "

                case "child_age":
                    match action:
                        case 'get':
                            return cf.child_age
                        case 'adjust':
                            cf.child_age = new_value
                        case 'text':
                            return "up to what age a person is defined as a child (x >= 0)                              "

                case "girl_present_dfv":
                    match action:
                        case 'get':
                            return cf.girl_present_dfv
                        case 'adjust':
                            cf.girl_present_dfv = new_value
                        case 'text':
                            return "DFV if a girl is present (x >= 0.0)                                                                 "

                case "boy_present_dfv":
                    match action:
                        case 'get':
                            return cf.boy_present_dfv
                        case 'adjust':
                            cf.boy_present_dfv = new_value
                        case 'text':
                            return "DFV if a boy is present (x >= 0.0)                                                                "

                case "smombie_dfv":
                    match action:
                        case 'get':
                            return cf.smombie_dfv
                        case 'adjust':
                            cf.smombie_dfv = new_value
                        case 'text':
                            return "DFV of a smartphone zombie (smombie) (x >= 0.0)                                                "

                case "smombie_start_age":
                    match action:
                        case 'get':
                            return cf.smombie_start_age
                        case 'adjust':
                            cf.smombie_start_age = new_value
                        case 'text':
                            return "starting age of a smombie to apply the DFV (x >= 0)                                              "

                case "smombie_peak_age":
                    match action:
                        case 'get':
                            return cf.smombie_peak_age
                        case 'adjust':
                            cf.smombie_peak_age = new_value
                        case 'text':
                            return "age where smombie DFV impact reaches its peak (x >= value above)                 "

                case "smombie_end_age":
                    match action:
                        case 'get':
                            return cf.smombie_end_age
                        case 'adjust':
                            cf.smombie_end_age = new_value
                        case 'text':
                            return "age where smombie DFV impact reaches its end (x >= value above)                   "

                case "smombie_chance_at_start_age":
                    match action:
                        case 'get':
                            return cf.smombie_chance_at_start_age
                        case 'adjust':
                            cf.smombie_chance_at_start_age = new_value
                        case 'text':
                            return "multiplicative linear increase to smombie DFV from start to peak age (x >= 0.0)"

                case "smombie_chance_at_peak_age":
                    match action:
                        case 'get':
                            return cf.smombie_chance_at_peak_age
                        case 'adjust':
                            cf.smombie_chance_at_peak_age = new_value
                        case 'text':
                            return "multiplicative smombie value to DFV at peak age (x >= 0.0)                                   "

                case "smombie_chance_at_end_age":
                    match action:
                        case 'get':
                            return cf.smombie_chance_at_end_age
                        case 'adjust':
                            cf.smombie_chance_at_end_age = new_value
                        case 'text':
                            return "multiplicative linear decrease to smombie DFV from peak to end age (x >= 0.0)"

                case "smombie_base_chance":
                    match action:
                        case 'get':
                            return cf.smombie_base_chance
                        case 'adjust':
                            cf.smombie_base_chance = new_value
                        case 'text':
                            return "multiplicative value to smombie DFV for other ages (x >= 0.0)                               "

                case "male_gender_dfv":
                    match action:
                        case 'get':
                            return cf.male_gender_dfv
                        case 'adjust':
                            cf.male_gender_dfv = new_value
                        case 'text':
                            return "DFV for men (x >= 0.0)                                                                "

                case "female_gender_dfv":
                    match action:
                        case 'get':
                            return cf.female_gender_dfv
                        case 'adjust':
                            cf.female_gender_dfv = new_value
                        case 'text':
                            return "DFV for women (x >= 0.0)                                                           "

                case "other_gender_dfv":
                    match action:
                        case 'get':
                            return cf.other_gender_dfv
                        case 'adjust':
                            cf.other_gender_dfv = new_value
                        case 'text':
                            return "DFV for other genders (x >= 0.0)"

                case "impaired_vision_dfv":
                    match action:
                        case 'get':
                            return cf.impaired_vision_dfv
                        case 'adjust':
                            cf.impaired_vision_dfv = new_value
                        case 'text':
                            return "DFV for people with impaired vision (x >= 0.0)"

                case "healthy_vision_dfv":
                    match action:
                        case 'get':
                            return cf.healthy_vision_dfv
                        case 'adjust':
                            cf.healthy_vision_dfv = new_value
                        case 'text':
                            return "DFV for people with healthy vision (x >= 0.0)                                   "
        except:
            return "interrupt"  # interrupt if given value was not numerical


