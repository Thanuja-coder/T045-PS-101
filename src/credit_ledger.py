
import math
from datetime import timedelta,date
import calendar



def calculate_room_credits(booking, room):
    start_time = booking["start_ts"]
    end_time = booking["end_ts"]

    base_credits = room["credits_per_30min"]

    off_peak_slots = 0
    peak_slots = 0
    weekend_slots = 0

    current_time = start_time

    # Count the different types of 30-minute slots
    while current_time < end_time:

        # Weekend bookings receive half credits
        if current_time.weekday() >= 5:
            weekend_slots += 1

        # Weekday peak hours are from 10 AM to 1 PM
        elif current_time.hour >= 10 and current_time.hour < 13:
            peak_slots += 1

        # All other weekday slots are off-peak
        else:
            off_peak_slots += 1

        current_time += timedelta(minutes=30)

    # Calculate credits for each category
    off_peak_credits = off_peak_slots * base_credits
    weekend_credits = weekend_slots * base_credits * 0.5

    # Round up the peak credits only once per booking
    peak_credits = math.ceil(
        peak_slots * base_credits * 1.5
    )

    total_credits = (
        off_peak_credits +
        weekend_credits +
        peak_credits
    )

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



def consume_carry_forward_credits(
        credit_buckets, required_credits, return_consumed=False):
    # Arrange credit batches from oldest to newest
    credit_buckets = sorted(
        credit_buckets,
        key=lambda bucket: bucket["created_date"]
    )

    used_credits = 0
    remaining_buckets = []
    consumed_buckets = []

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

            if credits_to_use > 0:
                consumed_buckets.append({
                    "credits": credits_to_use,
                    "created_date": bucket["created_date"]
                })

        if available_credits > 0:
            remaining_buckets.append({
                "credits": available_credits,
                "created_date": bucket["created_date"]
            })

    if return_consumed:
        return used_credits, remaining_buckets, consumed_buckets
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
    carry_forward_used, remaining_buckets, consumed_buckets = (
    consume_carry_forward_credits(
        valid_buckets,
        required_credits,
        return_consumed=True
    )
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
        "overage_amount": overage["overage_amount"],
        "carry_forward_consumed_buckets": consumed_buckets
    }

def restore_booking_credits(ledger, credit_usage, refund_credits):
    remaining_refund = refund_credits

    restored = {
        "overage": 0,
        "current": 0,
        "carry_forward": 0
    }

    # 1. Restore overage credits first
    overage_to_restore = min(
        credit_usage["overage_credits"],
        remaining_refund
    )

    if credit_usage["overage_credits"] > 0:
        amount_per_credit = (
            credit_usage["overage_amount"]
            / credit_usage["overage_credits"]
        )
        amount_to_restore = round(
            overage_to_restore * amount_per_credit
        )
    else:
        amount_to_restore = 0

    ledger["overage_credits"] -= overage_to_restore
    ledger["overage_amount"] -= amount_to_restore

    remaining_refund -= overage_to_restore
    restored["overage"] = overage_to_restore

    # 2. Restore current-month credits
    current_to_restore = min(
        credit_usage["monthly_credits_used"],
        remaining_refund
    )

    ledger["remaining_monthly_credits"] += current_to_restore
    ledger["monthly_credits_used"] -= current_to_restore

    remaining_refund -= current_to_restore
    restored["current"] = current_to_restore

    # 3. Restore carry-forward credits
    for bucket in credit_usage["carry_forward_consumed_buckets"]:
        if remaining_refund <= 0:
            break

        credits_to_restore = min(
            bucket["credits"],
            remaining_refund
        )

        original_bucket = None

        for existing in ledger["carry_forward_buckets"]:
            if existing["created_date"] == bucket["created_date"]:
                original_bucket = existing
                break

        if original_bucket is not None:
            original_bucket["credits"] += credits_to_restore
        else:
            ledger["carry_forward_buckets"].append({
                "credits": credits_to_restore,
                "created_date": bucket["created_date"]
            })

        ledger["carry_forward_used"] -= credits_to_restore
        remaining_refund -= credits_to_restore
        restored["carry_forward"] += credits_to_restore

    # Keep carry-forward buckets in oldest-first order
    ledger["carry_forward_buckets"].sort(
        key=lambda item: item["created_date"]
    )

    return restored