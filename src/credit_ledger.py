
import math
from datetime import timedelta,date
import calendar


def calculate_room_credits(booking, room):
    start_time = booking["start_ts"]
    end_time = booking["end_ts"]

    base_credits = room["credits_per_30min"]

    total_credits = 0
    current_time = start_time

    # Calculate the credits for each 30-minute slot
    while current_time < end_time:

        multiplier = 1

        # Check whether the booking is on a weekend
        if current_time.weekday() >= 5:
            multiplier = 0.5

        # Check whether the weekday slot is during peak hours
        elif current_time.hour >= 10 and current_time.hour < 13:
            multiplier = 1.5

        # Calculate credits for this 30-minute slot
        slot_credits = base_credits * multiplier

        # Round the slot credits up to the next whole number
        slot_credits = math.ceil(slot_credits)

        total_credits += slot_credits

        # Move to the next 30-minute slot
        current_time = current_time + timedelta(minutes=30)

    return total_credits


def calculate_carry_forward_limit(monthly_room_credits):
    # Members can carry forward a maximum of 25% of their monthly credits
    carry_forward_limit = monthly_room_credits * 0.25

    # Round down to the nearest whole credit
    return math.floor(carry_forward_limit)



def calculate_carry_forward_expiry(billing_cycle_start):
    # Find the month after the current billing cycle
    next_month = billing_cycle_start.month + 1
    next_year = billing_cycle_start.year

    # Handle December and move to January of the next year
    if next_month > 12:
        next_month = 1
        next_year += 1

    # Find the last day of the following month
    last_day = calendar.monthrange(next_year, next_month)[1]

    # Return the expiry date
    return date(next_year, next_month, last_day)


def remove_expired_carry_forward_credits(credit_buckets, current_date):
    valid_buckets = []

    # Check each carry-forward credit batch
    for bucket in credit_buckets:

        created_date = bucket["created_date"]

        # Calculate when this credit batch expires
        expiry_date = calculate_carry_forward_expiry(created_date)

        # Keep credits that have not expired
        if current_date <= expiry_date:
            valid_buckets.append(bucket)

    return valid_buckets


def consume_carry_forward_credits(credit_buckets, required_credits):
    # Arrange credit batches from oldest to newest
    credit_buckets = sorted(
        credit_buckets,
        key=lambda bucket: bucket["created_date"]
    )

    used_credits = 0
    remaining_buckets = []

    # Use the oldest available credits first
    for bucket in credit_buckets:

        available_credits = bucket["credits"]

        if required_credits > 0:
            credits_to_use = min(
                available_credits, required_credits
            )

            available_credits -= credits_to_use
            required_credits -= credits_to_use
            used_credits += credits_to_use

        # Keep batches that still have credits remaining
        if available_credits > 0:
            remaining_buckets.append({
                "credits": available_credits,
                "created_date": bucket["created_date"]
            })

    return used_credits, remaining_buckets



def calculate_room_overage(available_credits, required_credits):
    # Calculate credits that exceed the available balance
    overage_credits = required_credits - available_credits

    # Overage cannot be negative
    if overage_credits < 0:
        overage_credits = 0

    # Each additional room credit costs Rs. 150
    overage_amount = overage_credits * 150

    return {
        "overage_credits": overage_credits,
        "overage_amount": overage_amount
    }


def process_room_credit_usage(credit_buckets, monthly_credits_available,
                              required_credits, current_date):

    # First, remove carry-forward credits that have expired
    valid_buckets = remove_expired_carry_forward_credits(
        credit_buckets, current_date
    )

    # Consume valid carry-forward credits using FIFO
    carry_forward_used, remaining_buckets = consume_carry_forward_credits(
        valid_buckets, required_credits
    )

    # Calculate how many credits are still required
    remaining_required = required_credits - carry_forward_used

    # Use current month's credits after carry-forward credits
    monthly_credits_used = min(
        monthly_credits_available, remaining_required
    )

    # Calculate any remaining shortage as room credit overage
    overage = calculate_room_overage(
        monthly_credits_used,
        remaining_required
    )

    return {
        "carry_forward_used": carry_forward_used,
        "monthly_credits_used": monthly_credits_used,
        "remaining_buckets": remaining_buckets,
        "overage_credits": overage["overage_credits"],
        "overage_amount": overage["overage_amount"]
    }
