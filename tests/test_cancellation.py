
import unittest
from datetime import datetime, timedelta
from src.cancellation import calculate_cancellation_refund, check_booking_no_show
from src.cancellation import calculate_no_show_fee

class TestCancellationRefund(unittest.TestCase):

    def test_full_refund_more_than_24_hours_before(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start - timedelta(hours=25)

        refund = calculate_cancellation_refund(
            10, booking_start, cancellation_time
        )

        self.assertEqual(refund, 10)

    def test_half_refund_between_2_and_24_hours(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start - timedelta(hours=12)

        refund = calculate_cancellation_refund(
            10, booking_start, cancellation_time
        )

        self.assertEqual(refund, 5)

    def test_half_refund_rounds_down(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start - timedelta(hours=12)

        refund = calculate_cancellation_refund(
            9, booking_start, cancellation_time
        )

        self.assertEqual(refund, 4)

    def test_no_refund_less_than_2_hours_before(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start - timedelta(hours=1)

        refund = calculate_cancellation_refund(
            10, booking_start, cancellation_time
        )

        self.assertEqual(refund, 0)

    
    def test_exactly_2_hours_before_booking(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start - timedelta(hours=2)

        refund = calculate_cancellation_refund(
            10, booking_start, cancellation_time
        )

        self.assertEqual(refund, 5)

    
    def test_exactly_24_hours_before_booking(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start - timedelta(hours=24)

        refund = calculate_cancellation_refund(
            10, booking_start, cancellation_time
        )

        self.assertEqual(refund, 5)

    
    def test_zero_booking_credits(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start - timedelta(hours=25)

        with self.assertRaises(ValueError):
            calculate_cancellation_refund(
                0, booking_start, cancellation_time
            )

    def test_negative_booking_credits(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start - timedelta(hours=25)

        with self.assertRaises(ValueError):
            calculate_cancellation_refund(
                -5, booking_start, cancellation_time
            )

    def test_cancellation_after_booking_starts(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        cancellation_time = booking_start + timedelta(hours=1)

        with self.assertRaises(ValueError):
            calculate_cancellation_refund(
                10, booking_start, cancellation_time
            )

    def test_cancellation_at_booking_start(self):
        booking_start = datetime(2026, 11, 15, 10, 0)

        with self.assertRaises(ValueError):
            calculate_cancellation_refund(
                10, booking_start, booking_start
            )


    def test_check_in_within_15_minutes(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        check_in_time = booking_start + timedelta(minutes=5)
        current_time = booking_start + timedelta(minutes=20)

        result = check_booking_no_show(
            booking_start, check_in_time, current_time
        )

        self.assertFalse(result)

    def test_check_in_exactly_at_15_minutes(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        check_in_time = booking_start + timedelta(minutes=15)
        current_time = booking_start + timedelta(minutes=20)

        result = check_booking_no_show(
            booking_start, check_in_time, current_time
        )

        self.assertFalse(result)

    def test_no_check_in_after_15_minutes(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        current_time = booking_start + timedelta(minutes=16)

        result = check_booking_no_show(
            booking_start, None, current_time
        )

        self.assertTrue(result)

    def test_no_show_not_detected_before_deadline(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        current_time = booking_start + timedelta(minutes=10)

        result = check_booking_no_show(
            booking_start, None, current_time
        )

        self.assertFalse(result)

    def test_late_check_in_is_no_show(self):
        booking_start = datetime(2026, 11, 15, 10, 0)
        check_in_time = booking_start + timedelta(minutes=16)
        current_time = booking_start + timedelta(minutes=20)

        result = check_booking_no_show(
            booking_start, check_in_time, current_time
        )

        self.assertTrue(result)


    def test_first_no_show_has_no_fee(self):
        fee = calculate_no_show_fee(1)
        self.assertEqual(fee, 0)

    def test_second_no_show_has_200_fee(self):
        fee = calculate_no_show_fee(3)
        self.assertEqual(fee, 200)

    def test_third_no_show_has_200_fee(self):
        fee = calculate_no_show_fee(3)
        self.assertEqual(fee, 200)

    def test_zero_no_shows_has_no_fee(self):
        fee = calculate_no_show_fee(0)
        self.assertEqual(fee, 0)

    def test_negative_no_show_count(self):
        with self.assertRaises(ValueError):
            calculate_no_show_fee(-1)


if __name__ == "__main__":
    unittest.main()
