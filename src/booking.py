
from datetime import timedelta


class BookingValidationError(ValueError):
    def __init__(self, message, rule_id):
        super().__init__(message)
        self.rule_id = rule_id


def validate_room_booking(booking, rooms):
    room_id = booking["resource"]

    if room_id not in rooms:
        raise BookingValidationError(
            f"Room does not exist: {room_id}", "BR-02"
        )

    room = rooms[room_id]
    start_time = booking["start_ts"]
    end_time = booking["end_ts"]

    if end_time <= start_time:
        raise BookingValidationError(
            "End time must be after start time", "BR-02"
        )

    duration_minutes = (end_time - start_time).total_seconds() / 60

    if duration_minutes < 30:
        raise BookingValidationError(
            "Minimum booking duration is 30 minutes", "BR-02"
        )

    if duration_minutes % 30 != 0:
        raise BookingValidationError(
            "Booking duration must be in 30-minute increments", "BR-02"
        )

    if duration_minutes > 240:
        raise BookingValidationError(
            "Maximum booking duration is 4 hours", "BR-02"
        )

    attendees = booking["attendees"]

    if attendees is None or attendees < 1:
        raise BookingValidationError(
            "Attendees must be at least 1", "BR-02"
        )

    if attendees > room["seats"]:
        raise BookingValidationError(
            "Attendees exceed room capacity", "BR-02"
        )

    return True


def validate_desk_booking(booking):
    if booking["end_ts"] <= booking["start_ts"]:
        raise BookingValidationError(
            "End time must be after start time", "BR-10"
        )

    return True


def validate_booking_overlap(new_booking, accepted_bookings):
    if new_booking["resource"] == "HOT_DESK":
        return True

    for existing_booking in accepted_bookings:
        if existing_booking["resource"] != new_booking["resource"]:
            continue

        if (
            new_booking["start_ts"] < existing_booking["end_ts"]
            and new_booking["end_ts"] > existing_booking["start_ts"]
        ):
            raise BookingValidationError(
                f"Room {new_booking['resource']} is already booked "
                "for this time slot",
                "BR-12"
            )

    return True


def validate_advance_booking(booking, member, plans):
    plan_name = member["plan"]
    requested_time = booking["requested_ts"]
    booking_start = booking["start_ts"]

    advance_days = plans[plan_name]["advance_days"]
    latest_allowed_time = requested_time + timedelta(days=advance_days)

    if booking_start > latest_allowed_time:
        raise BookingValidationError(
            f"{plan_name} members can book only "
            f"{advance_days} days in advance",
            "BR-06"
        )

    return True


def validate_future_booking_limit(
    booking, member, accepted_bookings, plans
):
    if member["plan"] != "FLEX":
        return True

    if booking["resource"] == "HOT_DESK":
        return True

    member_id = member["member_id"]
    requested_time = booking["requested_ts"]
    future_room_bookings = 0

    max_bookings = plans["FLEX"].get(
        "max_future_room_bookings", 2
    )

    for existing_booking in accepted_bookings:
        if existing_booking["member_id"] != member_id:
            continue

        if existing_booking["resource"] == "HOT_DESK":
            continue

        if existing_booking["start_ts"] > requested_time:
            future_room_bookings += 1

    if future_room_bookings >= max_bookings:
        raise BookingValidationError(
            "FLEX members can have a maximum of "
            f"{max_bookings} future room bookings",
            "BR-06"
        )

    return True


def validate_booking_freeze(booking, member, freeze_events):
    member_id = member["member_id"]
    booking_date = booking["start_ts"].date()

    for event in freeze_events:
        if event["member_id"] != member_id:
            continue

        if event["event_type"] != "FREEZE":
            continue

        freeze_start = event["effective_date"]
        freeze_days = event["freeze_days"]
        freeze_end = freeze_start + timedelta(days=freeze_days - 1)

        if freeze_start <= booking_date <= freeze_end:
            raise BookingValidationError(
                "Member is currently frozen", "BR-09"
            )

    return True


def validate_freeze_start(freeze_event, accepted_bookings):
    member_id = freeze_event["member_id"]
    requested_time = freeze_event["requested_ts"]

    for booking in accepted_bookings:
        if booking["member_id"] != member_id:
            continue

        if booking["start_ts"] > requested_time:
            raise ValueError(
                "Cannot start freeze while future bookings exist"
            )

    return True


def validate_hot_desk_capacity(booking, accepted_bookings):
    if booking["resource"] != "HOT_DESK":
        return True

    new_start = booking["start_ts"]
    new_end = booking["end_ts"]
    occupied_desks = 0

    for existing in accepted_bookings:
        if existing["resource"] != "HOT_DESK":
            continue

        if (
            new_start < existing["end_ts"]
            and new_end > existing["start_ts"]
        ):
            occupied_desks += 1

    if occupied_desks >= 40:
        raise BookingValidationError(
            "Hot desk capacity is full", "BR-10"
        )

    return True


def validate_booking(
    booking, member, rooms, plans, accepted_bookings, freeze_events
):
    # Basic booking and capacity checks.
    if booking["resource"] == "HOT_DESK":
        validate_desk_booking(booking)
        validate_hot_desk_capacity(booking, accepted_bookings)
    else:
        validate_room_booking(booking, rooms)

    # Apply the booking rejection checks.
    validate_booking_overlap(booking, accepted_bookings)

    validate_advance_booking(booking, member, plans)

    validate_future_booking_limit(
        booking, member, accepted_bookings, plans
    )

    validate_booking_freeze(booking, member, freeze_events)

    return True
