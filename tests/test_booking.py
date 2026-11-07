
import unittest
from datetime import datetime, timedelta

from src.data_loader import load_plans, load_rooms
from src.booking import (
    validate_room_booking,
    validate_booking_overlap,
    validate_advance_booking,
    validate_future_booking_limit,
    validate_booking_freeze,
    validate_freeze_start,
    validate_hot_desk_capacity,
     validate_booking
)

class TestBooking(unittest.TestCase):

    def setUp(self):
        self.rooms = load_rooms()
        self.plans =load_plans()

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

    
    def test_flex_booking_within_advance_window(self):
        booking = self.create_booking(
            start=datetime(2026, 1, 10, 10, 0),
            end=datetime(2026, 1, 10, 11, 0)
        )
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        member = {"member_id": "M01", "plan": "FLEX"}

        result = validate_advance_booking(
            booking, member, self.plans
        )

        self.assertTrue(result)

    def test_flex_booking_exactly_7_days_ahead(self):
        booking = self.create_booking(
            start=datetime(2026, 1, 12, 10, 0),
            end=datetime(2026, 1, 12, 11, 0)
        )
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        member = {"member_id": "M01", "plan": "FLEX"}

        result = validate_advance_booking(
            booking, member, self.plans
        )

        self.assertTrue(result)

    def test_flex_booking_beyond_7_days(self):
        booking = self.create_booking(
            start=datetime(2026, 1, 13, 10, 0),
            end=datetime(2026, 1, 13, 11, 0)
        )
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        member = {"member_id": "M01", "plan": "FLEX"}

        with self.assertRaises(ValueError):
            validate_advance_booking(
                booking, member, self.plans
            )

    def test_dedicated_booking_within_30_days(self):
        booking = self.create_booking(
            start=datetime(2026, 2, 4, 10, 0),
            end=datetime(2026, 2, 4, 11, 0)
        )
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        member = {"member_id": "M07", "plan": "DEDICATED"}

        result = validate_advance_booking(
            booking, member, self.plans
        )

        self.assertTrue(result)

    def test_dedicated_booking_beyond_30_days(self):
        booking = self.create_booking(
            start=datetime(2026, 2, 5, 10, 0),
            end=datetime(2026, 2, 5, 11, 0)
        )
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        member = {"member_id": "M07", "plan": "DEDICATED"}

        with self.assertRaises(ValueError):
            validate_advance_booking(
                booking, member, self.plans
            )

    def test_team_booking_within_60_days(self):
        booking = self.create_booking(
            start=datetime(2026, 3, 6, 10, 0),
            end=datetime(2026, 3, 6, 11, 0)
        )
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        member = {"member_id": "M03", "plan": "TEAM"}

        result = validate_advance_booking(
            booking, member, self.plans
        )

        self.assertTrue(result)

    def test_team_booking_beyond_60_days(self):
        booking = self.create_booking(
            start=datetime(2026, 3, 7, 10, 0),
            end=datetime(2026, 3, 7, 11, 0)
        )
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        member = {"member_id": "M03", "plan": "TEAM"}

        with self.assertRaises(ValueError):
            validate_advance_booking(
                booking, member, self.plans
            )

    def test_flex_member_with_one_future_room_booking(self):
        booking = self.create_booking()
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        existing = self.create_existing_booking(
            start=datetime(2026, 1, 6, 10, 0)
        )
        existing["member_id"] = "M01"

        member = {"member_id": "M01", "plan": "FLEX"}

        self.assertTrue(
            validate_future_booking_limit(
                booking, member, [existing], self.plans
            )
        )

    def test_flex_member_cannot_make_third_future_room_booking(self):
        booking = self.create_booking()
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        existing_bookings = []

        for day in [6, 7]:
            existing = self.create_existing_booking(
                start=datetime(2026, 1, day, 10, 0)
            )
            existing["member_id"] = "M01"
            existing_bookings.append(existing)

        member = {"member_id": "M01", "plan": "FLEX"}

        with self.assertRaises(ValueError):
            validate_future_booking_limit(
                booking, member, existing_bookings, self.plans
            )

    def test_hot_desk_booking_does_not_count(self):
        booking = self.create_booking()
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        existing = self.create_existing_booking(
            start=datetime(2026, 1, 6, 10, 0)
        )
        existing["member_id"] = "M01"
        existing["resource"] = "HOT_DESK"

        member = {"member_id": "M01", "plan": "FLEX"}

        self.assertTrue(
            validate_future_booking_limit(
                booking, member, [existing], self.plans
            )
        )

    def test_past_room_booking_does_not_count(self):
        booking = self.create_booking()
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        existing = self.create_existing_booking(
            start=datetime(2026, 1, 4, 10, 0)
        )
        existing["member_id"] = "M01"

        member = {"member_id": "M01", "plan": "FLEX"}

        self.assertTrue(
            validate_future_booking_limit(
                booking, member, [existing], self.plans
            )
        )

    def test_team_member_has_no_future_booking_limit(self):
        booking = self.create_booking()
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        existing_bookings = []

        for day in [6, 7, 8]:
            existing = self.create_existing_booking(
                start=datetime(2026, 1, day, 10, 0)
            )
            existing["member_id"] = "M01"
            existing_bookings.append(existing)

        member = {"member_id": "M01", "plan": "TEAM"}

        self.assertTrue(
            validate_future_booking_limit(
                booking, member, existing_bookings, self.plans
            )
        )

    def test_new_hot_desk_booking_is_not_limited(self):
        booking = self.create_booking(resource="HOT_DESK")
        booking["requested_ts"] = datetime(2026, 1, 5, 10, 0)

        existing_bookings = []

        for day in [6, 7]:
            existing = self.create_existing_booking(
                start=datetime(2026, 1, day, 10, 0)
            )
            existing["member_id"] = "M01"
            existing_bookings.append(existing)

        member = {"member_id": "M01", "plan": "FLEX"}

        self.assertTrue(
            validate_future_booking_limit(
                booking, member, existing_bookings, self.plans
            )
        )

    def test_booking_during_freeze_is_rejected(self):
        booking = self.create_booking(
            start=datetime(2026, 2, 1, 10, 0)
        )

        freeze_events = [{
            "member_id": "M01",
            "event_type": "FREEZE",
            "effective_date": datetime(2026, 1, 25).date(),
            "freeze_days": 15
        }]

        member = {"member_id": "M01", "plan": "FLEX"}

        with self.assertRaises(ValueError):
            validate_booking_freeze(booking, member, freeze_events)

    def test_booking_after_freeze_is_allowed(self):
        booking = self.create_booking(
            start=datetime(2026, 2, 10, 10, 0)
        )

        freeze_events = [{
            "member_id": "M01",
            "event_type": "FREEZE",
            "effective_date": datetime(2026, 1, 25).date(),
            "freeze_days": 15
        }]

        member = {"member_id": "M01", "plan": "FLEX"}

        self.assertTrue(
            validate_booking_freeze(booking, member, freeze_events)
        )
    def test_freeze_start_rejected_with_future_booking(self):
        freeze_event = {
            "member_id": "M01",
            "event_type": "FREEZE",
            "requested_ts": datetime(2026, 1, 5, 10, 0),
            "effective_date": datetime(2026, 1, 10).date(),
            "freeze_days": 15
        }

        existing = self.create_existing_booking(
            start=datetime(2026, 1, 12, 10, 0)
        )
        existing["member_id"] = "M01"

        with self.assertRaises(ValueError):
            validate_freeze_start(
                freeze_event, [existing]
            )
    def test_freeze_start_allowed_without_future_bookings(self):
        freeze_event = {
            "member_id": "M01",
            "event_type": "FREEZE",
            "requested_ts": datetime(2026, 1, 5, 10, 0),
            "effective_date": datetime(2026, 1, 10).date(),
            "freeze_days": 15
        }

        self.assertTrue(
            validate_freeze_start(freeze_event, [])
        )
    
    def test_hot_desk_booking_allowed_when_39_desks_are_occupied(self):
        booking = {
            "resource": "HOT_DESK",
            "start_ts": datetime(2026, 2, 1, 9, 0),
            "end_ts": datetime(2026, 2, 1, 18, 0)
        }

        existing_bookings = []

        for i in range(39):
            existing_bookings.append({
                "booking_id": f"BK-{i}",
                "resource": "HOT_DESK",
                "start_ts": datetime(2026, 2, 1, 9, 0),
                "end_ts": datetime(2026, 2, 1, 18, 0)
            })

        self.assertTrue(
            validate_hot_desk_capacity(booking, existing_bookings)
        )

    def test_hot_desk_booking_rejected_when_40_desks_are_occupied(self):
        booking = {
            "resource": "HOT_DESK",
            "start_ts": datetime(2026, 2, 1, 9, 0),
            "end_ts": datetime(2026, 2, 1, 18, 0)
        }

        existing_bookings = []

        for i in range(40):
            existing_bookings.append({
                "booking_id": f"BK-{i}",
                "resource": "HOT_DESK",
                "start_ts": datetime(2026, 2, 1, 9, 0),
                "end_ts": datetime(2026, 2, 1, 18, 0)
            })

        with self.assertRaises(ValueError):
            validate_hot_desk_capacity(booking, existing_bookings)

    def test_hot_desk_booking_allowed_when_previous_booking_ends(self):
        booking = {
            "resource": "HOT_DESK",
            "start_ts": datetime(2026, 2, 1, 9, 0),
            "end_ts": datetime(2026, 2, 1, 18, 0)
        }

        existing_bookings = [{
            "booking_id": "BK-001",
            "resource": "HOT_DESK",
            "start_ts": datetime(2026, 2, 1, 8, 0),
            "end_ts": datetime(2026, 2, 1, 9, 0)
        } for i in range(40)]

        self.assertTrue(
            validate_hot_desk_capacity(booking, existing_bookings)
        )

    def test_other_resources_do_not_count_towards_hot_desk_capacity(self):
        booking = {
            "resource": "HOT_DESK",
            "start_ts": datetime(2026, 2, 1, 9, 0),
            "end_ts": datetime(2026, 2, 1, 18, 0)
        }

        existing_bookings = [{
            "booking_id": f"BK-{i}",
            "resource": "R-4A",
            "start_ts": datetime(2026, 2, 1, 9, 0),
            "end_ts": datetime(2026, 2, 1, 18, 0)
        } for i in range(40)]

        self.assertTrue(
            validate_hot_desk_capacity(booking, existing_bookings)
        )
    
    def test_complete_room_booking_validation(self):
        booking = {
            "booking_id": "BK-TEST",
            "member_id": "M01",
            "resource": "R-4A",
            "requested_ts": datetime(2026, 1, 1, 8, 0),
            "start_ts": datetime(2026, 1, 2, 9, 0),
            "end_ts": datetime(2026, 1, 2, 10, 0),
            "attendees": 2
        }

        member = {
            "member_id": "M01",
            "plan": "FLEX"
        }

        plans = {
            "FLEX": {
                "advance_days": 7,
                "max_future_room_bookings": 2
            }
        }

        rooms = {
            "R-4A": {"seats": 4}
        }

        self.assertTrue(
            validate_booking(
                booking, member, rooms, plans, [], []
            )
        )

    def test_complete_hot_desk_booking_validation(self):
        booking = {
            "booking_id": "BK-TEST",
            "member_id": "M01",
            "resource": "HOT_DESK",
            "requested_ts": datetime(2026, 1, 1, 8, 0),
            "start_ts": datetime(2026, 1, 2, 9, 0),
            "end_ts": datetime(2026, 1, 2, 18, 0)
        }

        member = {
            "member_id": "M01",
            "plan": "FLEX"
        }

        plans = {
            "FLEX": {
                "advance_days": 7,
                "max_future_room_bookings": 2
            }
        }

        self.assertTrue(
            validate_booking(
                booking, member, {}, plans, [], []
            )
        )

    def test_complete_booking_validation_rejects_overlap(self):
        booking = {
            "booking_id": "BK-TEST",
            "member_id": "M01",
            "resource": "R-4A",
            "requested_ts": datetime(2026, 1, 1, 8, 0),
            "start_ts": datetime(2026, 1, 2, 9, 0),
            "end_ts": datetime(2026, 1, 2, 10, 0),
            "attendees": 2
        }

        existing_booking = {
            "booking_id": "BK-OLD",
            "member_id": "M02",
            "resource": "R-4A",
            "start_ts": datetime(2026, 1, 2, 9, 30),
            "end_ts": datetime(2026, 1, 2, 10, 30)
        }

        member = {
            "member_id": "M01",
            "plan": "FLEX"
        }

        plans = {
            "FLEX": {
                "advance_days": 7,
                "max_future_room_bookings": 2
            }
        }

        rooms = {
            "R-4A": {"seats": 4}
        }

        with self.assertRaises(ValueError):
            validate_booking(
                booking, member, rooms, plans,
                [existing_booking], []
            )

if __name__ == "__main__":
    unittest.main()
