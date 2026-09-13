"""Unit tests for the pure logic in SumoWithAVs/main.py.

main.py is written to be executed from inside the SumoWithAVs directory and imports traci, sumolib,
gui and xml2csvSWA at module level. The tests therefore load it from its file path with those four
modules replaced by stubs, so the suite runs without a SUMO installation and without a display.
"""

import importlib.util
import os
import pathlib
import random
import sys
import types
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_DIR = REPO_ROOT / "SumoWithAVs"
MAIN_PATH = MODULE_DIR / "main.py"


class FakeTraCIException(Exception):
    """Stand-in for traci.TraCIException, which main.py names in an except clause."""


def build_traci_stub() -> types.ModuleType:
    """Builds a traci stub rich enough for the functions exercised here."""
    traci_stub = types.ModuleType("traci")
    traci_stub.TraCIException = FakeTraCIException

    vehicle = types.SimpleNamespace(
        colors={},
        speeds={},
        widths={},
        heights={},
        setColor=lambda veh, color: traci_stub.vehicle.colors.__setitem__(veh, color),
        getSpeed=lambda veh: traci_stub.vehicle.speeds.get(veh, 0.0),
        getWidth=lambda veh: traci_stub.vehicle.widths.get(veh, 1.8),
        getHeight=lambda veh: traci_stub.vehicle.heights.get(veh, 1.4),
    )
    person = types.SimpleNamespace(
        speeds={},
        getSpeed=lambda ped: traci_stub.person.speeds.get(ped, 0.0),
    )
    lane = types.SimpleNamespace(
        lengths={},
        occupancies={},
        getLength=lambda lane_id: traci_stub.lane.lengths.get(lane_id, 7.0),
        getLastStepOccupancy=lambda lane_id: traci_stub.lane.occupancies.get(lane_id, 0.0),
    )
    traci_stub.vehicle = vehicle
    traci_stub.person = person
    traci_stub.lane = lane
    return traci_stub


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

    sys.modules["traci"] = build_traci_stub()

    xml2csv_stub = types.ModuleType("xml2csvSWA")
    xml2csv_stub.pythonPath = "python"
    sys.modules["xml2csvSWA"] = xml2csv_stub

    spec = importlib.util.spec_from_file_location("pedsumo_main", MAIN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MainLogicTestBase(unittest.TestCase):
    # loaded once for the whole class: importing main.py is the expensive part of the suite
    @classmethod
    def setUpClass(cls):
        cls.main = load_main_module()
        cls.cf = cls.main.cf
        cls.traci = sys.modules["traci"]

    def setUp(self):
        self.main = type(self).main
        self.cf = type(self).cf
        self.traci = type(self).traci
        self._saved_config = {}
        self._saved_ped_attributes = dict(self.cf.ped_attribute_dict)
        self._saved_results_folder = self.main.results_folder_for_next_sim

    def tearDown(self):
        for key, value in self._saved_config.items():
            setattr(self.cf, key, value)
        self.cf.ped_attribute_dict.clear()
        self.cf.ped_attribute_dict.update(self._saved_ped_attributes)
        self.main.results_folder_for_next_sim = self._saved_results_folder

    def set_config(self, **values):
        """Sets config values for the duration of one test, restoring them in tearDown."""
        for key, value in values.items():
            if key not in self._saved_config:
                self._saved_config[key] = getattr(self.cf, key)
            setattr(self.cf, key, value)


class DefianceFactorTests(MainLogicTestBase):
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

    def test_ehmi_defiance_factor_distinguishes_equipped_vehicles(self):
        self.assertEqual(self.main.get_ehmi_defiance_factor("", {"veh0"}), 1.0)
        self.assertEqual(self.main.get_ehmi_defiance_factor("veh1", {"veh0"}), 1.0)
        self.assertEqual(
            self.main.get_ehmi_defiance_factor("veh0", {"veh0"}), self.cf.ehmi_dfv
        )

    def test_child_present_defiance_factor_is_independent_of_iteration_order(self):
        # two children with different genders at the same crossing: the returned factor must not
        # depend on which one a set happens to yield first
        self.cf.ped_attribute_dict.clear()
        self.cf.ped_attribute_dict["ped_a"] = {"age": 10, "gender": "male"}
        self.cf.ped_attribute_dict["ped_b"] = {"age": 10, "gender": "female"}
        forwards = self.main.get_child_present_defiance_factor({"ped_a", "ped_b"})
        backwards = self.main.get_child_present_defiance_factor({"ped_b", "ped_a"})
        self.assertEqual(forwards, backwards)
        # sorted() order means ped_a (male) decides
        self.assertEqual(forwards, self.cf.boy_present_dfv)

    def test_no_child_present_returns_neutral_factor(self):
        self.cf.ped_attribute_dict.clear()
        self.cf.ped_attribute_dict["adult"] = {"age": 40, "gender": "female"}
        self.assertEqual(self.main.get_child_present_defiance_factor({"adult"}), 1.0)

    def test_road_occupancy_defiance_factor_covers_low_high_and_between(self):
        self.traci.lane.occupancies = {"lane_low": 0.0, "lane_high": 0.5}
        self.assertEqual(
            self.main.get_road_occupancy_defiance_factor({"lane_low"}),
            self.cf.low_occupancy_rate_dfv,
        )
        self.assertEqual(
            self.main.get_road_occupancy_defiance_factor({"lane_high"}),
            self.cf.high_occupancy_rate_dfv,
        )
        midpoint = (self.cf.lane_low_occupancy_rate + self.cf.lane_high_occupancy_rate) / 2
        self.traci.lane.occupancies = {"lane_mid": midpoint}
        factor = self.main.get_road_occupancy_defiance_factor({"lane_mid"})
        self.assertGreater(factor, self.cf.high_occupancy_rate_dfv)
        self.assertLess(factor, self.cf.low_occupancy_rate_dfv)


class CrossingLaneDetectionTests(MainLogicTestBase):
    def test_recognises_sumo_crossing_lane_ids(self):
        for lane in (":J3_c0_0", ":1234567_c1_0", ":cluster_1009345595_1011753411_c0_0",
                     ":cluster_123_456_c12_1"):
            with self.subTest(lane=lane):
                self.assertTrue(self.main.is_crossing_lane(lane))

    def test_crossings_at_clustered_junctions_are_not_skipped(self):
        # regression test: the previous filter excluded every lane containing "cluster", which threw
        # away the crossings at junctions netconvert had merged - 1313 of 3299 crossings in the
        # bundled Ulm scenario, and 1310 of 6330 in Ingolstadt
        self.assertTrue(self.main.is_crossing_lane(":cluster_1009345595_1011753411_c0_0"))

    def test_rejects_lanes_that_are_not_crossings(self):
        for lane in (
            "E0_0",              # ordinary edge lane
            "cityroad_0",        # ordinary lane that merely contains the letter "c"
            ":J3_w0_0",          # walking area
            ":J3_0_0",           # internal vehicle lane
            ":cluster_123_0_0",  # internal vehicle lane at a clustered junction
            "-gneE12_1",
        ):
            with self.subTest(lane=lane):
                self.assertFalse(self.main.is_crossing_lane(lane))


class SmombieTests(MainLogicTestBase):
    def test_distraction_chance_is_age_dependent(self):
        self.cf.ped_attribute_dict.clear()
        for age in (self.cf.smombie_start_age, self.cf.smombie_peak_age, self.cf.smombie_end_age):
            self.cf.ped_attribute_dict["ped_%d" % age] = {"age": age}

        start = self.main.get_smombie_distraction_chance("ped_%d" % self.cf.smombie_start_age)
        peak = self.main.get_smombie_distraction_chance("ped_%d" % self.cf.smombie_peak_age)
        end = self.main.get_smombie_distraction_chance("ped_%d" % self.cf.smombie_end_age)

        self.assertAlmostEqual(start, self.cf.smombie_chance_at_start_age)
        self.assertAlmostEqual(peak, self.cf.smombie_chance_at_peak_age)
        self.assertAlmostEqual(end, self.cf.smombie_chance_at_end_age)
        self.assertGreater(peak, start)
        self.assertGreater(peak, end)

    def test_age_outside_the_modelled_span_falls_back_to_base_chance(self):
        self.cf.ped_attribute_dict.clear()
        self.cf.ped_attribute_dict["toddler"] = {"age": self.cf.smombie_start_age - 1}
        self.cf.ped_attribute_dict["senior"] = {"age": self.cf.smombie_end_age + 1}
        self.assertEqual(
            self.main.get_smombie_distraction_chance("toddler"), self.cf.smombie_base_chance
        )
        self.assertEqual(
            self.main.get_smombie_distraction_chance("senior"), self.cf.smombie_base_chance
        )

    def test_defiance_factor_uses_the_age_dependent_chance(self):
        self.cf.ped_attribute_dict.clear()
        self.cf.ped_attribute_dict["teen"] = {"age": self.cf.smombie_peak_age}
        # a chance of 1.0 must always distract, a chance of 0.0 never
        self.set_config(
            smombie_chance_at_peak_age=1.0,
            smombie_base_chance=1.0,
            smombie_chance_at_start_age=1.0,
        )
        self.assertEqual(self.main.get_smombie_defiance_factor("teen"), self.cf.smombie_dfv)
        self.set_config(
            smombie_chance_at_peak_age=0.0,
            smombie_base_chance=0.0,
            smombie_chance_at_start_age=0.0,
        )
        self.assertEqual(self.main.get_smombie_defiance_factor("teen"), 1.0)


class PromptTests(MainLogicTestBase):
    def build_prompt(self, closest_vehicle, ehmi_set):
        self.cf.ped_attribute_dict.clear()
        self.cf.ped_attribute_dict["ped0"] = {"age": 30, "gender": "female"}
        self.traci.lane.lengths = {"crossing0_0": 7.0}
        self.traci.vehicle.widths = {closest_vehicle: 1.8}
        self.traci.vehicle.heights = {closest_vehicle: 1.4}
        return self.main.generate_prompt_for_crossing_decision(
            "ped0",
            {"ped0": 5},
            {"ped0"},
            "crossing0",
            closest_vehicle,
            1,
            4.0,
            ehmi_set,
        )

    def test_prompt_says_the_vehicle_has_an_interface_only_when_it_does(self):
        # regression test: these two branches were swapped, so every LLM prompt described the
        # eHMI state of the approaching vehicle as the exact opposite of the simulated state
        with_ehmi = self.build_prompt("veh0", {"veh0"})
        without_ehmi = self.build_prompt("veh0", set())
        self.assertIn("has an interface attached", with_ehmi)
        self.assertNotIn("does not have an interface attached", with_ehmi)
        self.assertIn("does not have an interface attached", without_ehmi)

    def test_prompt_reports_walking_state_correctly(self):
        self.traci.person.speeds = {"ped0": 0.0}
        self.assertIn("You are not walking.", self.build_prompt("veh0", set()))
        self.traci.person.speeds = {"ped0": 1.4}
        self.assertIn("You are walking.", self.build_prompt("veh0", set()))
        self.traci.person.speeds = {}


class DeterminismTests(MainLogicTestBase):
    def run_assignment(self, vehicles, pedestrians, seed):
        avs = set()
        ehmi = set()
        random.seed(seed)
        self.cf.ped_attribute_dict.clear()
        self.main.adjust_newly_added_entities(
            vehicles, set(), avs, ehmi, pedestrians, set()
        )
        return sorted(avs), sorted(ehmi), dict(self.cf.ped_attribute_dict)

    def test_vehicle_and_pedestrian_assignment_is_reproducible_for_a_fixed_seed(self):
        # regression test: the assignment iterated over a set, and CPython randomises string hashing
        # per process, so the same seed produced different AVs between runs. Presenting the two
        # inputs in different orders stands in for that per-process variation.
        vehicles_a = ["veh0", "veh1", "veh2", "veh3", "veh4", "veh5"]
        vehicles_b = list(reversed(vehicles_a))
        peds_a = ["ped0", "ped1", "ped2", "ped3"]
        peds_b = list(reversed(peds_a))

        self.set_config(av_density=0.5, ehmi_density=0.5)
        self.main.av_density = 0.5
        self.main.ehmi_density = 0.5

        first = self.run_assignment(vehicles_a, peds_a, seed=42)
        second = self.run_assignment(vehicles_b, peds_b, seed=42)
        self.assertEqual(first, second)

    def test_different_seeds_produce_different_realisations(self):
        # the point of --seed: identical parameters must still allow independent replications
        vehicles = ["veh%d" % i for i in range(40)]
        self.set_config(av_density=0.5, ehmi_density=0.5)
        self.main.av_density = 0.5
        self.main.ehmi_density = 0.5
        self.assertNotEqual(
            self.run_assignment(vehicles, [], seed=1),
            self.run_assignment(vehicles, [], seed=2),
        )


class ConfigAndCliTests(MainLogicTestBase):
    def test_get_current_simulation_name_matches_active_scenario(self):
        self.set_config(
            scenarios=[["ScenarioA", "/tmp/a.sumocfg"], ["ScenarioB", "/tmp/b.sumocfg"]],
            sumocfgPath="/tmp/b.sumocfg",
        )
        self.assertEqual(self.main.get_current_simulation_name(), "ScenarioB")
        self.set_config(sumocfgPath="/tmp/unknown.sumocfg")
        self.assertEqual(self.main.get_current_simulation_name(), "")

    def test_generate_start_config_contains_selected_outputs_and_thread_option(self):
        results_folder = os.path.join("tmp", "results")
        self.set_config(
            sumocfgPath=os.path.join("tmp", "example.sumocfg"),
            outputFilesActive=True,
            statsOutput=True,
            tripinfoOutput=True,
            personsummaryOutput=False,
            summaryOutput=False,
            vehroutesOutput=False,
            fcdOutput=False,
            fullOutput=False,
            queueOutput=False,
            edgedataOutput=False,
            lanedataOutput=False,
            lanechangeOutput=False,
            amitranOutput=False,
            ndumpOutput=False,
            linkOutput=False,
            personinfoOutput=False,
            multithreading_rerouting_active=True,
            rerouting_threads=4,
            multithreading_routing_active=False,
        )
        self.main.results_folder_for_next_sim = results_folder

        config = self.main.generate_start_config("sumo")
        self.assertEqual(config[0:3], ["sumo", "-c", os.path.join("tmp", "example.sumocfg")])
        self.assertIn("--statistic-output", config)
        # os.path.join, not a hardcoded "/": this assertion failed on Windows
        self.assertIn(os.path.join(results_folder, "stats.xml"), config)
        self.assertIn("--tripinfo-output", config)
        self.assertIn(os.path.join(results_folder, "tripinfo.xml"), config)
        self.assertIn("--device.rerouting.threads", config)
        self.assertIn("4", config)
        self.assertEqual(config[-2:], ["--start", "--quit-on-end"])

    def test_disabling_output_files_omits_every_output_flag(self):
        self.set_config(outputFilesActive=False, multithreading_rerouting_active=False,
                        multithreading_routing_active=False,
                        sumocfgPath=os.path.join("tmp", "example.sumocfg"))
        self.main.results_folder_for_next_sim = os.path.join("tmp", "results")
        config = self.main.generate_start_config("sumo")
        self.assertEqual(config, ["sumo", "-c", os.path.join("tmp", "example.sumocfg"),
                                  "--start", "--quit-on-end"])

    def test_float_range_matches_values_inside_interval(self):
        float_range = self.main.FloatRange(0.0, 1.0)
        self.assertTrue(0.0 in float_range)
        self.assertTrue(0.5 in float_range)
        self.assertTrue(1.0 in float_range)
        self.assertFalse(-0.1 in float_range)
        self.assertEqual(repr(float_range), "[0.0,1.0]")

    def test_every_configured_scenario_points_at_an_existing_sumocfg(self):
        # catches a scenario entry whose path was renamed or never shipped
        for name, relative_path in self.cf.scenarios:
            with self.subTest(scenario=name):
                # paths in config.py are relative to the SumoWithAVs working directory
                resolved = (MODULE_DIR / relative_path).resolve()
                self.assertTrue(
                    resolved.is_file(),
                    "scenario %s points at missing file %s" % (name, resolved),
                )

    def test_seed_option_defaults_to_config_and_accepts_an_override(self):
        argv = sys.argv
        try:
            sys.argv = ["main.py", "--nogui"]
            self.assertEqual(self.main.get_options().seed, self.cf.random_seed)
            sys.argv = ["main.py", "--nogui", "--seed", "7"]
            self.assertEqual(self.main.get_options().seed, 7)
        finally:
            sys.argv = argv


class OptionalLlmDependencyTests(MainLogicTestBase):
    def test_missing_transformers_raises_an_actionable_import_error(self):
        # regression test: the availability check used to run after transformers was already called,
        # so a missing dependency surfaced as "NoneType is not callable" instead of this message
        find_spec = importlib.util.find_spec
        importlib.util.find_spec = lambda name, *a, **kw: (
            None if name == "transformers" else find_spec(name, *a, **kw)
        )
        try:
            with self.assertRaises(ImportError) as caught:
                self.main.load_transformers_pipeline("declare-lab/flan-alpaca-large")
            self.assertIn("requirements_llm.txt", str(caught.exception))
        finally:
            importlib.util.find_spec = find_spec

    def test_transformers_is_not_imported_unless_the_llm_method_is_selected(self):
        # importing transformers costs tens of seconds and pulls in torch; the default "normal"
        # method must not pay that cost
        self.assertNotIn("transformers", sys.modules)


if __name__ == "__main__":
    unittest.main()
