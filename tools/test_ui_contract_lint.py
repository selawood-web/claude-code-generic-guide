#!/usr/bin/env python3
"""Tests for tools/ui_contract_lint.py — each rule fails on its defect and on nothing else."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import ui_contract_lint as L  # noqa: E402

EXAMPLE = os.path.join(ROOT, ".claude", "skills", "ui-contract", "example-contract.json")


def base() -> dict:
    with open(EXAMPLE, encoding="utf-8") as fh:
        return json.load(fh)


def codes(data, severity=None) -> list[str]:
    return [f.code for f in L.lint(data) if severity is None or f.severity == severity]


class ExampleIsClean(unittest.TestCase):
    def test_shipped_example_has_no_findings(self):
        self.assertEqual(L.lint(base()), [])

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, os.path.join(HERE, "ui_contract_lint.py"), EXAMPLE],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        missing = subprocess.run([sys.executable, os.path.join(HERE, "ui_contract_lint.py"), "/nonexistent.json"],
                                 capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)


class Structure(unittest.TestCase):
    def test_not_an_object(self):
        self.assertIn("UC01", codes([]))

    def test_missing_section(self):
        d = base()
        del d["surfaces"]
        self.assertIn("UC01", codes(d))

    def test_bad_policy(self):
        d = base()
        d["policy"]["off_context"] = "faded"
        self.assertIn("UC01", codes(d))


class SameLogicOtherOutput(unittest.TestCase):
    def test_profile_missing_a_layer(self):
        d = base()
        del d["boards"]["manufacture"]["profile"]["layers"]["walls"]
        self.assertIn("UC03", codes(d))

    def test_profile_inventing_a_measurement(self):
        d = base()
        d["boards"]["presentation"]["profile"]["measurements"]["perspective-depth"] = "show"
        self.assertIn("UC03", codes(d))

    def test_board_without_output(self):
        d = base()
        del d["boards"]["installation"]["profile"]["output"]
        self.assertIn("UC03", codes(d))

    def test_context_on_unknown_board(self):
        d = base()
        d["contexts"]["quote.idle"] = {"board": "quote", "label": "Quote"}
        self.assertIn("UC02", codes(d))

    def test_behaviour_that_varies_by_board(self):
        d = base()
        d["commands"]["dimension.add"]["does"] = {"design": "adds a dimension", "manufacture": "adds a part size"}
        self.assertIn("UC14", codes(d))


class OneHome(unittest.TestCase):
    def test_unknown_home(self):
        d = base()
        d["commands"]["draw.wall"]["home"] = "ribbon.walls"
        self.assertIn("UC04", codes(d))

    def test_second_entry_without_why(self):
        d = base()
        d["commands"]["edit.move"]["also"][0]["why"] = ""
        self.assertIn("UC04", codes(d))

    def test_second_entry_repeating_home(self):
        d = base()
        d["commands"]["edit.move"]["also"].append({"surface": "toolbar.edit", "why": "again"})
        self.assertIn("UC04", codes(d))

    def test_scattered_command_is_a_warning(self):
        d = base()
        d["surfaces"]["panel.a"] = {"label": "A", "contexts": ["*"]}
        d["surfaces"]["panel.b"] = {"label": "B", "contexts": ["*"]}
        d["commands"]["dimension.add"]["also"] = [
            {"surface": "panel.a", "why": "x"}, {"surface": "panel.b", "why": "y"},
            {"surface": "panel.layers", "why": "z"}]
        self.assertEqual(codes(d, "warning"), ["UC11"])
        self.assertEqual(codes(d, "error"), [])

    def test_unreachable_command(self):
        d = base()
        d["commands"]["edit.move"]["enabled"] = ["*"]
        d["commands"]["edit.move"]["disabled"] = {}
        self.assertIn("UC07", codes(d))


class OneNameOneMeaning(unittest.TestCase):
    def test_duplicate_label(self):
        d = base()
        d["commands"]["output.export"]["label"] = "cut list"
        self.assertIn("UC05", codes(d))

    def test_shortcut_clash_in_shared_context(self):
        d = base()
        d["commands"]["place.cabinet"]["shortcut"] = "W"
        self.assertIn("UC06", codes(d))

    def test_same_shortcut_in_disjoint_contexts_is_fine(self):
        d = base()
        d["commands"]["manufacture.cutlist"]["shortcut"] = "W"
        self.assertNotIn("UC06", codes(d))


class OnlyWhatIsRelevant(unittest.TestCase):
    def test_disabled_without_reason(self):
        d = base()
        d["commands"]["edit.move"]["disabled"]["design.idle"] = " "
        self.assertIn("UC12", codes(d))

    def test_undeclared_state_inside_own_board(self):
        d = base()
        d["commands"]["edit.move"]["disabled"] = {}
        self.assertIn("UC12", codes(d))

    def test_pattern_matching_nothing(self):
        d = base()
        d["commands"]["draw.wall"]["enabled"] = ["desing.*"]
        self.assertIn("UC08", codes(d))

    def test_two_states_in_one_context(self):
        d = base()
        d["commands"]["draw.wall"]["disabled"]["design.idle"] = "No"
        self.assertIn("UC13", codes(d))

    def test_overloaded_context(self):
        d = base()
        d["policy"]["max_enabled_per_context"] = 4
        self.assertIn("UC10", codes(d, "warning"))

    def test_dead_end_context(self):
        d = base()
        d["boards"]["review"] = copy.deepcopy(d["boards"]["design"])
        d["contexts"]["review.idle"] = {"board": "review", "label": "Review"}
        for cmd in d["commands"].values():
            cmd["enabled"] = [p for p in cmd["enabled"] if p != "*"] or ["design.*"]
        found = L.lint(d)
        self.assertIn("UC09", [f.code for f in found if f.where == "contexts.review.idle"])

    def test_off_board_reason_is_generated(self):
        d = base()
        state = L.Contract(d).state(d["commands"]["manufacture.cutlist"], "design.idle")
        self.assertEqual(state, L.State("disabled", "Available in Manufacture"))

    def test_hidden_policy(self):
        d = base()
        d["policy"]["off_context"] = "hidden"
        state = L.Contract(d).state(d["commands"]["manufacture.cutlist"], "design.idle")
        self.assertEqual(state.kind, "hidden")
        self.assertEqual(L.lint(d), [])


class Matrix(unittest.TestCase):
    def test_matrix_rows_and_totals(self):
        out = L.matrix(base())
        self.assertIn("| edit.move | ○ | ● |", out)
        self.assertIn("| **enabled** | 6 | 7 | 5 | 5 | 5 |", out)

    def test_lint_does_not_mutate_input(self):
        d = base()
        before = copy.deepcopy(d)
        L.lint(d)
        self.assertEqual(d, before)


if __name__ == "__main__":
    unittest.main()
