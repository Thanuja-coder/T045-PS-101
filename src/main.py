
from pathlib import Path

from src.data_loader import (
    load_plans,
    load_members,
    load_rooms,
    load_bookings,
    load_plan_events
)
from src.command_parser import load_commands

from datetime import datetime,date
from src.cancellation import (
    calculate_cancellation_refund,
    check_booking_no_show
)
from src.credit_ledger import (
    calculate_room_credits,
    process_room_credit_usage,calculate_carry_forward_limit,
    calculate_carry_forward_expiry
)
from src.membership import (
    calculate_membership_allowance,
    calculate_freeze_allowance
)
from src.cancellation import (
    calculate_cancellation_refund,
    check_booking_no_show,
    calculate_no_show_fee
)

from src.invoice import (
    build_invoice_record,
    write_invoice_records,
    calculate_freeze_waiver,
    calculate_freeze_adjustment
)
def create_monthly_credit_ledger(member, plans, billing_month, freeze_events):

    freeze_event_dict = {
        str(index): event
        for index, event in enumerate(freeze_events)
    }

    allowance = calculate_freeze_allowance(
        member,
        plans,
        billing_month,
        freeze_event_dict
    )

    carry_forward_buckets = []

    opening_credits = member["opening_carry_credits"]

    if opening_credits > 0:
        carry_forward_buckets.append({
            "credits": opening_credits,
            "created_date": billing_month
        })

    ledger = {
        "member_id": member["member_id"],
        "billing_month": billing_month,
        "monthly_credits": allowance["room_credits"],
        "remaining_monthly_credits": allowance["room_credits"],
        "carry_forward_buckets": carry_forward_buckets,
        "carry_forward_used": 0,
        "monthly_credits_used": 0,
        "overage_credits": 0,
        "overage_amount": 0
    }

    return ledger

def create_carry_forward_bucket(ledger, billing_month):
    unused_credits = ledger["remaining_monthly_credits"]

    carry_limit = calculate_carry_forward_limit(
        ledger["monthly_credits"]
    )

    carry_credits = min(unused_credits, carry_limit)

    if carry_credits <= 0:
        return None

    return {
        "credits": carry_credits,
        "created_date": billing_month
    }

def process_commands(commands, bookings, members, rooms, plans, events):
    from src.booking import validate_booking
    from src.plan_manager import (
        process_upgrade,
        process_downgrade,
        process_freeze
    )

    accepted_bookings = []
    booking_decisions = []
    active_freeze_events = []

    check_ins = {}
    cancelled_bookings = {}
    booking_refunds = {}

    no_show_counts = {}
    no_show_fees = {}
    processed_no_shows = set()

    credit_ledgers = {}
    monthly_allowances = {}
    room_overage_records = {}

    upgrade_charges = {}
    freeze_records = []
    invoices = []
    
    for command in commands:
        action = command["action"]
        arguments = command["arguments"]
        
        if action == "CHECKIN":
            booking_id = arguments[0]
            check_in_time = datetime.strptime(
                arguments[1], "%Y-%m-%d %H:%M:%S"
            )

            booking = bookings[booking_id]

            if booking_id not in [
                item["booking_id"] for item in accepted_bookings
            ]:
                print("REJECT CHECKIN:", booking_id, "Booking not accepted")

            elif booking_id in cancelled_bookings:
                print("REJECT CHECKIN:", booking_id, "Booking cancelled")

            elif check_booking_no_show(
                booking["start_ts"],
                check_in_time,
                check_in_time
            ):
                print("REJECT CHECKIN:", booking_id, "Check-in window expired")

            else:
                check_ins[booking_id] = check_in_time
                print("CHECKIN:", booking_id, "recorded")

        elif action == "CANCEL":
            booking_id = arguments[0]
            cancellation_time = datetime.strptime(
                arguments[1], "%Y-%m-%d %H:%M:%S"
            )

            booking = bookings[booking_id]

            if booking_id not in [
                item["booking_id"] for item in accepted_bookings
            ]:
                print("REJECT CANCEL:", booking_id, "Booking not accepted")

            elif booking_id in check_ins:
                print("REJECT CANCEL:", booking_id, "Already checked in")

            else:
                try:
                    if booking["resource"] in rooms:
                        room_credits = calculate_room_credits(
                            booking,
                            rooms[booking["resource"]]
                        )
                    else:
                        room_credits = 0

                    refund = calculate_cancellation_refund(
                        room_credits,
                        booking["start_ts"],
                        cancellation_time
                    )

                    booking_refunds[booking_id] = refund
                    cancelled_bookings[booking_id] = cancellation_time

                    accepted_bookings.remove(booking)

                    print(
                        "CANCEL:", booking_id,
                        "Refund credits:", refund
                    )

                except ValueError as error:
                    print("REJECT CANCEL:", booking_id, error)

        if action == "PLAN_EVENT":
            event_id = arguments[0]
            event = events[event_id]

            member = members[event["member_id"]]

            try:
                if event["event_type"] == "UPGRADE":
                    upgrade_details = process_upgrade( member,event["new_plan"],plans,event["requested_ts"],event_id, events)
                    billing_month = date(
    event["requested_ts"].year,
    event["requested_ts"].month,
    1
)
                    charge_key = (member["member_id"], billing_month)
                    upgrade_charges[charge_key] = (upgrade_charges.get(charge_key, 0)+ upgrade_details["additional_fee"]
                                                   )
                    print("UPGRADE:", event_id, "processed")

                elif event["event_type"] == "DOWNGRADE":
                    process_downgrade(
                        member,
                        event["new_plan"],
                        plans,
                        event["requested_ts"],
                        event_id,
                        events
                    )

                    print("DOWNGRADE:", event_id, "scheduled")

                elif event["event_type"] == "FREEZE":
                    previous_events = {
                        key: value
                        for key, value in events.items()
                        if key != event_id
                        and value["requested_ts"] <= event["requested_ts"]
                    }

                    freeze_event = process_freeze(
                        member,
                        event["freeze_days"],
                        event["effective_date"],
                        event["requested_ts"],
                        event_id,
                        previous_events,
                        accepted_bookings
                    )
                    events[event_id] = freeze_event
                    active_freeze_events.append(freeze_event)
                    freeze_records.append({
    "member_id": member["member_id"],
    "requested_ts": event["requested_ts"],
    "effective_date": event["effective_date"],
    "freeze_days": event["freeze_days"],
    "monthly_plan_fee": calculate_membership_allowance(
        member, plans
    )["plan_fee"]
})
                    print("FREEZE:", event_id, "processed")

            except ValueError as error:
                print("REJECT PLAN EVENT:", event_id, error)

        
        elif action == "BOOK":
            booking_id = arguments[0]
            booking = bookings[booking_id]
            member = members[booking["member_id"]]

            try:
                validate_booking(
                    booking,
                    member,
                    rooms,
                    plans,
                    accepted_bookings,
                    active_freeze_events
                )

                # Process credits only for meeting-room bookings
                if booking["resource"] in rooms:

                    billing_month = date(
                        booking["start_ts"].year,
                        booking["start_ts"].month,
                        1
                    )

                    ledger_key = (
                        member["member_id"],
                        billing_month
                    )

                    # Create the monthly ledger if it does not exist
                    if ledger_key not in credit_ledgers:
                        credit_ledgers[ledger_key] = (
                            create_monthly_credit_ledger(
                                member,
                                plans,
                                billing_month,
                                active_freeze_events
                            )
                        )

                    ledger = credit_ledgers[ledger_key]

                    required_credits = calculate_room_credits(
                        booking,
                        rooms[booking["resource"]]
                    )

                    usage = process_room_credit_usage(
                        ledger["carry_forward_buckets"],
                        ledger["remaining_monthly_credits"],
                        required_credits,
                        booking["start_ts"].date()
                    )

                    # Update the member's monthly balance
                    ledger["carry_forward_buckets"] = (
                        usage["remaining_buckets"]
                    )

                    ledger["remaining_monthly_credits"] -= (
                        usage["monthly_credits_used"]
                    )

                    ledger["carry_forward_used"] += (
                        usage["carry_forward_used"]
                    )

                    ledger["monthly_credits_used"] += (
                        usage["monthly_credits_used"]
                    )

                    ledger["overage_credits"] += (
                        usage["overage_credits"]
                    )

                    ledger["overage_amount"] += (
                        usage["overage_amount"]
                    )

                accepted_bookings.append(booking)
                print("ACCEPT:", booking_id)
            except ValueError as error:
                print("REJECT:", booking_id, error)
        
        
        elif action == "CLOSE_CYCLE":
            billing_month = datetime.strptime(
                arguments[0], "%Y-%m"
            ).date()
            
            # Process ROOM no-shows for this billing month
            next_month = billing_month.month + 1
            next_year = billing_month.year

            if next_month > 12:
                next_month = 1
                next_year += 1

            cycle_close_time = datetime(
                next_year,
                next_month,
                1
            )

            for booking in accepted_bookings:

                booking_id = booking["booking_id"]
                member_id = booking["member_id"]

                booking_month = date(
                    booking["start_ts"].year,
                    booking["start_ts"].month,
                    1
                )

                if booking_month != billing_month:
                    continue

                # Only meeting-room bookings have no-show fees
                if booking["resource"] not in rooms:
                    continue

                if booking_id in processed_no_shows:
                    continue

                if booking_id in check_ins:
                    continue
                if booking_id in cancelled_bookings:
                    continue
                if check_booking_no_show(
                    booking["start_ts"],
                    None,
                    cycle_close_time
                ):
                    processed_no_shows.add(booking_id)

                    count_key = (member_id, billing_month)

                    no_show_counts[count_key] = (
                        no_show_counts.get(count_key, 0) + 1
                    )

                    fee = calculate_no_show_fee(
                        no_show_counts[count_key]
                    )

                    no_show_fees[count_key] = (
                        no_show_fees.get(count_key, 0) + fee
                    )

                    print(
                        "NO SHOW:",
                        booking_id,
                        "Count:",
                        no_show_counts[count_key],
                        "Fee:",
                        fee
                    )

            for member_id, member in members.items():

                ledger_key = (member_id, billing_month)

                # Create a ledger even if the member made no room bookings
                if ledger_key not in credit_ledgers:
                    credit_ledgers[ledger_key] = (
                        create_monthly_credit_ledger(
                            member,
                            plans,
                            billing_month,
                            active_freeze_events
                        )
                    )

                ledger = credit_ledgers[ledger_key]

                carry_bucket = create_carry_forward_bucket(
                    ledger,
                    billing_month
                )

                if carry_bucket is not None:

                    next_month = billing_month.month + 1
                    next_year = billing_month.year

                    if next_month > 12:
                        next_month = 1
                        next_year += 1

                    next_month_date = date(
                        next_year,
                        next_month,
                        1
                    )

                    next_ledger_key = (
                        member_id,
                        next_month_date
                    )

                    if next_ledger_key not in credit_ledgers:
                        credit_ledgers[next_ledger_key] = (
                            create_monthly_credit_ledger(
                                member,
                                plans,
                                next_month_date,
                                active_freeze_events
                            )
                        )

                    credit_ledgers[next_ledger_key][
                        "carry_forward_buckets"
                    ].append(carry_bucket)
                    
            # Generate one invoice for every member
            for member_id, member in members.items():

                ledger_key = (member_id, billing_month)
                ledger = credit_ledgers[ledger_key]

                # Get the monthly plan fee
                plan_fee = calculate_membership_allowance(
                    member, plans
                )["plan_fee"]

                # Get room overage amount
                room_overage = ledger["overage_amount"]

                # Get upgrade charges
                upgrade_amount = upgrade_charges.get(
                    ledger_key, 0
                )

                # Get no-show fees
                no_show_amount = no_show_fees.get(
                    ledger_key, 0
                )

                freeze_fee_total = 0
                freeze_waiver_total = 0

                # Calculate freeze fees and monthly waivers
                for freeze in freeze_records:

                    if freeze["member_id"] != member_id:
                        continue

                    waiver_details = calculate_freeze_waiver(
                        freeze["monthly_plan_fee"],
                        freeze["effective_date"],
                        freeze["freeze_days"]
                    )

                    for breakdown in waiver_details["monthly_breakdown"]:

                        if breakdown["billing_month"] == billing_month.strftime("%Y-%m"):

                            adjustment = calculate_freeze_adjustment(
                                breakdown["waiver"],
                                False
                            )

                            freeze_waiver_total += (
                                adjustment["invoice_waiver"]
                            )

                    requested_month = date(
                        freeze["requested_ts"].year,
                        freeze["requested_ts"].month,
                        1
                    )

                    if requested_month == billing_month:
                        freeze_fee_total += 500

                # Create invoice
                invoice_id = (
                    f"INV-{member_id}-"
                    f"{billing_month.year}"
                    f"{billing_month.month:02d}"
                )

                invoice = build_invoice_record(
                    invoice_id,
                    member_id,
                    plan_fee,
                    upgrade_charges=upgrade_amount,
                    room_overage=room_overage,
                    no_show_fees=no_show_amount,
                    freeze_fees=freeze_fee_total,
                    freeze_waiver=freeze_waiver_total
                )

                invoices.append(invoice)

            print("CLOSE CYCLE:", billing_month, "processed")

                
    return accepted_bookings, booking_decisions, invoices




def main():
    # Load all project data
    plans = load_plans()
    members = load_members()
    rooms = load_rooms()
    bookings = load_bookings()
    events = load_plan_events()

    # Store results generated while processing commands
    accepted_bookings = []
    booking_decisions = []
    credit_ledgers = []
    invoices = []
    payments = {}

    # Load commands in their original file order
    commands = load_commands()

    print("Project data loaded successfully.")
    print("Members:", len(members))
    print("Bookings:", len(bookings))
    print("Commands:", len(commands))

    accepted_bookings, booking_decisions, invoices = process_commands(
    commands,
    bookings,
    members,
    rooms,
    plans,
    events
)
        # Create output folder if it does not exist
    Path("output").mkdir(exist_ok=True)

    # Save monthly invoices
    write_invoice_records(
        invoices,
        "output/invoices.csv"
    )

    print("Invoices generated:", len(invoices))
    print("Invoice file saved: output/invoices.csv")
    print("Accepted bookings:", len(accepted_bookings))


if __name__ == "__main__":
    main()
