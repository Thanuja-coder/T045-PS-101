
from src.membership import calculate_upgrade_details
from datetime import date
from src.membership import calculate_upgrade_details
from src.booking import validate_freeze_start
from datetime import date, timedelta


def process_upgrade(member, new_plan_name, plans, requested_ts,
                    event_id, events):

    # The upgrade takes effect on the same day it is requested
    effective_date = requested_ts.date()

    # Calculate the additional fee and credits using the existing function
    upgrade_details = calculate_upgrade_details(
        member,
        new_plan_name,
        plans,
        effective_date
    )

    # Create the upgrade event using the existing CSV data structure
    event = {
        "event_id": event_id,
        "member_id": member["member_id"],
        "requested_ts": requested_ts,
        "event_type": "UPGRADE",
        "effective_date": effective_date,
        "new_plan": new_plan_name,
        "seats": member["seats"],
        "freeze_days": None
    }

    # Record the event
    events[event_id] = event

    # Update the member's current plan
    member["plan"] = new_plan_name

    return upgrade_details


def process_downgrade(member, new_plan_name, plans, requested_ts,
                      event_id, events):

    # Find the first day of the next calendar month
    next_month = requested_ts.month + 1
    next_year = requested_ts.year

    if next_month > 12:
        next_month = 1
        next_year += 1

    effective_date = date(next_year, next_month, 1)

    # Create the downgrade event
    event = {
        "event_id": event_id,
        "member_id": member["member_id"],
        "requested_ts": requested_ts,
        "event_type": "DOWNGRADE",
        "effective_date": effective_date,
        "new_plan": new_plan_name,
        "seats": member["seats"],
        "freeze_days": None,
        "old_plan": member["plan"]
    }

    # Record the scheduled downgrade
    events[event_id] = event

    # Return the scheduled change details
    return event


def process_freeze(member, freeze_days, effective_date, requested_ts,
                   event_id, events, accepted_bookings):

    # Check whether the requested freeze duration is valid
    if freeze_days < 15 or freeze_days > 60:
        raise ValueError("Freeze duration must be between 15 and 60 days")

    # Calculate the last day of the freeze
    freeze_end = effective_date + timedelta(days=freeze_days - 1)

    # A freeze must start and end in the same calendar year
    if effective_date.year != freeze_end.year:
        raise ValueError("Freeze must end within the same calendar year")

    # Calculate how many valid freeze days the member has already used
    used_freeze_days = 0

    for event in events.values():
        if event["member_id"] != member["member_id"]:
            continue

        if event["event_type"] != "FREEZE":
            continue

        previous_days = event["freeze_days"]
        previous_start = event["effective_date"]

        # Ignore invalid historical freeze records
        if previous_days < 15 or previous_days > 60:
            continue

        previous_end = previous_start + timedelta(days=previous_days - 1)

        if previous_start.year != previous_end.year:
            continue

        # Count freezes that belong to the same calendar year
        if previous_start.year == effective_date.year:
            used_freeze_days += previous_days

    # The member cannot use more than 60 freeze days in one year
    if used_freeze_days + freeze_days > 60:
        raise ValueError("Member cannot use more than 60 freeze days per year")

    # Prepare the freeze event for the existing booking validation
    freeze_event = {
        "event_id": event_id,
        "member_id": member["member_id"],
        "requested_ts": requested_ts,
        "event_type": "FREEZE",
        "effective_date": effective_date,
        "new_plan": None,
        "seats": member["seats"],
        "freeze_days": freeze_days
    }

    # Reuse the existing future-booking validation
    validate_freeze_start(freeze_event, accepted_bookings)

    # Record the freeze only after all validations pass
    events[event_id] = freeze_event

    return freeze_event