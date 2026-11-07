
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
