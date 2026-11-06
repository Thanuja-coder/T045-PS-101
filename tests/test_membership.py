
import unittest
from decimal import Decimal
from unittest import result
from src.data_loader import load_plans, load_members
from src.membership import calculate_membership_allowance, validate_member, register_member


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

if __name__ == "__main__":
    unittest.main()