from datetime import timedelta



def validate_room_booking(booking, rooms):
    room_id = booking["resource"]

    # Check whether the requested room exists
    if room_id not in rooms:
        raise ValueError(f"Room does not exist: {room_id}")

    room = rooms[room_id]

    start_time = booking["start_ts"]
    end_time = booking["end_ts"]

    # Check whether the end time is after the start time
    if end_time <= start_time:
        raise ValueError("End time must be after start time")

    duration = end_time - start_time
    duration_minutes = duration.total_seconds() / 60

    # Check minimum booking duration
    if duration_minutes < 30:
        raise ValueError("Minimum booking duration is 30 minutes")

    # Check 30-minute increments
    if duration_minutes % 30 != 0:
        raise ValueError("Booking duration must be in 30-minute increments")

    # Check maximum booking duration
    if duration_minutes > 240:
        raise ValueError("Maximum booking duration is 4 hours")

    attendees = booking["attendees"]

    # Check room capacity
    if attendees is None or attendees < 1:
        raise ValueError("Attendees must be at least 1")

    if attendees > room["seats"]:
        raise ValueError("Attendees exceed room capacity")

    return True




def validate_booking_overlap(new_booking, accepted_bookings):

    for existing_booking in accepted_bookings:

        # Check whether both bookings are for the same room
        if new_booking["resource"] != existing_booking["resource"]:
            continue

        # Get the start and end times of both bookings
        new_start = new_booking["start_ts"]
        new_end = new_booking["end_ts"]

        existing_start = existing_booking["start_ts"]
        existing_end = existing_booking["end_ts"]

        # Check whether the booking times overlap
        if new_start < existing_end and new_end > existing_start:
            raise ValueError(
                f"Room {new_booking['resource']} is already booked "
                f"for this time slot"
            )

    return True


def validate_advance_booking(booking, member, plans):
    requested_time = booking["requested_ts"]
    booking_start = booking["start_ts"]

    plan_name = member["plan"]
    advance_days = plans[plan_name]["advance_days"]

    latest_allowed_time = requested_time + timedelta(days=advance_days)

    if booking_start > latest_allowed_time:
        raise ValueError(
            f"{plan_name} members can book only "
            f"{advance_days} days in advance"
        )

    return True
def validate_future_booking_limit(booking, member, accepted_bookings, plans):
    plan_name = member["plan"]

    max_bookings = plans[plan_name]["max_future_room_bookings"]

    # Plans without a booking limit can make future room bookings
    if max_bookings is None:
        return True

    # This limit applies only to room bookings
    if booking["resource"] == "HOT_DESK":
        return True

    requested_time = booking["requested_ts"]
    member_id = member["member_id"]

    future_room_bookings = 0

    for existing_booking in accepted_bookings:
        if existing_booking["member_id"] != member_id:
            continue

        if existing_booking["resource"] == "HOT_DESK":
            continue

        if existing_booking["start_ts"] > requested_time:
            future_room_bookings += 1

    if future_room_bookings >= max_bookings:
        raise ValueError(
            f"{plan_name} members can have a maximum of "
            f"{max_bookings} future room bookings"
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
            raise ValueError("Member is currently frozen")

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
    # Only check capacity for hot-desk bookings
    if booking["resource"] != "HOT_DESK":
        return True

    new_start = booking["start_ts"]
    new_end = booking["end_ts"]

    occupied_desks = 0

    for existing in accepted_bookings:
        # Count only existing hot-desk bookings
        if existing["resource"] == "HOT_DESK":
            existing_start = existing["start_ts"]
            existing_end = existing["end_ts"]

            # Check whether the bookings overlap
            if new_start < existing_end and new_end > existing_start:
                occupied_desks += 1

    # The floor has a maximum capacity of 40 shared desks
    if occupied_desks >= 40:
        raise ValueError("Hot desk capacity is full")

    return True



def validate_booking(booking, member, rooms, plans,
                     accepted_bookings, freeze_events):

    # 1. Check whether the resource is already booked
    validate_booking_overlap(booking, accepted_bookings)

    # 2. Check the advance booking limit of the member's plan
    validate_advance_booking(booking, member, plans)

    # 3. Check whether the member is frozen
    validate_booking_freeze(booking, member, freeze_events)

    # 4. Check the maximum number of future room bookings
    validate_future_booking_limit(
        booking, member, accepted_bookings, plans
    )

    # 5. Perform resource-specific validation
    if booking["resource"] == "HOT_DESK":

        # Check whether a shared hot desk is available
        validate_hot_desk_capacity(booking, accepted_bookings)

    else:

        # Validate the meeting-room booking
        validate_room_booking(booking, rooms)

    return True
