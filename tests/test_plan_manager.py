
import unittest
from datetime import datetime

from src.data_loader import load_plans, load_members
from src.plan_manager import process_upgrade, process_downgrade


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
if __name__ == "__main__":
    unittest.main()
