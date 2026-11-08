from datetime import timedelta


def calculate_cancellation_refund(
        booking_credits, booking_start, cancellation_time):

    # Check whether booking credits are valid
    if booking_credits <= 0:
        raise ValueError("Booking credits must be greater than zero")

    # Cancellation must happen before the booking starts
    if cancellation_time >= booking_start:
        raise ValueError("Cancellation must happen before booking starts")

    # Calculate the time remaining before the booking
    time_before_booking = booking_start - cancellation_time

    # More than 24 hours before booking gives a full refund
    if time_before_booking > timedelta(hours=24):
        return booking_credits

    # Between 2 and 24 hours gives a 50% refund
    elif time_before_booking >= timedelta(hours=2):
        return booking_credits // 2

    # Less than 2 hours gives no refund
    else:
        return 0

def check_booking_no_show(booking_start, check_in_time, current_time):

    # Calculate the end of the 15-minute check-in window
    check_in_deadline = booking_start + timedelta(minutes=15)

    # If the current time is still within the allowed window,
    # the booking cannot be marked as a no-show
    if current_time <= check_in_deadline:
        return False

    # If the member checked in within the allowed time,
    # the booking is not a no-show
    if check_in_time is not None and check_in_time <= check_in_deadline:
        return False

    # Otherwise, the booking is considered a no-show
    return True

    
def calculate_no_show_fee(no_show_count):

    # Check whether the no-show count is valid
    if no_show_count < 0:
        raise ValueError("No-show count cannot be negative")

    # No fee is charged for the first no-show
    if no_show_count <= 2:
        return 0

    # A fee of Rs. 200 is charged from the second no-show
    return 200
