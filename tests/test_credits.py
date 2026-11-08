
import unittest
from datetime import datetime,date

from src.credit_ledger import calculate_room_credits


class TestRoomCreditCalculation(unittest.TestCase):

    def test_normal_room_booking_credits(self):
        booking = {
            "start_ts": datetime(2026, 11, 9, 9, 0),
            "end_ts": datetime(2026, 11, 9, 10, 0)
        }

        room = {"credits_per_30min": 1}

        result = calculate_room_credits(booking, room)

        self.assertEqual(result, 2)

    def test_peak_hour_room_booking_credits(self):
        booking = {
            "start_ts": datetime(2026, 11, 9, 10, 0),
            "end_ts": datetime(2026, 11, 9, 10, 30)
        }

        room = {"credits_per_30min": 1}

        result = calculate_room_credits(booking, room)

        self.assertEqual(result, 2)

    def test_weekend_room_booking_credits(self):
        booking = {
            "start_ts": datetime(2026, 11, 8, 9, 0),
            "end_ts": datetime(2026, 11, 8, 9, 30)
        }

        room = {"credits_per_30min": 1}

        result = calculate_room_credits(booking, room)

        self.assertEqual(result, 1)

    def test_each_slot_is_calculated_separately(self):
        booking = {
            "start_ts": datetime(2026, 11, 9, 9, 30),
            "end_ts": datetime(2026, 11, 9, 10, 30)
        }

        room = {"credits_per_30min": 1}

        result = calculate_room_credits(booking, room)

        # 9:30 to 10:00 = 1 credit
        # 10:00 to 10:30 = 2 credits
        self.assertEqual(result, 3)


    def test_carry_forward_limit_for_20_credits(self):
        from src.credit_ledger import calculate_carry_forward_limit

        result = calculate_carry_forward_limit(20)

        self.assertEqual(result, 5)

    def test_carry_forward_limit_rounds_down(self):
        from src.credit_ledger import calculate_carry_forward_limit

        result = calculate_carry_forward_limit(15)

        self.assertEqual(result, 3)

    def test_carry_forward_limit_for_12_credits(self):
        from src.credit_ledger import calculate_carry_forward_limit

        result = calculate_carry_forward_limit(12)

        self.assertEqual(result, 3)

    def test_january_credits_expire_at_end_of_february(self):
        from src.credit_ledger import calculate_carry_forward_expiry

        result = calculate_carry_forward_expiry(date(2026, 1, 1))

        self.assertEqual(result, date(2026, 2, 28))

    def test_december_credits_expire_at_end_of_january(self):
        from src.credit_ledger import calculate_carry_forward_expiry

        result = calculate_carry_forward_expiry(date(2025, 12, 1))

        self.assertEqual(result, date(2026, 1, 31))

    def test_leap_year_expiry(self):
        from src.credit_ledger import calculate_carry_forward_expiry

        result = calculate_carry_forward_expiry(date(2024, 1, 1))

        self.assertEqual(result, date(2024, 2, 29))

    
class TestFIFOCreditConsumption(unittest.TestCase):

    def test_oldest_credits_are_used_first(self):
        from src.credit_ledger import consume_carry_forward_credits

        credit_buckets = [
            {
                "credits": 3,
                "created_date": date(2026, 1, 1)
            },
            {
                "credits": 4,
                "created_date": date(2026, 2, 1)
            }
        ]

        used, remaining = consume_carry_forward_credits(
            credit_buckets, 5
        )

        self.assertEqual(used, 5)
        self.assertEqual(remaining[0]["credits"], 2)

    def test_consumption_from_single_credit_batch(self):
        from src.credit_ledger import consume_carry_forward_credits

        credit_buckets = [
            {
                "credits": 5,
                "created_date": date(2026, 1, 1)
            }
        ]

        used, remaining = consume_carry_forward_credits(
            credit_buckets, 2
        )

        self.assertEqual(used, 2)
        self.assertEqual(remaining[0]["credits"], 3)

    def test_all_available_credits_are_consumed(self):
        from src.credit_ledger import consume_carry_forward_credits

        credit_buckets = [
            {
                "credits": 2,
                "created_date": date(2026, 1, 1)
            },
            {
                "credits": 3,
                "created_date": date(2026, 2, 1)
            }
        ]

        used, remaining = consume_carry_forward_credits(
            credit_buckets, 5
        )

        self.assertEqual(used, 5)
        self.assertEqual(remaining, [])
    
    def test_required_credits_exceed_carry_forward_balance(self):
        from src.credit_ledger import consume_carry_forward_credits

        credit_buckets = [
            {
                "credits": 3,
                "created_date": date(2026, 1, 1)
            },
            {
                "credits": 4,
                "created_date": date(2026, 2, 1)
            }
        ]

        used, remaining = consume_carry_forward_credits(
            credit_buckets, 9
        )

        self.assertEqual(used, 7)
        self.assertEqual(remaining, [])
        self.assertGreaterEqual(used, 0)

    
class TestRoomCreditOverage(unittest.TestCase):

    def test_calculate_room_credit_overage(self):
        from src.credit_ledger import calculate_room_overage

        result = calculate_room_overage(
            available_credits=12,
            required_credits=15
        )

        self.assertEqual(result["overage_credits"], 3)
        self.assertEqual(result["overage_amount"], 450)

    def test_no_overage_when_credits_are_sufficient(self):
        from src.credit_ledger import calculate_room_overage

        result = calculate_room_overage(
            available_credits=15,
            required_credits=12
        )

        self.assertEqual(result["overage_credits"], 0)
        self.assertEqual(result["overage_amount"], 0)

    def test_no_overage_when_credits_are_equal(self):
        from src.credit_ledger import calculate_room_overage

        result = calculate_room_overage(
            available_credits=10,
            required_credits=10
        )

        self.assertEqual(result["overage_credits"], 0)
        self.assertEqual(result["overage_amount"], 0)


class TestExpiredCarryForwardCredits(unittest.TestCase):

    def test_credits_are_valid_on_expiry_date(self):
        from src.credit_ledger import remove_expired_carry_forward_credits

        credit_buckets = [
            {
                "credits": 3,
                "created_date": date(2026, 1, 1)
            }
        ]

        result = remove_expired_carry_forward_credits(
            credit_buckets, date(2026, 2, 28)
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["credits"], 3)

    def test_expired_credits_are_removed(self):
        from src.credit_ledger import remove_expired_carry_forward_credits

        credit_buckets = [
            {
                "credits": 3,
                "created_date": date(2026, 1, 1)
            }
        ]

        result = remove_expired_carry_forward_credits(
            credit_buckets, date(2026, 3, 1)
        )

        self.assertEqual(result, [])

    def test_only_expired_batches_are_removed(self):
        from src.credit_ledger import remove_expired_carry_forward_credits

        credit_buckets = [
            {
                "credits": 3,
                "created_date": date(2026, 1, 1)
            },
            {
                "credits": 4,
                "created_date": date(2026, 2, 1)
            }
        ]

        result = remove_expired_carry_forward_credits(
            credit_buckets, date(2026, 3, 1)
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["credits"], 4)


class TestCreditUsageIntegration(unittest.TestCase):

    def test_expiry_fifo_and_monthly_credit_consumption(self):
        from src.credit_ledger import process_room_credit_usage

        credit_buckets = [
            {
                "credits": 3,
                "created_date": date(2026, 1, 1)
            },
            {
                "credits": 4,
                "created_date": date(2026, 2, 1)
            }
        ]

        result = process_room_credit_usage(
            credit_buckets,
            monthly_credits_available=5,
            required_credits=9,
            current_date=date(2026, 3, 1)
        )

        self.assertEqual(result["carry_forward_used"], 4)
        self.assertEqual(result["monthly_credits_used"], 5)
        self.assertEqual(result["overage_credits"], 0)
        self.assertEqual(result["overage_amount"], 0)

    def test_overage_when_all_available_credits_are_insufficient(self):
        from src.credit_ledger import process_room_credit_usage

        credit_buckets = [
            {
                "credits": 4,
                "created_date": date(2026, 2, 1)
            }
        ]

        result = process_room_credit_usage(
            credit_buckets,
            monthly_credits_available=5,
            required_credits=12,
            current_date=date(2026, 3, 1)
        )

        self.assertEqual(result["carry_forward_used"], 4)
        self.assertEqual(result["monthly_credits_used"], 5)
        self.assertEqual(result["overage_credits"], 3)
        self.assertEqual(result["overage_amount"], 450)

if __name__ == "__main__":
    unittest.main()


