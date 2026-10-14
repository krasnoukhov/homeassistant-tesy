"""Tests for keeping the card's dashboard resource (no Home Assistant needed)."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from unittest import TestCase

_PATH = (
    Path(__file__).parents[1] / "custom_components" / "tesy" / "lovelace_resource.py"
)
_SPEC = spec_from_file_location("tesy_lovelace_resource", _PATH)
res = module_from_spec(_SPEC)
sys.modules[_SPEC.name] = res  # dataclasses look the module up
_SPEC.loader.exec_module(res)

URL = "/tesy_static/tesy-boiler-card.js?v=bbbb2222"


def item(id_, url, type_="module"):
    return {"id": id_, "url": url, "type": type_}


class PlanResourceTest(TestCase):
    def test_created_when_missing(self):
        plan = res.plan_resource([item("x", "/local/other-card.js")], URL)
        self.assertTrue(plan.create)
        self.assertIsNone(plan.update_id)
        self.assertEqual(plan.foreign_urls, [])

    def test_nothing_to_do_when_current(self):
        plan = res.plan_resource([item("a", URL)], URL)
        self.assertFalse(plan.changes)

    def test_new_hash_updates_the_existing_entry(self):
        plan = res.plan_resource(
            [item("a", "/tesy_static/tesy-boiler-card.js?v=aaaa1111")], URL
        )
        self.assertEqual(plan.update_id, "a")
        self.assertFalse(plan.create)

    def test_hand_made_entry_without_hash_is_taken_over(self):
        plan = res.plan_resource([item("a", "/tesy_static/tesy-boiler-card.js")], URL)
        self.assertEqual(plan.update_id, "a")

    def test_wrong_type_is_fixed(self):
        plan = res.plan_resource([item("a", URL, "js")], URL)
        self.assertEqual(plan.update_id, "a")

    def test_duplicates_are_removed(self):
        plan = res.plan_resource(
            [
                item("a", URL),
                item("b", "/tesy_static/tesy-boiler-card.js?v=old"),
                item("c", "/tesy_static/tesy-boiler-card.js"),
            ],
            URL,
        )
        self.assertIsNone(plan.update_id)
        self.assertEqual(plan.delete_ids, ["b", "c"])

    def test_copies_elsewhere_are_reported_not_touched(self):
        plan = res.plan_resource(
            [item("a", URL), item("z", "/local/tesy-boiler-card.js?v=1")], URL
        )
        self.assertFalse(plan.changes)
        self.assertEqual(plan.foreign_urls, ["/local/tesy-boiler-card.js?v=1"])

    def test_removal_takes_only_own_entries(self):
        ids = res.plan_removal(
            [
                item("a", URL),
                item("b", "/tesy_static/tesy-boiler-card.js"),
                item("z", "/local/tesy-boiler-card.js"),
            ],
            URL,
        )
        self.assertEqual(ids, ["a", "b"])
