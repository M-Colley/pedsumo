import importlib.util
import os
import pathlib
import sys
import types
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_DIR = REPO_ROOT / "SumoWithAVs"
MAIN_PATH = MODULE_DIR / "main.py"


def load_main_module():
    os.environ.setdefault("SUMO_HOME", str(REPO_ROOT))
    if str(MODULE_DIR) not in sys.path:
        sys.path.insert(0, str(MODULE_DIR))

    gui_stub = types.ModuleType("gui")
    gui_stub.run_gui = lambda: None
    gui_stub.run_cgui = lambda: None
    gui_stub.current_traci_step = 0
    sys.modules["gui"] = gui_stub

    sumolib_stub = types.ModuleType("sumolib")
    sumolib_stub.checkBinary = lambda binary: binary
    sys.modules["sumolib"] = sumolib_stub

    sys.modules["traci"] = types.ModuleType("traci")
    sys.modules["xml2csvSWA"] = types.ModuleType("xml2csvSWA")

    spec = importlib.util.spec_from_file_location("pedsumo_main", MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MainLogicTests(unittest.TestCase):
    def setUp(self):
        self.main = load_main_module()
        self.cf = self.main.cf
        self.original_values = {
            "scenarios": self.cf.scenarios,
            "sumocfgPath": self.cf.sumocfgPath,
            "outputFilesActive": self.cf.outputFilesActive,
            "statsOutput": self.cf.statsOutput,
            "tripinfoOutput": self.cf.tripinfoOutput,
            "personsummaryOutput": self.cf.personsummaryOutput,
            "summaryOutput": self.cf.summaryOutput,
            "vehroutesOutput": self.cf.vehroutesOutput,
            "fcdOutput": self.cf.fcdOutput,
            "fullOutput": self.cf.fullOutput,
            "queueOutput": self.cf.queueOutput,
            "edgedataOutput": self.cf.edgedataOutput,
            "lanedataOutput": self.cf.lanedataOutput,
            "lanechangeOutput": self.cf.lanechangeOutput,
            "amitranOutput": self.cf.amitranOutput,
            "ndumpOutput": self.cf.ndumpOutput,
            "linkOutput": self.cf.linkOutput,
            "personinfoOutput": self.cf.personinfoOutput,
            "multithreading_rerouting_active": self.cf.multithreading_rerouting_active,
            "rerouting_threads": self.cf.rerouting_threads,
            "multithreading_routing_active": self.cf.multithreading_routing_active,
            "routing_threads": self.cf.routing_threads,
        }
        self.original_results_folder = self.main.results_folder_for_next_sim

    def tearDown(self):
        for key, value in self.original_values.items():
            setattr(self.cf, key, value)
        self.main.results_folder_for_next_sim = self.original_results_folder

    def test_waiting_time_defiance_factor_handles_boundary_and_growth(self):
        accepted = self.cf.waiting_time_accepted_value
        self.assertEqual(
            self.main.get_waiting_time_defiance_factor(accepted),
            self.cf.waiting_time_dfv_under_accepted_value,
        )
        self.assertAlmostEqual(
            self.main.get_waiting_time_defiance_factor(accepted + 10),
            1.0 + 10 * self.cf.waiting_time_dfv_over_accepted_value_increase_per_second,
        )

    def test_group_size_defiance_factor_covers_ranges(self):
        self.assertEqual(self.main.get_group_size_defiance_factor(1), 1.0)
        self.assertEqual(
            self.main.get_group_size_defiance_factor(2),
            self.cf.group_size_dfv_two_to_three,
        )
        self.assertEqual(
            self.main.get_group_size_defiance_factor(5),
            self.cf.group_size_dfv_over_three,
        )

    def test_time_to_collision_defiance_factor_uses_linear_interpolation(self):
        self.assertEqual(
            self.main.get_time_to_collision_defiance_factor(self.cf.ttc_lower_extreme_time),
            self.cf.ttc_dfv_under_lower_extreme,
        )
        self.assertEqual(
            self.main.get_time_to_collision_defiance_factor(self.cf.ttc_lower_bound_time),
            self.cf.ttc_dfv_under_lower_bound,
        )
        midpoint = (self.cf.ttc_lower_bound_time + self.cf.ttc_upper_bound_time) / 2
        expected = self.cf.ttc_base_at_lower_bound + (
            midpoint - self.cf.ttc_lower_bound_time
        ) * (
            (self.cf.ttc_base_at_upper_bound - self.cf.ttc_base_at_lower_bound)
            / (self.cf.ttc_upper_bound_time - self.cf.ttc_lower_bound_time)
        )
        self.assertAlmostEqual(
            self.main.get_time_to_collision_defiance_factor(midpoint), expected
        )
        self.assertEqual(
            self.main.get_time_to_collision_defiance_factor(self.cf.ttc_upper_bound_time),
            self.cf.ttc_dfv_over_upper_bound,
        )

    def test_get_current_simulation_name_matches_active_scenario(self):
        self.cf.scenarios = [["ScenarioA", "/tmp/a.sumocfg"], ["ScenarioB", "/tmp/b.sumocfg"]]
        self.cf.sumocfgPath = "/tmp/b.sumocfg"
        self.assertEqual(self.main.get_current_simulation_name(), "ScenarioB")
        self.cf.sumocfgPath = "/tmp/unknown.sumocfg"
        self.assertEqual(self.main.get_current_simulation_name(), "")

    def test_generate_start_config_contains_selected_outputs_and_thread_option(self):
        self.cf.sumocfgPath = "/tmp/example.sumocfg"
        self.main.results_folder_for_next_sim = "/tmp/results"
        self.cf.outputFilesActive = True
        self.cf.statsOutput = True
        self.cf.tripinfoOutput = True
        self.cf.personsummaryOutput = False
        self.cf.summaryOutput = False
        self.cf.vehroutesOutput = False
        self.cf.fcdOutput = False
        self.cf.fullOutput = False
        self.cf.queueOutput = False
        self.cf.edgedataOutput = False
        self.cf.lanedataOutput = False
        self.cf.lanechangeOutput = False
        self.cf.amitranOutput = False
        self.cf.ndumpOutput = False
        self.cf.linkOutput = False
        self.cf.personinfoOutput = False
        self.cf.multithreading_rerouting_active = True
        self.cf.rerouting_threads = 4
        self.cf.multithreading_routing_active = False

        config = self.main.generate_start_config("sumo")
        self.assertEqual(config[0:3], ["sumo", "-c", "/tmp/example.sumocfg"])
        self.assertIn("--statistic-output", config)
        self.assertIn("/tmp/results/stats.xml", config)
        self.assertIn("--tripinfo-output", config)
        self.assertIn("/tmp/results/tripinfo.xml", config)
        self.assertIn("--device.rerouting.threads", config)
        self.assertIn("4", config)
        self.assertTrue(config[-2:] == ["--start", "--quit-on-end"])

    def test_float_range_matches_values_inside_interval(self):
        float_range = self.main.FloatRange(0.0, 1.0)
        self.assertTrue(0.0 in float_range)
        self.assertTrue(0.5 in float_range)
        self.assertTrue(1.0 in float_range)
        self.assertFalse(-0.1 in float_range)
        self.assertEqual(repr(float_range), "[0.0,1.0]")


if __name__ == "__main__":
    unittest.main()
