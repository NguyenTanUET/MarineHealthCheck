
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C2 (Branch/Decision) tests for the marine health classifier.
"""

from typing import Dict, Any, List, Tuple
import math
import json

def classify_marine_health(temp_c: float, sal_psu: float, do_mgL: float, nh3_mgL: float) -> Dict[str, Any]:
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
        return "moderate"
    def bucket_nh3(a: float) -> str:
        if a <= 0.02:
            return "safe"
        if a > 0.05:
            return "high"
        return "moderate"

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
    return {"risk": risk, "factors": [k for k,v in factors.items() if v != "safe"]}

DECISIONS = [
    "VAL_temp_gt0","VAL_sal_gt0","VAL_do_gt0","VAL_nh3_ge0",
    "T_safe_24_28","T_moderate_22_24_or_28_30",
    "S_safe_30_35","S_moderate_28_30_or_35_37",
    "DO_safe_ge6","DO_high_lt4",
    "NH3_safe_le_0_02","NH3_high_gt_0_05",
    "AGG_has_high","AGG_has_moderate",
]

def eval_decisions(temp_c: float, sal_psu: float, do_mgL: float, nh3_mgL: float):
    d = {}
    d["VAL_temp_gt0"] = (temp_c > 0)
    d["VAL_sal_gt0"]  = (sal_psu > 0)
    d["VAL_do_gt0"]   = (do_mgL > 0)
    d["VAL_nh3_ge0"]  = (nh3_mgL >= 0)
    t_safe = (24 <= temp_c <= 28)
    t_mod  = ((22 <= temp_c < 24) or (28 < temp_c <= 30))
    s_safe = (30 <= sal_psu <= 35)
    s_mod  = ((28 <= sal_psu < 30) or (35 < sal_psu <= 37))
    do_safe = (do_mgL >= 6)
    do_high = (do_mgL < 4)
    nh3_safe = (nh3_mgL <= 0.02)
    nh3_high = (nh3_mgL > 0.05)
    d["T_safe_24_28"] = t_safe
    d["T_moderate_22_24_or_28_30"] = t_mod
    d["S_safe_30_35"] = s_safe
    d["S_moderate_28_30_or_35_37"] = s_mod
    d["DO_safe_ge6"] = do_safe
    d["DO_high_lt4"] = do_high
    d["NH3_safe_le_0_02"] = nh3_safe
    d["NH3_high_gt_0_05"] = nh3_high
    any_high = ((not t_safe and not t_mod) or (not s_safe and not s_mod) or do_high or (not nh3_safe and nh3_high))
    any_mod = (not any_high) and (t_mod or s_mod or (not do_safe and not do_high) or (not nh3_safe and not nh3_high))
    d["AGG_has_high"] = any_high
    d["AGG_has_moderate"] = any_mod
    return d

TESTS = [
    ("ALL_SAFE", dict(temp_c=26.0, sal_psu=32.0, do_mgL=7.0,  nh3_mgL=0.005), "low"),
    ("TEMP_MOD", dict(temp_c=22.5, sal_psu=32.0, do_mgL=7.0,  nh3_mgL=0.005), "medium"),
    ("TEMP_HIGH",dict(temp_c=20.0, sal_psu=32.0, do_mgL=7.0,  nh3_mgL=0.005), "high"),
    ("SAL_MOD",  dict(temp_c=26.0, sal_psu=29.0, do_mgL=7.0,  nh3_mgL=0.005), "medium"),
    ("SAL_HIGH", dict(temp_c=26.0, sal_psu=27.0, do_mgL=7.0,  nh3_mgL=0.005), "high"),
    ("DO_MOD",   dict(temp_c=26.0, sal_psu=32.0, do_mgL=5.0,  nh3_mgL=0.005), "medium"),
    ("DO_HIGH",  dict(temp_c=26.0, sal_psu=32.0, do_mgL=3.0,  nh3_mgL=0.005), "high"),
    ("NH3_MOD",  dict(temp_c=26.0, sal_psu=32.0, do_mgL=7.0,  nh3_mgL=0.03),  "medium"),
    ("NH3_HIGH", dict(temp_c=26.0, sal_psu=32.0, do_mgL=7.0,  nh3_mgL=0.06),  "high"),
]

ERROR_TESTS = [
    ("VAL_temp_le0", dict(temp_c=0.0, sal_psu=32.0, do_mgL=7.0, nh3_mgL=0.0)),
    ("VAL_sal_le0",  dict(temp_c=26.0, sal_psu=0.0, do_mgL=7.0, nh3_mgL=0.0)),
    ("VAL_do_le0",   dict(temp_c=26.0, sal_psu=32.0, do_mgL=0.0, nh3_mgL=0.0)),
    ("VAL_nh3_lt0",  dict(temp_c=26.0, sal_psu=32.0, do_mgL=7.0, nh3_mgL=-0.001)),
]

def main():
    cov = {name: set() for name in DECISIONS}
    passed = 0

    print("[RUN] C2 branch suite")
    for name, inp, expected in TESTS:
        out = classify_marine_health(**inp)
        ok = (out["risk"] == expected)
        passed += int(ok)
        dec = eval_decisions(**inp)
        for k,v in dec.items():
            cov[k].add(bool(v))
        print(f"- {name:10s} inputs={json.dumps(inp)} => risk={out['risk']} expected={expected} [{'PASS' if ok else 'FAIL'}]")

    for name, inp in ERROR_TESTS:
        try:
            classify_marine_health(**inp)
            ok = False
        except ValueError:
            ok = True
        passed += int(ok)
        dec = eval_decisions(**inp)
        for k,v in dec.items():
            cov[k].add(bool(v))
        print(f"- {name:10s} inputs={json.dumps(inp)} => raises ValueError [{'PASS' if ok else 'FAIL'}]")

    total = len(TESTS) + len(ERROR_TESTS)
    print(f"\n[SUMMARY] {passed}/{total} tests passed.")
    print("\n[DECISION COVERAGE — C2]\n(decision : seen True?  seen False?)")
    for name in DECISIONS:
        tf = cov[name]
        print(f"  {name:28s}:  {'T' if True in tf else '-'}       {'F' if False in tf else '-'}")

    both = [n for n in DECISIONS if True in cov[n] and False in cov[n]]
    missing = [n for n in DECISIONS if n not in both]
    if not missing:
        print("\n[RESULT] C2 achieved for all tracked decisions.")
    else:
        print("\n[RESULT] C2 NOT fully achieved for:", ", ".join(missing))

if __name__ == "__main__":
    main()
