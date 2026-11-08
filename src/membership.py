import calendar
from decimal import Decimal, ROUND_HALF_UP
import math

def validate_member(member,plans,members):
    member_id=member["member_id"]
    plan_name=member["plan"]
    seats=member["seats"]

    if member_id in members:
        raise ValueError(f"Member ID already exists: {member_id}")

    if plan_name not in plans:
        raise ValueError(f"Plan does not exist: {plan_name}")
    if seats < 1 :
        raise ValueError(f"Seats must be at least 1 for member ID: {member_id}")

    minimum_seats = plans[plan_name]["min_seats"]
    
    if minimum_seats is not None and seats < minimum_seats:
        raise ValueError(
            f"{plan_name} requires at least {minimum_seats} seats"
        )

    return True


def register_member(member, plans, members):
    validate_member(member, plans, members)

    members[member["member_id"]] = member

    return member



def calculate_membership_allowance(member, plans):
    plan_name = member["plan"]
    seats = member["seats"]

    plan = plans[plan_name]

    # Calculate room credits
    room_credits = plan["room_credits"]

    if plan["unit"] == "per seat per month":
        room_credits = room_credits * seats

    # Calculate plan fee
    plan_fee = plan["monthly_fee"]

    if plan["unit"] == "per seat per month":
        plan_fee = plan_fee * seats

    return {
        "member_id": member["member_id"],
        "plan": plan_name,
        "plan_fee": plan_fee,
        "fee_unit": plan["unit"],
        "desk_days": plan["desk_days"],
        "room_credits": room_credits,
        "opening_carry_credits": member["opening_carry_credits"]
    }

def calculate_upgrade_details(member, new_plan_name, plans, effective_date):

    # Check whether the new plan exists
    if new_plan_name not in plans:
        raise ValueError(f"Plan does not exist: {new_plan_name}")

    # Get the current plan details
    old_allowance = calculate_membership_allowance(member, plans)

    # Create a copy of the member with the new plan
    new_member = member.copy()
    new_member["plan"] = new_plan_name

    # Get the new plan details
    new_allowance = calculate_membership_allowance(new_member, plans)

    # Both plans must be monthly plans for this calculation
    if old_allowance["fee_unit"] not in ("per month", "per seat per month"):
        raise ValueError("Current plan must be a monthly plan")

    if new_allowance["fee_unit"] not in ("per month", "per seat per month"):
        raise ValueError("New plan must be a monthly plan")

    # Calculate the number of days in the effective month
    days_in_month = calendar.monthrange(
        effective_date.year,
        effective_date.month
    )[1]

    # Include the effective date in the remaining days
    remaining_days = days_in_month - effective_date.day + 1

    # Calculate the difference between the two plan fees
    fee_difference = (
        new_allowance["plan_fee"] - old_allowance["plan_fee"]
    )

    # Calculate the additional fee for the remaining days
    additional_fee = (
        fee_difference * Decimal(remaining_days) / Decimal(days_in_month)
    )

    # Round the additional fee to the nearest rupee
    additional_fee = additional_fee.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    # Calculate the difference in room credits
    credit_difference = (
        new_allowance["room_credits"] - old_allowance["room_credits"]
    )

    # Calculate additional credits proportionally
    additional_credits = (
        credit_difference * remaining_days / days_in_month
    )

    # Round additional credits down
    additional_credits = math.floor(additional_credits)

    return {
        "member_id": member["member_id"],
        "old_plan": member["plan"],
        "new_plan": new_plan_name,
        "effective_date": effective_date,
        "remaining_days": remaining_days,
        "days_in_month": days_in_month,
        "additional_fee": additional_fee,
        "additional_room_credits": additional_credits
    }