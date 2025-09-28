#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aquatic Biology Black-Box Testing Demo
- System Under Test (SUT): classify_marine_health(temp_c, sal_psu, do_mgL, nh3_mgL)
- Two black-box techniques:
    (1) Decision Table-based tests (selected representative cases)
    (2) Boundary Value tests for key thresholds
Outputs:
- Prints unittest results.
- Writes a CSV "decision_table_marine_health.csv" with columns:
  ID, Case, Inputs, Expected Output, Actual Output, Result
"""

from typing import Dict, Any, List, Dict as Dct
import math
import csv
import unittest
import json

# ---------- System Under Test ----------
def classify_marine_health(temp_c: float, sal_psu: float, do_mgL: float, nh3_mgL: float) -> Dict[str, Any]:
    """
    Classify marine fish health risk for a tropical marine aquarium (black-box).
    """
    # Validation
    for name, val in [('temp_c', temp_c), ('sal_psu', sal_psu), ('do_mgL', do_mgL), ('nh3_mgL', nh3_mgL)]:
        if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
            raise ValueError(f"{name} must be a finite number.")
    if temp_c <= 0 or sal_psu <= 0 or do_mgL <= 0 or nh3_mgL < 0:
        raise ValueError("Invalid physical ranges.")

    def bucket_temp(t: float) -> str:
        if 24 <= t <= 28:
            return "safe"
        if (22 <= t < 24) or (28 < t <= 30):
            return "moderate"
        return "high"

    def bucket_sal(s: float) -> str:
        if 30 <= s <= 35:
            return "safe"
        if (28 <= s < 30) or (35 < s <= 37):
            return "moderate"
        return "high"

    def bucket_do(o: float) -> str:
        if o >= 6:
            return "safe"
        if o < 4:
            return "high"
        return "moderate"  # 4–<6

    def bucket_nh3(a: float) -> str:
        if a <= 0.02:
            return "safe"
        if a > 0.05:
            return "high"
        return "moderate"  # (0.02, 0.05]

    factors = {
        "temp": bucket_temp(temp_c),
        "salinity": bucket_sal(sal_psu),
        "dissolved_oxygen": bucket_do(do_mgL),
        "ammonia": bucket_nh3(nh3_mgL),
    }

    if "high" in factors.values():
        risk = "high"
    elif "moderate" in factors.values():
        risk = "medium"
    else:
        risk = "low"

    return {"risk": risk, "factors": [k for k, v in factors.items() if v != "safe"]}


# ---------- Decision Table (Representative Cases) ----------
def decision_table_rows() -> List[Dct[str, Any]]:
    rows: List[Dct[str, Any]] = []

    def add_case(label, t, s, o, a, expected_risk):
        rows.append({
            "Case": label, "Temp_C": t, "Sal_PSU": s, "DO_mgL": o, "NH3_mgL": a,
            "Expected_Risk": expected_risk
        })

    # All safe
    add_case("ALL_SAFE", 26.0, 32.0, 7.0, 0.005, "low")

    # Single-factor moderates
    add_case("TEMP_MOD", 22.5, 32.0, 7.0, 0.005, "medium")
    add_case("SAL_MOD", 26.0, 29.0, 7.0, 0.005, "medium")
    add_case("DO_MOD", 26.0, 32.0, 5.0, 0.005, "medium")
    add_case("NH3_MOD", 26.0, 32.0, 7.0, 0.03, "medium")

    # Single-factor highs
    add_case("TEMP_HIGH", 20.0, 32.0, 7.0, 0.005, "high")
    add_case("SAL_HIGH", 26.0, 27.0, 7.0, 0.005, "high")
    add_case("DO_HIGH", 26.0, 32.0, 3.0, 0.005, "high")
    add_case("NH3_HIGH", 26.0, 32.0, 7.0, 0.06, "high")

    # Emergency hypoxia dominance
    add_case("HYPOXIA_EMERGENCY", 26.0, 32.0, 1.5, 0.0, "high")

    # Mixed moderate + high (dominance by high)
    add_case("MIXED_HIGH_DOM", 23.0, 29.5, 3.5, 0.01, "high")

    # Multiple moderates -> medium
    add_case("MULTI_MODERATES", 23.5, 36.0, 5.5, 0.01, "medium")

    return rows


def write_decision_table_csv(path: str = "decision_table_marine_health.csv"):
    """
    Write CSV with columns:
    ID, Case, Inputs, Expected Output, Actual Output, Result
    - Inputs is a compact JSON string of the four inputs.
    - Expected Output is the expected risk level (string).
    - Actual Output is the actual risk level returned by SUT.
    - Result is 'Pass' if equal, else 'Fail'.
    """
    rows = decision_table_rows()

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Case", "Inputs", "Expected Output", "Actual Output", "Result"])
        writer.writeheader()
        for i, r in enumerate(rows, start=1):
            inputs = {
                "temp_c": r["Temp_C"],
                "sal_psu": r["Sal_PSU"],
                "do_mgL": r["DO_mgL"],
                "nh3_mgL": r["NH3_mgL"],
            }
            expected = r["Expected_Risk"]
            actual = classify_marine_health(**inputs)["risk"]
            result = "Pass" if expected == actual else "Fail"
            writer.writerow({
                "ID": i,
                "Case": r["Case"],
                "Inputs": json.dumps(inputs, ensure_ascii=False),
                "Expected Output": expected,
                "Actual Output": actual,
                "Result": result,
            })
    return path


# ---------- Unit Tests ----------
class TestDecisionTableMarine(unittest.TestCase):
    def test_decision_rows(self):
        for r in decision_table_rows():
            out = classify_marine_health(r["Temp_C"], r["Sal_PSU"], r["DO_mgL"], r["NH3_mgL"])
            self.assertEqual(out["risk"], r["Expected_Risk"], msg=f"Case {r['Case']} failed: {out}")

class TestBoundaryValuesMarine(unittest.TestCase):
    def test_temp_boundaries(self):
        self.assertEqual(classify_marine_health(24.0, 32, 7, 0.0)["risk"], "low")
        self.assertEqual(classify_marine_health(23.99, 32, 7, 0.0)["risk"], "medium")
        self.assertEqual(classify_marine_health(28.0, 32, 7, 0.0)["risk"], "low")
        self.assertEqual(classify_marine_health(28.01, 32, 7, 0.0)["risk"], "medium")
        self.assertEqual(classify_marine_health(21.9, 32, 7, 0.0)["risk"], "high")
        self.assertEqual(classify_marine_health(30.1, 32, 7, 0.0)["risk"], "high")

    def test_sal_boundaries(self):
        self.assertEqual(classify_marine_health(26, 30.0, 7, 0.0)["risk"], "low")
        self.assertEqual(classify_marine_health(26, 29.99, 7, 0.0)["risk"], "medium")
        self.assertEqual(classify_marine_health(26, 35.0, 7, 0.0)["risk"], "low")
        self.assertEqual(classify_marine_health(26, 35.01, 7, 0.0)["risk"], "medium")
        self.assertEqual(classify_marine_health(26, 27.9, 7, 0.0)["risk"], "high")
        self.assertEqual(classify_marine_health(26, 37.1, 7, 0.0)["risk"], "high")

    def test_do_boundaries(self):
        self.assertEqual(classify_marine_health(26, 32, 6.0, 0.0)["risk"], "low")
        self.assertEqual(classify_marine_health(26, 32, 5.99, 0.0)["risk"], "medium")
        self.assertEqual(classify_marine_health(26, 32, 4.0, 0.0)["risk"], "medium")
        self.assertEqual(classify_marine_health(26, 32, 3.99, 0.0)["risk"], "high")
        self.assertEqual(classify_marine_health(26, 32, 1.99, 0.0)["risk"], "high")

    def test_nh3_boundaries(self):
        self.assertEqual(classify_marine_health(26, 32, 7, 0.02)["risk"], "low")
        self.assertEqual(classify_marine_health(26, 32, 7, 0.02001)["risk"], "medium")
        self.assertEqual(classify_marine_health(26, 32, 7, 0.05)["risk"], "medium")
        self.assertEqual(classify_marine_health(26, 32, 7, 0.05001)["risk"], "high")

    def test_aggregation_rules(self):
        self.assertEqual(classify_marine_health(23.0, 29.0, 3.9, 0.04)["risk"], "high")
        self.assertEqual(classify_marine_health(23.0, 32.0, 7.0, 0.0)["risk"], "medium")
        self.assertEqual(classify_marine_health(26.0, 32.0, 7.0, 0.0)["risk"], "low")

    def test_validation(self):
        with self.assertRaises(ValueError):
            classify_marine_health(-1, 32, 7, 0.0)
        with self.assertRaises(ValueError):
            classify_marine_health(26, -1, 7, 0.0)
        with self.assertRaises(ValueError):
            classify_marine_health(26, 32, 0, 0.0)
        with self.assertRaises(ValueError):
            classify_marine_health(26, 32, 7, -0.001)
        with self.assertRaises(ValueError):
            classify_marine_health(float("nan"), 32, 7, 0.0)

# ---------- Boundary Test Case Enumeration & CSV ----------
def boundary_cases_rows():
    """
    Return a list of boundary test cases with expected risks.
    Each row contains: Case, Temp_C, Sal_PSU, DO_mgL, NH3_mgL, Expected_Risk
    """
    rows = []
    def add(label, t, s, o, a, exp):
        rows.append({"Case": label, "Temp_C": t, "Sal_PSU": s, "DO_mgL": o, "NH3_mgL": a, "Expected_Risk": exp})

    # Temperature boundaries
    add("TEMP_SAFE_LO", 24.0, 32, 7, 0.0, "low")
    add("TEMP_BELOW_SAFE", 23.99, 32, 7, 0.0, "medium")
    add("TEMP_SAFE_HI", 28.0, 32, 7, 0.0, "low")
    add("TEMP_ABOVE_SAFE", 28.01, 32, 7, 0.0, "medium")
    add("TEMP_LOW_HIGH", 21.9, 32, 7, 0.0, "high")
    add("TEMP_HIGH_HIGH", 30.1, 32, 7, 0.0, "high")

    # Salinity boundaries
    add("SAL_SAFE_LO", 26, 30.0, 7, 0.0, "low")
    add("SAL_BELOW_SAFE", 26, 29.99, 7, 0.0, "medium")
    add("SAL_SAFE_HI", 26, 35.0, 7, 0.0, "low")
    add("SAL_ABOVE_SAFE", 26, 35.01, 7, 0.0, "medium")
    add("SAL_LOW_HIGH", 26, 27.9, 7, 0.0, "high")
    add("SAL_HIGH_HIGH", 26, 37.1, 7, 0.0, "high")

    # Dissolved Oxygen boundaries
    add("DO_SAFE", 26, 32, 6.0, 0.0, "low")
    add("DO_MOD_BELOW_SAFE", 26, 32, 5.99, 0.0, "medium")
    add("DO_MOD_EDGE", 26, 32, 4.0, 0.0, "medium")
    add("DO_HIGH", 26, 32, 3.99, 0.0, "high")
    add("DO_EMERGENCY", 26, 32, 1.99, 0.0, "high")

    # Ammonia boundaries
    add("NH3_SAFE", 26, 32, 7, 0.02, "low")
    add("NH3_MOD_BELOW_HIGH", 26, 32, 7, 0.02001, "medium")
    add("NH3_MOD_EDGE", 26, 32, 7, 0.05, "medium")
    add("NH3_HIGH", 26, 32, 7, 0.05001, "high")

    # Aggregation checks
    add("AGGR_HIGH_DOM", 23.0, 29.0, 3.9, 0.04, "high")
    add("AGGR_ANY_MOD", 23.0, 32.0, 7.0, 0.0, "medium")
    add("AGGR_ALL_SAFE", 26.0, 32.0, 7.0, 0.0, "low")
    return rows


def write_boundary_csv(path: str = "boundary_tests_marine_health.csv"):
    """
    Write CSV with columns:
    ID, Case, Inputs, Expected Output, Actual Output, Result
    for boundary test cases.
    """
    rows = boundary_cases_rows()
    import json, csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Case", "Inputs", "Expected Output", "Actual Output", "Result"])
        writer.writeheader()
        for i, r in enumerate(rows, start=1):
            inputs = {
                "temp_c": r["Temp_C"],
                "sal_psu": r["Sal_PSU"],
                "do_mgL": r["DO_mgL"],
                "nh3_mgL": r["NH3_mgL"],
            }
            expected = r["Expected_Risk"]
            actual = classify_marine_health(**inputs)["risk"]
            result = "Pass" if expected == actual else "Fail"
            writer.writerow({
                "ID": i,
                "Case": r["Case"],
                "Inputs": json.dumps(inputs, ensure_ascii=False),
                "Expected Output": expected,
                "Actual Output": actual,
                "Result": result,
            })
    return path


def main():
    # Write decision table CSV alongside the script when run directly
    csv_path_decision_table = write_decision_table_csv("decision_table_marine_health.csv")
    print(f"[INFO] Wrote decision table: {csv_path_decision_table}")
    csv_path_boundary = write_boundary_csv("boundary_tests_marine_health.csv")
    print(f"[INFO] Wrote decision table: {csv_path_boundary}")

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDecisionTableMarine)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestBoundaryValuesMarine)
    alltests = unittest.TestSuite([suite, suite2])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(alltests)

    print(f"[SUMMARY] testsRun={result.testsRun}, failures={len(result.failures)}, errors={len(result.errors)}, success={result.wasSuccessful()}")

if __name__ == "__main__":
    main()

