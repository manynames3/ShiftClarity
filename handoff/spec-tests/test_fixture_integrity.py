"""Handoff-integrity tests, not an implemented application engine. Standard library only."""
import unittest, json, csv, re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))
D = Decimal
class FixtureIntegrity(unittest.TestCase):
    def setUp(self):
        self.work = read("data/synthetic/work_records.json")
        self.lines = read("data/synthetic/invoice_lines.json")
        self.rules = read("data/synthetic/rate_rules.json")
        self.expected = read("data/synthetic/expected_results.json")
    def test_input_counts_and_minutes(self):
        self.assertEqual(len(self.work), 14)
        self.assertEqual(sum(w["worked_minutes"] for w in self.work), 8880)
        self.assertEqual(len(self.lines), 10)
        self.assertEqual(len(self.rules), 3)
    def test_unique_ids(self):
        for rows in [self.work, self.lines, self.rules]:
            self.assertEqual(len(rows), len({x["id"] for x in rows}))
    def test_source_references_exist(self):
        work_ids = {w["id"] for w in self.work}
        for line in self.lines:
            self.assertTrue(set(line["shift_ids"]).issubset(work_ids))
        excerpt_ids = {x["id"] for x in read("data/synthetic/source_excerpts.json")}
        for rule in self.rules:
            self.assertIn(rule["source_excerpt_id"], excerpt_ids)
    def test_coverage_is_exact_partition(self):
        cats = self.expected["coverage"]["categories"]
        ids = [s for v in cats.values() for s in v["shift_ids"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {w["id"] for w in self.work})
        self.assertEqual(sum(v["records"] for v in cats.values()), 14)
        self.assertEqual(sum(v["minutes"] for v in cats.values()), 8880)
        work_by_id = {w["id"]: w for w in self.work}
        for v in cats.values():
            self.assertEqual(v["records"], len(v["shift_ids"]))
            self.assertEqual(v["minutes"], sum(work_by_id[s]["worked_minutes"] for s in v["shift_ids"]))
    def test_evaluated_denominators(self):
        c = self.expected["coverage"]; cats = c["categories"]
        self.assertEqual(sum(cats[k]["records"] for k in ["evaluated_aligned","evaluated_flagged"]), c["evaluated_records"])
        self.assertEqual(sum(cats[k]["minutes"] for k in ["evaluated_aligned","evaluated_flagged"]), c["evaluated_minutes"])
        self.assertEqual(c["evaluated_minutes"], 7440)
    def test_financial_oracle_math(self):
        for finding in self.expected["findings"]:
            self.assertEqual(D(finding["expected_amount"]) - D(finding["invoiced_amount"]), D(finding["discrepancy_amount"]))
        self.assertEqual(D(40) * D("65") - D("2400"), D("200"))
        self.assertEqual(D(24) * D("65"), D("1560"))
    def test_posted_control_total(self):
        total = sum(D(x["amount"]) for x in self.lines if x["state"] == "posted")
        self.assertEqual(total, D("6240.00"))
        self.assertEqual(D(self.expected["controls"]["supported_expected_total"]) - total, D("1760.00"))
    def test_credit_rebill_control(self):
        chain = [x for x in self.lines if x["chain_id"] == "CHAIN-001"]
        self.assertEqual(sum(D(x["amount"]) for x in chain), D("780.00"))
        self.assertTrue(any(D(x["amount"]) < 0 for x in chain))
    def test_aggregate_control(self):
        line = next(x for x in self.lines if x["id"] == "LINE-005")
        self.assertEqual(len(line["shift_ids"]), 3)
        self.assertEqual(D(line["amount"]) / 3, D("520.00"))
        self.assertEqual(line["minutes"], 1440)
    def test_late_entry_is_deliberate(self):
        w = next(w for w in self.work if w["id"] == "S010")
        self.assertEqual(w["service_date"], "2026-10-04")
        self.assertTrue(w["recorded_at"].startswith("2026-10-07"))
    def test_unknown_values_not_zero(self):
        for gap in self.expected["coverage_tasks"]:
            self.assertIsNone(gap["amount"])
        self.assertIsNone(self.expected["financial_totals"]["collected_amount"])
    def test_no_self_approved_rules(self):
        for rule in self.rules:
            self.assertNotEqual(rule["author_id"], rule["approver_id"])
    def test_draft_outside_canonical_run(self):
        draft = read("data/synthetic/draft_rule.json")
        self.assertFalse(draft["included_in_RUN_001"])
        self.assertEqual(draft["state"], "pending_approval")
        self.assertEqual(draft["effective_from"], "2026-10-13")
    def test_golden_cases_numbered_and_money(self):
        cases = read("spec-tests/golden_cases.json")
        self.assertEqual(len(cases), 20)
        self.assertEqual(len({c["id"] for c in cases}), 20)
        self.assertEqual((D(61) / D(60) * D("65")).quantize(D(".01"), rounding=ROUND_HALF_UP), D("66.08"))
    def test_scope_lock(self):
        scope = read("contracts/scope-lock.json")
        self.assertEqual(scope["product"], "ShiftClarity")
        self.assertEqual(scope["authorized_stage"], "LOCAL_SYNTHETIC_DEMO")
        for flag in ["real_data_allowed","paid_api_calls_allowed","live_integrations_allowed","deployment_allowed","source_system_writes_allowed","outbound_messages_allowed"]:
            self.assertFalse(scope[flag])
    def test_brand_consistency(self):
        t = read("brand/tokens.json")
        self.assertEqual(t["color"]["ink"], "#142333")
        self.assertEqual(t["color"]["teal"], "#006C78")
        for fname in ["shiftclarity-mark.svg","shiftclarity-wordmark.svg","shiftclarity-mark-inverse.svg","shiftclarity-wordmark-inverse.svg"]:
            self.assertIn("<svg", (ROOT / "brand" / fname).read_text())
    def test_no_font_files_or_secrets(self):
        prohibited = {".ttf", ".otf", ".woff", ".woff2", ".pem", ".key"}
        self.assertEqual([str(p) for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in prohibited], [])
    def test_csv_roundtrip_counts(self):
        for name, count in [("work_records",14),("invoice_lines",10)]:
            with (ROOT / f"data/synthetic/{name}.csv").open() as f:
                self.assertEqual(len(list(csv.DictReader(f))), count)
    def test_acceptance_matrix_complete(self):
        with (ROOT / "contracts/acceptance-matrix.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([x["requirement_id"] for x in rows], [f"SC-{i:02}" for i in range(1,33)])
        self.assertTrue(all(x["implementation_status"] == "not_started" for x in rows))
    def test_reference_exists(self):
        self.assertTrue((ROOT / "reference/index.html").exists())
        self.assertTrue((ROOT / "START_HERE_CODEX.md").exists())
        self.assertIn("Every shift. Clearly aligned.", (ROOT / "README.md").read_text())

if __name__ == "__main__":
    unittest.main()
