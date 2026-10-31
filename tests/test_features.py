"""Tests for per-model extended features (no Home Assistant needed)."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import TestCase

_PATH = Path(__file__).parents[1] / "custom_components" / "tesy" / "features.py"
_SPEC = spec_from_file_location("tesy_features", _PATH)
features = module_from_spec(_SPEC)
_SPEC.loader.exec_module(features)

ALL = {
    features.FEATURE_SCHEDULE,
    features.FEATURE_TIMEZONE,
    features.FEATURE_READBACK,
}
PROGRAMS = {
    "id": "2004",
    "tz": "EET-2EEST,M3.5.0/3,M10.5.0/4",
    **{f"prgP{p}{d}": "FF" * 24 for p in (1, 2, 3) for d in features._DAYS},
}


class DeviceFeaturesTest(TestCase):
    def test_modeco2_gets_everything(self):
        self.assertEqual(features.device_features(PROGRAMS), ALL)

    def test_other_models_get_nothing(self):
        # Same fields, but the model is not verified: basic behaviour.
        for model in ("2000", "2003", "2005", None):
            data = {**PROGRAMS, "id": model}
            self.assertEqual(features.device_features(data), frozenset(), model)

    def test_missing_fields_disable_their_feature(self):
        # The read-back needs no fields; the others need theirs.
        readback = features.FEATURE_READBACK
        self.assertEqual(features.device_features({"id": 2004}), {readback})
        self.assertEqual(
            features.device_features({"id": 2004, "tz": "UTC0"}),
            {features.FEATURE_TIMEZONE, readback},
        )
        # All 21 program days are needed, not just the first one.
        partial = {k: v for k, v in PROGRAMS.items() if k != "prgP3SU"}
        self.assertEqual(
            features.device_features(partial), {features.FEATURE_TIMEZONE, readback}
        )

    def test_bellislimo_gets_everything(self):
        data = {**PROGRAMS, "id": "2002", "cdt": "0"}
        self.assertEqual(
            features.device_features(data), ALL | {features.FEATURE_COUNTDOWN}
        )

    def test_countdown_needs_cdt(self):
        # Only cdt is required; ht just makes Ready In more accurate.
        countdown = features.FEATURE_COUNTDOWN
        self.assertIn(countdown, features.device_features({"id": "2002", "cdt": "5"}))
        self.assertNotIn(countdown, features.device_features({"id": "2002"}))

    def test_countdown_is_bellislimo_only(self):
        # The ModEco 2 doesn't report cdt; other models are unverified.
        for model in ("2000", "2003", "2004", "2005"):
            data = {**PROGRAMS, "id": model, "cdt": "5"}
            self.assertNotIn(
                features.FEATURE_COUNTDOWN, features.device_features(data), model
            )

    def test_numeric_tz_disables_timezone(self):
        # BelliSlimo Wi-Fi 0.26 reports tz as a number, not a POSIX string.
        readback = features.FEATURE_READBACK
        for model in ("2002", "2004"):
            for tz in ("180", "-120", " 0 "):
                data = {"id": model, "tz": tz}
                self.assertEqual(
                    features.device_features(data), {readback}, (model, tz)
                )

    def test_no_data(self):
        self.assertEqual(features.device_features(None), frozenset())
