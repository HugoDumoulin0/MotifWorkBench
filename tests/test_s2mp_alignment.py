import importlib.util
import itertools
import math
from pathlib import Path
import random
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ("MWB_macOS", "MWB_Linux", "MWB_Win")
A = [{44, 785}, {44}, {5}, {56}, {44}]
B = [{44, 785}, {44, 155}, {5}, {56}, {44}]


def load_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = {
            platform: load_source(platform + "_s2mp", ROOT / platform / "src/mesure_S2MP.py")
            for platform in PLATFORMS
        }

    def assert_valid_alignment(self, module, left, right):
        pairs = list(module.mapping(left, right).items())
        self.assertEqual(len({j for _, j in pairs}), len(pairs))
        self.assertEqual(pairs, sorted(pairs))
        self.assertTrue(all(0 <= i < len(left) and 0 <= j < len(right) for i, j in pairs))
        self.assertTrue(all(module.weight(left[i], right[j]) > 0 for i, j in pairs))
        self.assertTrue(all(i < next_i and j < next_j for (i, j), (next_i, next_j) in zip(pairs, pairs[1:])))
        self.assertEqual(module.mapping(right, left), dict(sorted((j, i) for i, j in pairs)))
        score = module.main_simDegree(left, right)
        self.assertTrue(math.isfinite(score))
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)
        self.assertAlmostEqual(score, module.main_simDegree(right, left))

    def test_punctuation_regression_aligns_same_positions(self):
        for platform, module in self.modules.items():
            with self.subTest(platform=platform):
                self.assertEqual(module.mapping(A, B), dict(enumerate(range(5))))
                self.assertAlmostEqual(module.main_simDegree(A, B), 14 / 15)
                self.assertAlmostEqual(module.main_simDegree(B, A), 14 / 15)

    def test_repeated_identical_itemsets_are_not_reused(self):
        for platform, module in self.modules.items():
            for left, right in [([{1}] * 8, [{1}] * 3), ([{1}] * 5, [{1}] * 5), (A, A), (B, B)]:
                with self.subTest(platform=platform, left=left, right=right):
                    self.assert_valid_alignment(module, left, right)
                    if left == right:
                        self.assertEqual(module.main_simDegree(left, right), 1)

    def test_partial_mapping_and_different_lengths(self):
        for platform, module in self.modules.items():
            with self.subTest(platform=platform):
                left, right = [{9}, {1}, {2}], [{1}, {2}]
                self.assertEqual(module.mapping(left, right), {1: 0, 2: 1})
                self.assertEqual(module.GetAveWeightScore(left, right, {1: 0, 2: 1}), 1)
                self.assertAlmostEqual(module.main_simDegree(left, right), 0.8)
                self.assertAlmostEqual(module.main_simDegree([{1}], [{8}, {1}, {9}]), 0.5)
                self.assert_valid_alignment(module, left, right)

    def test_inserted_itemset_has_symmetric_spacing_penalty(self):
        for platform, module in self.modules.items():
            with self.subTest(platform=platform):
                left, right = [{1}, {2}, {3}], [{1}, {9}, {2}, {3}]
                self.assertEqual(module.mapping(left, right), {0: 0, 1: 2, 2: 3})
                self.assertAlmostEqual(module.main_simDegree(left, right), 30 / 49)
                self.assert_valid_alignment(module, left, right)

    def test_empty_disjoint_and_reversed_patterns(self):
        for platform, module in self.modules.items():
            with self.subTest(platform=platform):
                for left, right in [([], []), ([], A), (A, []), ([{1}], [{2}]), ([set()], [set()])]:
                    self.assertEqual(module.mapping(left, right), {})
                    self.assertEqual(module.main_simDegree(left, right), 0)
                self.assertAlmostEqual(module.main_simDegree([{1}, {2}, {3}], [{3}, {2}, {1}]), 1 / 3)
                with self.assertRaises(TypeError):
                    module.main_simDegree([42], [{1}])

    def test_alignment_maximizes_weight_against_exhaustive_search(self):
        alphabet = ({1}, {2}, {1, 2})
        sequences = [list(seq) for size in range(1, 4) for seq in itertools.product(alphabet, repeat=size)]
        for platform, module in self.modules.items():
            for left, right in itertools.product(sequences, repeat=2):
                optimum = 0.0
                for count in range(1, min(len(left), len(right)) + 1):
                    for left_indices in itertools.combinations(range(len(left)), count):
                        for right_indices in itertools.combinations(range(len(right)), count):
                            value = sum(module.weight(left[i], right[j]) for i, j in zip(left_indices, right_indices))
                            optimum = max(optimum, value)
                pairs = module.mapping(left, right)
                actual = sum(module.weight(left[i], right[j]) for i, j in pairs.items())
                self.assertAlmostEqual(actual, optimum, msg=f"{platform}: {left}, {right}")
                self.assert_valid_alignment(module, left, right)

    def test_random_patterns_preserve_alignment_invariants(self):
        rng = random.Random(20261030)
        patterns = [[set(rng.sample(range(5), rng.randint(1, 3))) for _ in range(rng.randint(0, 8))] for _ in range(250)]
        for platform, module in self.modules.items():
            for left, right in zip(patterns, reversed(patterns)):
                self.assert_valid_alignment(module, left, right)

    def test_numeric_lexicon_ids_do_not_change_similarity(self):
        rng = random.Random(17)
        pairs = [(
            [set(rng.sample(range(5), rng.randint(1, 3))) for _ in range(rng.randint(1, 7))],
            [set(rng.sample(range(5), rng.randint(1, 3))) for _ in range(rng.randint(1, 7))],
        ) for _ in range(300)]
        for platform, module in self.modules.items():
            for left, right in pairs:
                relabeled_left = [{4 - item for item in items} for items in left]
                relabeled_right = [{4 - item for item in items} for items in right]
                self.assertAlmostEqual(
                    module.main_simDegree(left, right),
                    module.main_simDegree(relabeled_left, relabeled_right),
                    msg=platform,
                )

    def test_original_cluster_threshold_groups_the_reported_pair(self):
        for platform, module in self.modules.items():
            with self.subTest(platform=platform), patch.dict(sys.modules, {"mesure_S2MP": module}):
                grouping = load_source(platform + "_grouping", ROOT / platform / "src/regroupement.py")
                for patterns in ([A, B], [B, A]):
                    self.assertEqual(grouping.regroupement_1(patterns), {0: {0, 1}})

    def test_worker_versions_cache_before_lookup(self):
        for platform, module in self.modules.items():
            for enabled in (True, False):
                with self.subTest(platform=platform, enabled=enabled), tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    find_existing = Mock(return_value=None)
                    create = Mock(return_value={"root": root / "new"})
                    paths = types.SimpleNamespace(
                        generate_config_id=Mock(return_value="new"),
                        create_analysis_structure=create,
                        find_existing_analysis=find_existing,
                        get_analysis_root=Mock(return_value=root / "new"),
                        get_analyses_root=Mock(return_value=root),
                        get_analysis_group_root=Mock(return_value=root / "group"),
                        resolve_analysis_subdir=Mock(),
                    )
                    dependencies = {
                        "PyQt6.QtCore": types.SimpleNamespace(QThread=object, pyqtSignal=lambda *args: None),
                        "main": types.SimpleNamespace(run_analysis=Mock(), AnalysisCancelled=RuntimeError),
                        "mesure_S2MP": module,
                        "gui.core.analysis_paths": paths,
                    }
                    with patch.dict(sys.modules, dependencies), patch.object(sys, "path", sys.path.copy()):
                        worker_module = load_source(platform + "_worker", ROOT / platform / "gui/core/worker.py")
                        config = {"internal_clustering": enabled, "internal_clustering_alignment": "old"}
                        worker = worker_module.AnalysisWorker(config)
                    looked_up = find_existing.call_args.args[1]
                    self.assertEqual(looked_up, create.call_args.args[2])
                    self.assertFalse(worker.reusing_existing)
                    if enabled:
                        self.assertEqual(looked_up["internal_clustering_alignment"], module.ALIGNMENT_VERSION)
                    else:
                        self.assertNotIn("internal_clustering_alignment", looked_up)


if __name__ == "__main__":
    unittest.main()
