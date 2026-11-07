
import unittest
from datetime import datetime, timedelta

from src.data_loader import load_rooms
from src.booking import validate_room_booking
from src.booking import validate_booking_overlap


class TestBooking(unittest.TestCase):

    def setUp(self):
        self.rooms = load_rooms()

    def create_booking(self, resource="R-4A", start=None, end=None, attendees=2):
        if start is None:
            start = datetime(2026, 1, 5, 10, 0)

        if end is None:
            end = start + timedelta(hours=1)

        return {
            "booking_id": "BK-TEST",
            "member_id": "M01",
            "resource": resource,
            "start_ts": start,
            "end_ts": end,
            "attendees": attendees,
            "booked_by": None
        }

    def test_valid_room_booking(self):
        booking = self.create_booking()

        result = validate_room_booking(booking, self.rooms)

        self.assertTrue(result)

    def test_room_does_not_exist(self):
        booking = self.create_booking(resource="R-UNKNOWN")

        with self.assertRaises(ValueError):
            validate_room_booking(booking, self.rooms)

    def test_end_time_before_start_time(self):
        start = datetime(2026, 1, 5, 12, 0)
        end = datetime(2026, 1, 5, 11, 0)

        booking = self.create_booking(start=start, end=end)

        with self.assertRaises(ValueError):
            validate_room_booking(booking, self.rooms)

    def test_booking_less_than_30_minutes(self):
        start = datetime(2026, 1, 5, 10, 0)
        end = start + timedelta(minutes=15)

        booking = self.create_booking(start=start, end=end)

        with self.assertRaises(ValueError):
            validate_room_booking(booking, self.rooms)

    def test_booking_not_in_30_minute_increments(self):
        start = datetime(2026, 1, 5, 10, 0)
        end = start + timedelta(minutes=45)

        booking = self.create_booking(start=start, end=end)

        with self.assertRaises(ValueError):
            validate_room_booking(booking, self.rooms)

    def test_booking_exceeds_4_hours(self):
        start = datetime(2026, 1, 5, 10, 0)
        end = start + timedelta(hours=4, minutes=30)

        booking = self.create_booking(start=start, end=end)

        with self.assertRaises(ValueError):
            validate_room_booking(booking, self.rooms)

    def test_attendees_exceed_room_capacity(self):
        booking = self.create_booking(
            resource="R-4A",
            attendees=5
        )

        with self.assertRaises(ValueError):
            validate_room_booking(booking, self.rooms)

    
    def create_existing_booking(self, resource="R-4A",
                                start=None, end=None):
        if start is None:
            start = datetime(2026, 1, 5, 10, 0)

        if end is None:
            end = datetime(2026, 1, 5, 11, 0)

        return {
            "booking_id": "BK-EXISTING",
            "member_id": "M02",
            "resource": resource,
            "start_ts": start,
            "end_ts": end,
            "attendees": 2,
            "booked_by": None
        }

    def test_exact_time_overlap(self):
        existing = self.create_existing_booking()

        new_booking = self.create_booking(
            start=datetime(2026, 1, 5, 10, 0),
            end=datetime(2026, 1, 5, 11, 0)
        )

        with self.assertRaises(ValueError):
            validate_booking_overlap(new_booking, [existing])

    def test_partial_time_overlap(self):
        existing = self.create_existing_booking()

        new_booking = self.create_booking(
            start=datetime(2026, 1, 5, 10, 30),
            end=datetime(2026, 1, 5, 11, 30)
        )

        with self.assertRaises(ValueError):
            validate_booking_overlap(new_booking, [existing])

    def test_booking_starts_when_existing_booking_ends(self):
        existing = self.create_existing_booking()

        new_booking = self.create_booking(
            start=datetime(2026, 1, 5, 11, 0),
            end=datetime(2026, 1, 5, 12, 0)
        )

        result = validate_booking_overlap(new_booking, [existing])

        self.assertTrue(result)

    def test_booking_in_different_time_slot(self):
        existing = self.create_existing_booking()

        new_booking = self.create_booking(
            start=datetime(2026, 1, 5, 12, 0),
            end=datetime(2026, 1, 5, 13, 0)
        )

        result = validate_booking_overlap(new_booking, [existing])

        self.assertTrue(result)

    def test_booking_in_different_room(self):
        existing = self.create_existing_booking(resource="R-4A")

        new_booking = self.create_booking(
            resource="R-4B",
            start=datetime(2026, 1, 5, 10, 0),
            end=datetime(2026, 1, 5, 11, 0)
        )

        result = validate_booking_overlap(new_booking, [existing])

        self.assertTrue(result)



if __name__ == "__main__":
    unittest.main()
