#!/usr/bin/env python
import config as cf
import matplotlib.pyplot as plt
import sys
import time
from typing import Dict

from PySide6 import QtCore, QtGui, QtWidgets
from screeninfo import get_monitors

#############################################
# these are the size parameters for all three GUI windows

monitor_size_x : int = 0
monitor_size_y : int = 0

for monitor in get_monitors():
    if monitor_size_x < monitor.width:
        monitor_size_x = monitor.width
    if monitor_size_y < monitor.height:
        monitor_size_y = monitor.height

monitor_size_x = int(monitor_size_x / 2)
monitor_size_y = monitor_size_y

cGUI_size_x: int = monitor_size_x  # 800 if sys.platform.startswith("darwin") else 1000
cGUI_size_y: int = monitor_size_y  # 600 if sys.platform.startswith("darwin") else 800

GUI_size_x: int = monitor_size_x  # 500
GUI_size_y: int = monitor_size_y  # 1040

dv_size_x: int = int(monitor_size_x / 50)  # 12  # data visualization
dv_size_y: int = int(monitor_size_y / 200)  # 5  # data visualization

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

#current_crossing_events = 0

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

visualized_file = ""

num_of_loops: int = 0
loop_data: list = [] # saves configuration of each run in a loop
in_loop: bool = False # True if in a simulation loop with several simulations

app: QtWidgets.QApplication | None = None


def _get_app() -> QtWidgets.QApplication:
    """Return a QApplication instance, creating one if necessary."""

    global app
    existing = QtWidgets.QApplication.instance()
    if existing is not None and app is None:
        app = existing

    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle("Fusion")

        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(245, 247, 251))
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(31, 41, 51))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 255))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(241, 245, 249))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(31, 41, 55))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(37, 99, 235))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(255, 255, 255))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(37, 99, 235))
        palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))
        app.setPalette(palette)

        font = QtGui.QFont("Segoe UI", 10)
        app.setFont(font)

    return app


def _configure_table(table: QtWidgets.QTableWidget, headers: list[str]) -> None:
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
    table.setAlternatingRowColors(True)
    table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)


def _fill_table(table: QtWidgets.QTableWidget, data: list[list]) -> None:
    table.setRowCount(len(data))
    for row, row_data in enumerate(data):
        for column, value in enumerate(row_data):
            item = QtWidgets.QTableWidgetItem(str(value))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, column, item)


class SimulationWindow(QtWidgets.QMainWindow):
    """Main window shown during a running simulation."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Simulating")
        self.resize(GUI_size_x, GUI_size_y)
        self.setMinimumSize(720, 640)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.paused = False
        self.stop_requested = False
        self.quit_requested = False
        self.was_closed = False

        self.setStyleSheet(
            """
            QWidget {
                background-color: #f5f7fb;
                color: #1f2937;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 12pt;
            }
            QGroupBox {
                border: 1px solid #d0d7de;
                border-radius: 10px;
                margin-top: 12px;
                padding: 16px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 4px;
                color: #0f172a;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border-radius: 6px;
                padding: 10px 18px;
                font-weight: 600;
            }
            QPushButton#pauseButton {
                background-color: #f59e0b;
                color: #1f2937;
            }
            QPushButton#stopButton {
                background-color: #10b981;
            }
            QPushButton#quitButton {
                background-color: #ef4444;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QTableWidget {
                background-color: #ffffff;
                border: none;
                alternate-background-color: #f1f5f9;
                gridline-color: #d0d7de;
            }
            QHeaderView::section {
                background-color: #1d4ed8;
                color: #ffffff;
                padding: 6px;
                border: none;
                font-weight: 600;
            }
            """
        )

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(24, 24, 24, 24)

        self.time_label = QtWidgets.QLabel()
        self.time_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.ped_label = QtWidgets.QLabel()
        self.ped_label.setStyleSheet("font-size: 16px;")
        self.vehicle_label = QtWidgets.QLabel()
        self.vehicle_label.setStyleSheet("font-size: 16px;")

        status_group = QtWidgets.QGroupBox("Simulation Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)
        status_layout.setSpacing(6)
        status_layout.addWidget(self.time_label)
        status_layout.addWidget(self.ped_label)
        status_layout.addWidget(self.vehicle_label)
        main_layout.addWidget(status_group)

        self.crossing_data_table = QtWidgets.QTableWidget()
        _configure_table(
            self.crossing_data_table,
            ["Category", "Crossed", "Not Crossed", "Ratio (Crossed)"],
        )

        crossing_data_group = QtWidgets.QGroupBox("Crossing Overview")
        data_layout = QtWidgets.QVBoxLayout(crossing_data_group)
        data_layout.addWidget(self.crossing_data_table)
        main_layout.addWidget(crossing_data_group)

        self.ages_table = QtWidgets.QTableWidget()
        _configure_table(self.ages_table, ["Age", "Times crossed", "Times not crossed"])

        ages_group = QtWidgets.QGroupBox("Age Distribution")
        ages_layout = QtWidgets.QVBoxLayout(ages_group)
        ages_layout.addWidget(self.ages_table)
        main_layout.addWidget(ages_group)

        self.crossing_table = QtWidgets.QTableWidget()
        _configure_table(self.crossing_table, ["CrossingID", "Event Count"])

        crossings_group = QtWidgets.QGroupBox("Crossing Events by Location")
        crossings_layout = QtWidgets.QVBoxLayout(crossings_group)
        crossings_layout.addWidget(self.crossing_table)
        main_layout.addWidget(crossings_group)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        self.pause_button = QtWidgets.QPushButton("Pause")
        self.pause_button.setObjectName("pauseButton")
        self.pause_button.clicked.connect(self.toggle_pause)
        button_layout.addWidget(self.pause_button)

        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.request_stop)
        button_layout.addWidget(self.stop_button)

        self.quit_button = QtWidgets.QPushButton("Quit Application")
        self.quit_button.setObjectName("quitButton")
        self.quit_button.clicked.connect(self.request_quit)
        button_layout.addWidget(self.quit_button)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def update_time_step(self, timestep: int, delay: int) -> None:
        self.time_label.setText(
            f"Timestep: {timestep} (Update delay: {delay} steps)"
        )

    def update_counts(
        self, total_pedestrians: int, total_vehicles: int, total_av: int, total_ehmi: int
    ) -> None:
        self.ped_label.setText(f"Pedestrians: {total_pedestrians}")
        self.vehicle_label.setText(
            f"Vehicles: {total_vehicles}  (of which AVs: {total_av}/AVs with eHMI: {total_ehmi})"
        )

    def update_crossing_data(self, data: list[list]) -> None:
        _fill_table(self.crossing_data_table, data)

    def update_age_distribution(self, data: list[list]) -> None:
        _fill_table(self.ages_table, data)

    def update_crossing_events(self, data: list[list]) -> None:
        _fill_table(self.crossing_table, data)

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_button.setText("Continue" if self.paused else "Pause")

    def request_stop(self) -> None:
        self.stop_requested = True

    def request_quit(self) -> None:
        self.quit_requested = True
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        self.was_closed = True
        super().closeEvent(event)


class ConfigWindow(QtWidgets.QMainWindow):
    """Configuration window shown before running a simulation."""

    def __init__(self, loop_count: int, recent_message: str, error_prefix: str) -> None:
        super().__init__()
        self.setWindowTitle('Configurations' + recent_message)
        self.resize(cGUI_size_x, cGUI_size_y)
        self.setMinimumSize(720, 640)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.start_clicked = False
        self.add_loop_clicked = False
        self.quit_requested = False
        self.was_closed = False

        self.adjustable_inputs: Dict[str, QtWidgets.QLineEdit] = {}

        self.setStyleSheet(
            """
            QWidget {
                background-color: #f7f8fc;
                color: #1f2937;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 11pt;
            }
            QGroupBox {
                border: 1px solid #d0d7de;
                border-radius: 10px;
                margin-top: 14px;
                padding: 16px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 18px;
                padding: 0 4px;
                color: #0f172a;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border-radius: 6px;
                padding: 10px 18px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton#addLoopButton {
                background-color: #10b981;
            }
            QPushButton#quitButton {
                background-color: #ef4444;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #d0d7de;
                border-radius: 6px;
            }
            QScrollArea {
                border: none;
            }
            QLineEdit {
                padding: 6px 8px;
                border: 1px solid #d0d7de;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QCheckBox {
                padding: 4px 0;
            }
            """
        )

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(24, 24, 24, 24)

        header = QtWidgets.QLabel("Simulation Configuration")
        header.setStyleSheet("font-size: 22px; font-weight: 700;")
        main_layout.addWidget(header)

        scenario_group = QtWidgets.QGroupBox("Scenarios")
        scenario_layout = QtWidgets.QVBoxLayout(scenario_group)
        scenario_layout.setSpacing(12)
        self.scenario_list = QtWidgets.QListWidget()
        self.scenario_list.setAlternatingRowColors(True)
        self.scenario_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        for scenario in cf.scenarios:
            self.scenario_list.addItem(scenario[0])
        if self.scenario_list.count() > 0:
            self.scenario_list.setCurrentRow(0)
        scenario_layout.addWidget(self.scenario_list)
        main_layout.addWidget(scenario_group)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        self.start_button = QtWidgets.QPushButton("Start Simulation")
        self.start_button.clicked.connect(self._handle_start)
        buttons_layout.addWidget(self.start_button)

        self.quit_button = QtWidgets.QPushButton("Quit Application")
        self.quit_button.setObjectName("quitButton")
        self.quit_button.clicked.connect(self._handle_quit)
        buttons_layout.addWidget(self.quit_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        options_group = QtWidgets.QGroupBox("Run Options")
        options_layout = QtWidgets.QHBoxLayout(options_group)
        options_layout.setSpacing(12)
        self.visualization_checkbox = QtWidgets.QCheckBox("Data Visualization during Simulation")
        self.visualization_checkbox.setChecked(cf.visualization_shown)
        self.sumo_gui_checkbox = QtWidgets.QCheckBox("SUMO's GUI")
        self.sumo_gui_checkbox.setChecked(cf.sumo_GuiOn)
        self.convert_checkbox = QtWidgets.QCheckBox("Convert xml to csv after simulation")
        self.convert_checkbox.setChecked(cf.convert_to_csv_after_sim)
        options_layout.addWidget(self.visualization_checkbox)
        options_layout.addWidget(self.sumo_gui_checkbox)
        options_layout.addWidget(self.convert_checkbox)
        options_layout.addStretch()
        main_layout.addWidget(options_group)

        loop_group = QtWidgets.QGroupBox("Simulation Loop")
        loop_layout = QtWidgets.QVBoxLayout(loop_group)
        loop_controls = QtWidgets.QHBoxLayout()
        self.add_loop_button = QtWidgets.QPushButton("Add Configuration to Loop")
        self.add_loop_button.setObjectName("addLoopButton")
        self.add_loop_button.clicked.connect(self._handle_add_loop)
        loop_controls.addWidget(self.add_loop_button)
        loop_controls.addStretch()
        self.loop_count_label = QtWidgets.QLabel()
        loop_controls.addWidget(self.loop_count_label)
        loop_layout.addLayout(loop_controls)

        loop_form = QtWidgets.QFormLayout()
        loop_form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.loop_input = QtWidgets.QLineEdit("1")
        self.loop_input.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.loop_input.setMaximumWidth(120)
        loop_form.addRow("How many runs of this configuration?", self.loop_input)
        loop_layout.addLayout(loop_form)
        main_layout.addWidget(loop_group)

        timing_group = QtWidgets.QGroupBox("Timing")
        timing_layout = QtWidgets.QFormLayout(timing_group)
        timing_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.update_delay_input = QtWidgets.QLineEdit(str(cf.update_delay))
        self.update_delay_input.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.update_delay_input.setMaximumWidth(160)
        timing_layout.addRow("Gui update delay (increase for better performance)", self.update_delay_input)

        self.last_step_input = QtWidgets.QLineEdit("3600")
        self.last_step_input.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.last_step_input.setMaximumWidth(160)
        timing_layout.addRow("Timestep number up to which the simulation should run.\nScenario may not support higher last step.", self.last_step_input)
        main_layout.addWidget(timing_group)

        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: #ef4444; font-weight: 600;")
        main_layout.addWidget(self.error_label)

        adjust_group = QtWidgets.QGroupBox("Adjustable Configuration Values")
        adjust_layout = QtWidgets.QVBoxLayout(adjust_group)
        adjust_layout.setContentsMargins(0, 0, 0, 0)
        adjust_layout.setSpacing(0)
        self.adjust_scroll = QtWidgets.QScrollArea()
        self.adjust_scroll.setWidgetResizable(True)
        adjust_layout.addWidget(self.adjust_scroll)
        main_layout.addWidget(adjust_group)

        adjust_container = QtWidgets.QWidget()
        self.adjust_scroll.setWidget(adjust_container)
        self.adjust_layout = QtWidgets.QVBoxLayout(adjust_container)
        self.adjust_layout.setSpacing(12)
        self.adjust_layout.setContentsMargins(16, 16, 16, 16)
        self._build_adjustable_fields()

        self.update_loop_info(loop_count)
        self.set_error_message(error_prefix)

    def _build_adjustable_fields(self) -> None:
        section_headers = {
            "av_density": "Base",
            "group_size_dfv_two_to_three": "Group Size",
            "ttc_lower_extreme_time": "Time To Collision",
            "waiting_time_accepted_value": "Waiting Time",
            "small_vehicle_size": "Vehicle Size",
            "lane_low_occupancy_rate": "Occupancy",
            "child_age": "Children",
            "smombie_dfv": "Smombies",
            "male_gender_dfv": "Gender",
            "impaired_vision_dfv": "Disability",
            "walking_pedestrian_dfv": "Other",
        }

        for key in adjustable_config_values:
            if key in section_headers:
                header = QtWidgets.QLabel(section_headers[key])
                header.setStyleSheet("font-size: 16px; font-weight: 700; color: #1d4ed8; margin-top: 12px;")
                self.adjust_layout.addWidget(header)

            row_widget = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)

            label = QtWidgets.QLabel(adjust_config_value(key, 'text', 0))
            label.setWordWrap(True)
            row_layout.addWidget(label, 3)

            line_edit = QtWidgets.QLineEdit(str(adjust_config_value(key, 'get', 0)))
            line_edit.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            line_edit.setMaximumWidth(160)
            self.adjustable_inputs[key] = line_edit
            row_layout.addWidget(line_edit, 1)

            self.adjust_layout.addWidget(row_widget)

        self.adjust_layout.addStretch()

    def update_loop_info(self, loop_count: int) -> None:
        self.loop_count_label.setText(f"Currently added: {loop_count}")
        self.start_button.setText("Start Loop" if loop_count else "Start Simulation")

    def set_error_message(self, prefix: str) -> None:
        if prefix:
            message = f"{prefix}Adjust config values. Must be numbers."
        else:
            message = "Adjust config values. Must be numbers."
        self.error_label.setText(message)

    def get_form_values(self) -> Dict[str, object]:
        selected_index = self.scenario_list.currentRow()
        if selected_index < 0:
            selected_index = None

        adjustable_values = {key: field.text().strip() for key, field in self.adjustable_inputs.items()}

        return {
            'selected_scenario': selected_index,
            'update_delay': self.update_delay_input.text().strip(),
            'last_timestep': self.last_step_input.text().strip(),
            'loop_count': self.loop_input.text().strip(),
            'visualization': self.visualization_checkbox.isChecked(),
            'sumo_gui': self.sumo_gui_checkbox.isChecked(),
            'convert_xml': self.convert_checkbox.isChecked(),
            'adjustable': adjustable_values,
        }

    def _handle_start(self) -> None:
        self.start_clicked = True

    def _handle_add_loop(self) -> None:
        self.add_loop_clicked = True

    def _handle_quit(self) -> None:
        self.quit_requested = True
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        self.was_closed = True
        super().closeEvent(event)

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
    #global current_crossing_events
    #current_crossing_events = 0
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


def __create_gui() -> SimulationWindow:
    """Create and return the simulation window."""

    _get_app()

    reset_numbers()

    window = SimulationWindow()
    window.setWindowTitle(
        "Simulating "
        + current_sim
        + "|Ends at "
        + str(cf.run_sim_until_step)
        + "|Runs left after this: "
        + str(num_of_loops)
    )
    window.update_time_step(current_traci_step, cf.update_delay)
    window.update_counts(total_pedestrians, total_vehicles, total_av, total_ehmi)
    window.update_crossing_data(__create_crossing_data_array())
    window.update_age_distribution(ages)
    window.update_crossing_events(crossingIDs)
    window.show()
    return window


def __create_cgui() -> ConfigWindow:
    """Create and return the configuration window."""

    global numeric_error_msg

    _get_app()

    window = ConfigWindow(num_of_loops, recent_sim_msg, numeric_error_msg)
    window.show()
    numeric_error_msg = ""
    return window


def run_gui():
    """Runs the simulation window and handles user actions."""

    global gui
    global current_traci_step

    application = _get_app()

    if gui is None:
        gui = __create_gui()

    gui.update_time_step(current_traci_step, cf.update_delay)

    if cf.update_delay and int(current_traci_step) % cf.update_delay == 0:
        gui.update_crossing_data(__create_crossing_data_array())
        sort_ages()
        gui.update_age_distribution(ages)
        sort_crossingIDs()
        gui.update_crossing_events(crossingIDs)
        gui.update_counts(total_pedestrians, total_vehicles, total_av, total_ehmi)

        if cf.visualization_shown:
            vis_results()

    application.processEvents()

    if gui.stop_requested:
        close_gui()
        return 'stop'

    if gui.quit_requested or gui.was_closed:
        gui = None
        return 'closed'

    if gui.paused:
        while gui is not None and gui.paused:
            application.processEvents()
            if gui.stop_requested:
                close_gui()
                return 'stop'
            if gui.quit_requested or gui.was_closed:
                gui = None
                return 'closed'
            time.sleep(0.05)

    return None


def close_gui() -> None:
    """Closes the simulation window."""

    global gui
    global current_traci_step
    global current_sim
    global recent_sim_msg
    if gui is not None:
        gui.close()
        gui = None
        recent_sim_msg = " (" + str(current_sim) + " stopped at " + str(current_traci_step) + ")"
        current_sim = ""


def run_cgui() -> str:
    """Runs the configuration window and handles user interaction."""

    global in_loop
    global current_sim
    global numeric_error_msg
    global num_of_loops
    global cgui

    application = _get_app()

    if cgui is None:
        cgui = __create_cgui()

    while True:
        if cgui is None:
            return 'closed'

        cgui.update_loop_info(num_of_loops)
        application.processEvents()

        if cgui.quit_requested or cgui.was_closed:
            close_cgui()
            return 'closed'

        if cgui.add_loop_clicked:
            cgui.add_loop_clicked = False
            values = cgui.get_form_values()
            if values['selected_scenario'] is None:
                continue
            try:
                loops_to_add = int(values['loop_count'])
                for _ in range(loops_to_add):
                    num_of_loops += 1
                    run_configuration = list()
                    selected_index = values['selected_scenario']
                    run_configuration.append(cf.scenarios[selected_index][0])
                    run_configuration.append(cf.scenarios[selected_index][1])
                    run_configuration.append(int(values['update_delay']))
                    run_configuration.append(int(values['last_timestep']))
                    for elem in adjustable_config_values:
                        run_configuration.append(values['adjustable'][elem])
                    loop_data.append(run_configuration)
                numeric_error_msg = ""
                cgui.set_error_message("")
            except Exception:
                numeric_error_msg = "(!ERROR: all values must be numeric!) "
                cgui.set_error_message(numeric_error_msg)
                return 'restart'

        if (cgui.start_clicked and not in_loop and len(loop_data) != 0) or (len(loop_data) != 0 and in_loop):
            if not in_loop:
                values = cgui.get_form_values()
                cf.visualization_shown = bool(values['visualization'])
                cf.sumo_GuiOn = bool(values['sumo_gui'])
                cf.convert_to_csv_after_sim = bool(values['convert_xml'])
            current_run_config = loop_data[0]
            current_sim = current_run_config[0]
            cf.sumocfgPath = current_run_config[1]
            cf.update_delay = current_run_config[2]
            cf.run_sim_until_step = current_run_config[3]
            for i, elem in enumerate(adjustable_config_values):
                adjust_config_value(elem, 'adjust', current_run_config[4 + i])
            loop_data.pop(0)
            num_of_loops -= 1
            in_loop = num_of_loops != 0
            if cgui is not None:
                cgui.start_clicked = False
            close_cgui()
            return 'sim_start'

        if cgui.start_clicked and num_of_loops == 0:
            values = cgui.get_form_values()
            if cgui is not None:
                cgui.start_clicked = False
            if values['selected_scenario'] is None:
                time.sleep(0.05)
                continue

            cf.visualization_shown = bool(values['visualization'])
            cf.sumo_GuiOn = bool(values['sumo_gui'])
            cf.convert_to_csv_after_sim = bool(values['convert_xml'])

            if values['update_delay']:
                try:
                    cf.update_delay = int(values['update_delay'])
                except Exception:
                    pass

            if values['last_timestep']:
                try:
                    cf.run_sim_until_step = int(values['last_timestep'])
                except Exception:
                    pass

            for elem in adjustable_config_values:
                result = adjust_config_value(elem, 'adjust', values['adjustable'][elem])
                if str(result) == 'interrupt':
                    numeric_error_msg = "(!ERROR: all values must be numeric!) "
                    if cgui is not None:
                        cgui.set_error_message(numeric_error_msg)
                    return 'restart'

            selected_index = values['selected_scenario']
            current_sim = cf.scenarios[selected_index][0]
            cf.sumocfgPath = cf.scenarios[selected_index][1]
            close_cgui()
            return 'sim_start'

        time.sleep(0.05)



def close_cgui() -> None:
    """Closes the configuration window."""

    global cgui
    if cgui is not None:
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


