
from src.membership import calculate_upgrade_details
from datetime import date

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
