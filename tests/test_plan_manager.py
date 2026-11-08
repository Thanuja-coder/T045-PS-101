
import unittest
from datetime import datetime

from src.data_loader import load_plans, load_members
from src.plan_manager import process_upgrade, process_downgrade
from datetime import datetime, date
from src.plan_manager import process_upgrade, process_downgrade, process_freeze

class TestPlanManager(unittest.TestCase):

    def setUp(self):
        self.plans = load_plans()
        self.member = load_members()["M01"].copy()
        self.events = {}

    def test_process_upgrade(self):
        requested_ts = datetime(2026, 11, 16, 10, 30)

        result = process_upgrade(
            self.member,
            "DEDICATED",
            self.plans,
            requested_ts,
            "PE-16",
            self.events
        )

        # Check the calculated upgrade details
        self.assertEqual(result["additional_fee"], 3500)
        self.assertEqual(result["additional_room_credits"], 10)

        # Check that the member's plan was updated
        self.assertEqual(self.member["plan"], "DEDICATED")

        # Check that the upgrade event was recorded
        self.assertIn("PE-16", self.events)

        event = self.events["PE-16"]

        self.assertEqual(event["member_id"], self.member["member_id"])
        self.assertEqual(event["event_type"], "UPGRADE")
        self.assertEqual(event["new_plan"], "DEDICATED")
        self.assertEqual(event["effective_date"], requested_ts.date())
        self.assertEqual(event["requested_ts"], requested_ts)
        self.assertEqual(event["seats"], self.member["seats"])
        self.assertIsNone(event["freeze_days"])

    
    def test_process_downgrade(self):
        # M07 is a DEDICATED member in the sample data
        member = load_members()["M07"].copy()
        requested_ts = datetime(2026, 11, 16, 10, 30)

        result = process_downgrade(
            member,
            "FLEX",
            self.plans,
            requested_ts,
            "PE-17",
            self.events
        )

        # Downgrade should take effect from the next calendar month
        self.assertEqual(
            result["effective_date"],
            datetime(2026, 12, 1).date()
        )

        # The current plan should remain unchanged for now
        self.assertEqual(member["plan"], "DEDICATED")

        # Check the recorded downgrade event
        self.assertIn("PE-17", self.events)

        event = self.events["PE-17"]
        self.assertEqual(event["event_type"], "DOWNGRADE")
        self.assertEqual(event["old_plan"], "DEDICATED")
        self.assertEqual(event["new_plan"], "FLEX")
        self.assertEqual(event["member_id"], member["member_id"])
        self.assertEqual(event["requested_ts"], requested_ts)
        self.assertEqual(event["effective_date"], result["effective_date"])


    def test_downgrade_across_year_boundary(self):
        member = load_members()["M07"].copy()
        requested_ts = datetime(2026, 12, 20, 11, 0)

        result = process_downgrade(
            member,
            "FLEX",
            self.plans,
            requested_ts,
            "PE-18",
            self.events
        )

        # December downgrade should take effect on January 1
        self.assertEqual(
            result["effective_date"],
            datetime(2027, 1, 1).date()
        )

        # The current plan should remain unchanged
        self.assertEqual(member["plan"], "DEDICATED")

        # The scheduled downgrade should be recorded
        self.assertIn("PE-18", self.events)
        self.assertEqual(
            self.events["PE-18"]["event_type"],
            "DOWNGRADE"
        )

    def test_process_freeze_for_15_days(self):
        member = self.member.copy()
        requested_ts = datetime(2026, 11, 8, 10, 0)

        result = process_freeze(
            member, 15, date(2026, 11, 10),
            requested_ts, "PE-19", self.events, []
        )

        self.assertEqual(result["freeze_days"], 15)
        self.assertEqual(result["event_type"], "FREEZE")
        self.assertIn("PE-19", self.events)

    def test_process_freeze_for_60_days(self):
        member = self.member.copy()

        result = process_freeze(
            member, 60, date(2026, 1, 1),
            datetime(2026, 1, 1, 10, 0),
            "PE-20", self.events, []
        )

        self.assertEqual(result["freeze_days"], 60)

    def test_freeze_below_minimum_is_rejected(self):
        with self.assertRaises(ValueError):
            process_freeze(
                self.member.copy(), 14, date(2026, 11, 10),
                datetime(2026, 11, 8, 10, 0),
                "PE-21", self.events, []
            )

    def test_freeze_above_maximum_is_rejected(self):
        with self.assertRaises(ValueError):
            process_freeze(
                self.member.copy(), 61, date(2026, 11, 10),
                datetime(2026, 11, 8, 10, 0),
                "PE-22", self.events, []
            )

    def test_freeze_cannot_cross_calendar_year(self):
        with self.assertRaises(ValueError):
            process_freeze(
                self.member.copy(), 15, date(2026, 12, 20),
                datetime(2026, 12, 1, 10, 0),
                "PE-23", self.events, []
            )

    def test_annual_freeze_limit_is_checked(self):
        member = self.member.copy()

        self.events["PE-24"] = {
            "event_id": "PE-24",
            "member_id": member["member_id"],
            "requested_ts": datetime(2026, 2, 1, 10, 0),
            "event_type": "FREEZE",
            "effective_date": date(2026, 2, 1),
            "new_plan": None,
            "seats": member["seats"],
            "freeze_days": 20
        }

        # Another 40 days is allowed
        result = process_freeze(
            member, 40, date(2026, 6, 1),
            datetime(2026, 5, 20, 10, 0),
            "PE-25", self.events, []
        )

        self.assertEqual(result["freeze_days"], 40)

    def test_annual_freeze_limit_cannot_be_exceeded(self):
        member = self.member.copy()

        self.events["PE-26"] = {
            "event_id": "PE-26",
            "member_id": member["member_id"],
            "requested_ts": datetime(2026, 2, 1, 10, 0),
            "event_type": "FREEZE",
            "effective_date": date(2026, 2, 1),
            "new_plan": None,
            "seats": member["seats"],
            "freeze_days": 20
        }

        with self.assertRaises(ValueError):
            process_freeze(
                member, 41, date(2026, 6, 1),
                datetime(2026, 5, 20, 10, 0),
                "PE-27", self.events, []
            )

    def test_freeze_rejected_when_future_booking_exists(self):
        member = self.member.copy()

        future_booking = {
            "member_id": member["member_id"],
            "start_ts": datetime(2026, 11, 15, 10, 0)
        }

        with self.assertRaises(ValueError):
            process_freeze(
                member, 15, date(2026, 11, 20),
                datetime(2026, 11, 8, 10, 0),
                "PE-28", self.events, [future_booking]
            )
if __name__ == "__main__":
    unittest.main()
