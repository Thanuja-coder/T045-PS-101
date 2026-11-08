
from datetime import date
import unittest
from decimal import Decimal
from unittest import result
from src.data_loader import load_plans, load_members
from src.membership import calculate_membership_allowance, validate_member, register_member, calculate_upgrade_details,calculate_freeze_allowance


class TestMembership(unittest.TestCase):

    def setUp(self):
        self.plans = load_plans()
        self.members = load_members()

    def create_member(self, member_id, plan, seats):
        return {
            "member_id": member_id,
            "member_name": "Test Member",
            "company": None,
            "plan": plan,
            "seats": seats,
            "billing_cycle_start": None,
            "dedicated_desk": None,
            "opening_carry_credits": 0,
            "freeze_days_used_2026": 0,
            "gstin": None
        }

    def test_valid_member_registration(self):
        member = self.create_member("M21", "FLEX", 1)

        result = register_member(member, self.plans, self.members)

        self.assertEqual(result["member_id"], "M21")
        self.assertIn("M21", self.members)

    def test_duplicate_member_id(self):
        member = self.create_member("M01", "FLEX", 1)

        with self.assertRaises(ValueError):
            validate_member(member, self.plans, self.members)

    def test_invalid_plan(self):
        member = self.create_member("M21", "PREMIUM", 1)

        with self.assertRaises(ValueError):
            validate_member(member, self.plans, self.members)

    def test_team_minimum_seats(self):
        member = self.create_member("M21", "TEAM", 2)

        with self.assertRaises(ValueError):
            validate_member(member, self.plans, self.members)

    def test_flex_allowance(self):
        result = calculate_membership_allowance(
            self.members["M01"], self.plans
        )
        self.assertEqual(result["room_credits"], 20)
        self.assertEqual(result["desk_days"], 10)

    def test_team_pooled_credits(self):
        result = calculate_membership_allowance(
        self.members["M03"], self.plans)
        self.assertEqual(result["room_credits"], 180)
        self.assertEqual(result["plan_fee"], Decimal("36000"))

    def test_team_four_seats(self):
        result = calculate_membership_allowance(
        self.members["M18"], self.plans)
        self.assertEqual(result["room_credits"], 240)
        self.assertEqual(result["plan_fee"], Decimal("48000"))
    
    def test_dedicated_unlimited_desk(self):
        result = calculate_membership_allowance(
        self.members["M07"], self.plans)
        self.assertEqual(result["desk_days"], "UNLIMITED")


    def test_flex_to_dedicated_upgrade_fee(self):
        member = self.create_member("M21", "FLEX", 1)

        result = calculate_upgrade_details(
            member,
            "DEDICATED",
            self.plans,
            date(2026, 11, 16)
        )

        self.assertEqual(result["additional_fee"], Decimal("3500"))
        self.assertEqual(result["additional_room_credits"], 10)

    def test_upgrade_remaining_days_includes_effective_date(self):
        member = self.create_member("M21", "FLEX", 1)

        result = calculate_upgrade_details(
            member,
            "DEDICATED",
            self.plans,
            date(2026, 11, 16)
        )

        self.assertEqual(result["remaining_days"], 15)
        self.assertEqual(result["days_in_month"], 30)

    def test_upgrade_does_not_change_original_member(self):
        member = self.create_member("M21", "FLEX", 1)

        calculate_upgrade_details(
            member,
            "DEDICATED",
            self.plans,
            date(2026, 11, 16)
        )

        self.assertEqual(member["plan"], "FLEX")

    def test_upgrade_on_last_day_of_30_day_month(self):
        member = self.create_member("M21", "FLEX", 1)

        result = calculate_upgrade_details(
            member,
            "DEDICATED",
            self.plans,
            date(2026, 11, 30)
        )

        self.assertEqual(result["remaining_days"], 1)
        self.assertEqual(result["additional_fee"], Decimal("233"))
        self.assertEqual(result["additional_room_credits"], 0)

    def test_upgrade_on_last_day_of_february(self):
        member = self.create_member("M21", "FLEX", 1)

        result = calculate_upgrade_details(
            member,
            "DEDICATED",
            self.plans,
            date(2027, 2, 28)
        )

        self.assertEqual(result["days_in_month"], 28)
        self.assertEqual(result["remaining_days"], 1)
        self.assertEqual(result["additional_fee"], Decimal("250"))

    def test_upgrade_on_leap_year_february(self):
        member = self.create_member("M21", "FLEX", 1)

        result = calculate_upgrade_details(
            member,
            "DEDICATED",
            self.plans,
            date(2028, 2, 29)
        )

        self.assertEqual(result["days_in_month"], 29)
        self.assertEqual(result["remaining_days"], 1)
        self.assertEqual(result["additional_fee"], Decimal("241"))

    def test_flex_to_team_upgrade_uses_seat_based_allowance(self):
        member = self.create_member("M21", "FLEX", 3)

        result = calculate_upgrade_details(
            member,
            "TEAM",
            self.plans,
            date(2026, 11, 16)
        )

        self.assertEqual(result["additional_fee"], Decimal("14000"))
        self.assertEqual(result["additional_room_credits"], 80)

    
    def test_freeze_allowance_february_readme_example(self):
        member = self.members["M01"]

        freeze_events = {
            "PE-04": {
                "member_id": member["member_id"],
                "event_type": "FREEZE",
                "effective_date": date(2026, 1, 25),
                "freeze_days": 15
            }
        }

        result = calculate_freeze_allowance(
            member,
            self.plans,
            date(2026, 2, 1),
            freeze_events
        )

        self.assertEqual(result["freeze_days"], 8)
        self.assertEqual(result["active_days"], 20)
        self.assertEqual(result["room_credits"], 14)
        self.assertEqual(result["desk_days"], 7)

    def test_freeze_allowance_january_readme_example(self):
        member = self.members["M01"]

        freeze_events = {
            "PE-04": {
                "member_id": member["member_id"],
                "event_type": "FREEZE",
                "effective_date": date(2026, 1, 25),
                "freeze_days": 15
            }
        }

        result = calculate_freeze_allowance(
            member,
            self.plans,
            date(2026, 1, 1),
            freeze_events
        )

        self.assertEqual(result["freeze_days"], 7)
        self.assertEqual(result["active_days"], 24)
        self.assertEqual(result["room_credits"], 15)
        self.assertEqual(result["desk_days"], 7)

    def test_freeze_allowance_without_freeze(self):
        member = self.members["M01"]

        result = calculate_freeze_allowance(
            member,
            self.plans,
            date(2026, 2, 1),
            {}
        )

        self.assertEqual(result["room_credits"], 20)
        self.assertEqual(result["desk_days"], 10)
        self.assertEqual(result["freeze_days"], 0)
        self.assertEqual(result["active_days"], 28)

if __name__ == "__main__":
    unittest.main()