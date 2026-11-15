
import math
from pathlib import Path

from src.reports import (
    write_reports,
    print_booking_register,
    print_member_credit_ledger,
    print_monthly_invoices
)

from src.data_loader import (
    load_plans,
    load_members,
    load_rooms,
    load_bookings,
    load_plan_events
)
from src.command_parser import load_commands

from src.booking import BookingValidationError

from datetime import datetime,date,timedelta

from src.cancellation import (
    calculate_cancellation_refund,
    check_booking_no_show
)
from src.credit_ledger import (
    calculate_room_credits,
    process_room_credit_usage,calculate_carry_forward_limit,
    calculate_carry_forward_expiry,restore_booking_credits
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
    calculate_freeze_adjustment,
    calculate_late_interest
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
    if opening_credits > 0 and billing_month == date(2026, 1, 1):
        previous_month = billing_month - timedelta(days=1)
        carry_forward_buckets.append({
        "credits": opening_credits,
        "created_date": previous_month.replace(day=1)
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

    carry_credits = math.floor(
        min(unused_credits, carry_limit)
)

    if carry_credits <= 0:
        return None

    return {
        "credits": carry_credits,
        "created_date": billing_month
    }


def record_ledger_entry(
    ledger_entries,
    ledger,
    ts,
    entry,
    reference,
    credits
):
    carry_balance = sum(
        bucket["credits"]
        for bucket in ledger["carry_forward_buckets"]
    )

    ledger_entries.append({
        "member_id": ledger["member_id"],
        "ts": ts,
        "entry": entry,
        "reference": reference,
        "credits": credits,
        "carry_balance": carry_balance,
        "current_balance": ledger["remaining_monthly_credits"],
        "overage_credits": ledger["overage_credits"]
    })

def process_commands(
    commands,
    bookings,
    members,
    rooms,
    plans,
    events,
    unpaid_invoice_members=None
):
    from src.booking import validate_booking, BookingValidationError
    from src.plan_manager import (
        process_upgrade,
        process_downgrade,
        process_freeze
    )

    if unpaid_invoice_members is None:
        unpaid_invoice_members = set()

    accepted_bookings = []
    booking_decisions = []
    credit_ledger_entries = []
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
    monthly_plan_fees = {}
    freeze_records = []
    invoices = []

    # Track desk days used through successful check-ins.
    desk_checkin_days = {}

    # Track unpaid invoices and their issue dates.
    unpaid_invoices = {}
    invoice_issue_dates = {}
    invoice_billing_months = {}

    # Track late interest already calculated for each invoice.
    invoice_interest_accrued = {}

    # Late interest is added to the next monthly invoice.
    late_interest_by_month = {}


    def record_late_interest(invoice_id, calculation_time, target_month):
        invoice = unpaid_invoices[invoice_id]
        issue_date = invoice_issue_dates[invoice_id]

        days_late = max(
            0,
            (calculation_time.date() - issue_date.date()).days - 7
        )

        if days_late <= 0:
            return

        total_interest = calculate_late_interest(
            invoice["total"],
            days_late
        )

        already_recorded = invoice_interest_accrued.get(
            invoice_id, 0
        )

        new_interest = total_interest - already_recorded

        if new_interest > 0:
            key = (invoice["member_id"], target_month)

            late_interest_by_month[key] = (
                late_interest_by_month.get(key, 0) + new_interest
            )

        invoice_interest_accrued[invoice_id] = total_interest

    def add_booking_decision(
        ts,
        booking,
        action,
        result,
        rule_id="",
        credits=0,
        from_carry=0,
        from_current=0,
        overage=0,
        refund=0
    ):
        booking_decisions.append({
            "ts": ts,
            "booking_id": booking["booking_id"],
            "member_id": booking["member_id"],
            "action": action,
            "result": result,
            "rule_id": rule_id,
            "credits": credits,
            "from_carry": from_carry,
            "from_current": from_current,
            "overage": overage,
            "refund": refund
        })

    for command in commands:
        action = command["action"]
        arguments = command["arguments"]

        # --------------------------------------------------
        # CHECKIN
        # --------------------------------------------------
        if action == "CHECKIN":
            booking_id = arguments[0]
            check_in_time = datetime.strptime(
                arguments[1], "%Y-%m-%d %H:%M:%S"
            )

            booking = bookings[booking_id]

            if booking_id not in [
                item["booking_id"] for item in accepted_bookings
            ]:
                print(
                    "REJECT CHECKIN:",
                    booking_id,
                    "Booking not accepted"
                )

                add_booking_decision(
                    check_in_time, booking, "CHECKIN", "REJECT"
                )

            elif booking_id in cancelled_bookings:
                print(
                    "REJECT CHECKIN:",
                    booking_id,
                    "Booking cancelled"
                )

                add_booking_decision(
                    check_in_time, booking, "CHECKIN", "REJECT"
                )

            elif check_booking_no_show(
                booking["start_ts"],
                check_in_time,
                check_in_time
            ):
                print(
                    "REJECT CHECKIN:",
                    booking_id,
                    "Check-in window expired"
                )

                add_booking_decision(
                    check_in_time,
                    booking,
                    "CHECKIN",
                    "REJECT",
                    "BR-07"
                )

            else:
                check_ins[booking_id] = check_in_time

                                # Desk usage is counted only after successful check-in.
                if booking["resource"] == "HOT_DESK":
                    billing_month = date(
                        check_in_time.year,
                        check_in_time.month,
                        1
                    )

                    desk_key = (
                        booking["member_id"],
                        billing_month
                    )

                    if desk_key not in desk_checkin_days:
                        desk_checkin_days[desk_key] = set()

                    desk_checkin_days[desk_key].add(
                        check_in_time.date()
                    )

                print("CHECKIN:", booking_id, "recorded")

                add_booking_decision(
                    check_in_time, booking, "CHECKIN", "ACCEPT"
                )

        # --------------------------------------------------
        # CANCEL
        # --------------------------------------------------
        elif action == "CANCEL":
            booking_id = arguments[0]
            cancellation_time = datetime.strptime(
                arguments[1], "%Y-%m-%d %H:%M:%S"
            )

            booking = bookings[booking_id]

            if booking_id not in [
                item["booking_id"] for item in accepted_bookings
            ]:
                print(
                    "REJECT CANCEL:",
                    booking_id,
                    "Booking not accepted"
                )

                add_booking_decision(
                    cancellation_time, booking, "CANCEL", "REJECT"
                )

            elif booking_id in check_ins:
                print(
                    "REJECT CANCEL:",
                    booking_id,
                    "Already checked in"
                )

                add_booking_decision(
                    cancellation_time, booking, "CANCEL", "REJECT"
                )

            else:
                try:
                    if booking["resource"] in rooms:
                        room_credits = calculate_room_credits(
                            booking,
                            rooms[booking["resource"]]
                        )

                        refund = calculate_cancellation_refund(
                            room_credits,
                            booking["start_ts"],
                            cancellation_time
                        )
                    else:
                        # Desk bookings do not use room credits.
                        room_credits = 0
                        refund = 0

                    restored_credits = {
                        "overage": 0,
                        "current": 0,
                        "carry_forward": 0
                    }

                    if (
                        booking["resource"] in rooms
                        and refund > 0
                    ):
                        billing_month = date(
                            booking["start_ts"].year,
                            booking["start_ts"].month,
                            1
                        )

                        ledger_key = (
                            booking["member_id"],
                            billing_month
                        )

                        ledger = credit_ledgers[ledger_key]

                        restored_credits = restore_booking_credits(
                            ledger,
                            booking["credit_usage"],
                            refund
                        )

                    booking["refund_usage"] = restored_credits
                    if refund > 0 and booking["resource"] in rooms:
                        billing_month = date(
                            booking["start_ts"].year,
                            booking["start_ts"].month,
                            1
                        )

                        ledger = credit_ledgers[
                            (booking["member_id"], billing_month)
                        ]

                        record_ledger_entry(
                            credit_ledger_entries,
                            ledger,
                            cancellation_time,
                            "REFUND",
                            booking_id,
                            refund
                        )
                    booking_refunds[booking_id] = refund
                    cancelled_bookings[booking_id] = cancellation_time

                    accepted_bookings.remove(booking)

                    print(
                        "CANCEL:",
                        booking_id,
                        "Refund credits:",
                        refund
                    )

                    add_booking_decision(
                        cancellation_time,
                        booking,
                        "CANCEL",
                        "ACCEPT",
                        "BR-07",
                        credits=refund,
                        from_carry=restored_credits["carry_forward"],
                        from_current=restored_credits["current"],
                        overage=restored_credits["overage"],
                        refund=refund
                    )

                except ValueError as error:
                    print("REJECT CANCEL:", booking_id, error)

                    add_booking_decision(
                        cancellation_time,
                        booking,
                        "CANCEL",
                        "REJECT",
                        "BR-07"
                    )

        
        # --------------------------------------------------
        # PLAN EVENT
        # --------------------------------------------------
        elif action == "PLAN_EVENT":
            event_id = arguments[0]
            event = events[event_id]

            member = members[event["member_id"]]

            try:
                if event["event_type"] == "UPGRADE":

                    billing_month = date(
                        event["requested_ts"].year,
                        event["requested_ts"].month,
                        1
                    )

                    charge_key = (
                        member["member_id"],
                        billing_month
                    )

                    # Preserve the original plan fee before upgrading.
                    original_plan_fee = calculate_membership_allowance(
                        member,
                        plans
                    )["plan_fee"]

                    # Create the ledger before changing the member's plan.
                    # This ensures the original plan's credits are granted.
                    if charge_key not in credit_ledgers:

                        credit_ledgers[charge_key] = (
                            create_monthly_credit_ledger(
                                member,
                                plans,
                                billing_month,
                                active_freeze_events
                            )
                        )

                        ledger = credit_ledgers[charge_key]

                        record_ledger_entry(
                            credit_ledger_entries,
                            ledger,
                            billing_month,
                            "GRANT",
                            "MONTHLY_PLAN",
                            ledger["monthly_credits"]
                        )

                    ledger = credit_ledgers[charge_key]

                    # Process the upgrade and calculate the prorated difference.
                    upgrade_details = process_upgrade(
                        member,
                        event["new_plan"],
                        plans,
                        event["requested_ts"],
                        event_id,
                        events
                    )

                    # Add only the additional prorated room credits.
                    additional_credits = (
                        upgrade_details["additional_room_credits"]
                    )

                    ledger["monthly_credits"] += additional_credits

                    ledger["remaining_monthly_credits"] += (
                        additional_credits
                    )

                    # Record the additional credits in the ledger.
                    if additional_credits > 0:
                        record_ledger_entry(
                            credit_ledger_entries,
                            ledger,
                            event["requested_ts"],
                            "UPGRADE",
                            event_id,
                            additional_credits
                        )

                    # Preserve the original plan fee for this month.
                    if charge_key not in monthly_plan_fees:
                        monthly_plan_fees[charge_key] = original_plan_fee

                    # Add the upgrade charge to this month's invoice.
                    upgrade_charges[charge_key] = (
                        upgrade_charges.get(charge_key, 0)
                        + upgrade_details["additional_fee"]
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
                            member,
                            plans
                        )["plan_fee"]
                    })

                    print("FREEZE:", event_id, "processed")

            except ValueError as error:
                print("REJECT PLAN EVENT:", event_id, error)


        # --------------------------------------------------
        # BOOK
        # --------------------------------------------------
        elif action == "BOOK":
            booking_id = arguments[0]
            booking = bookings[booking_id]
            member = members[booking["member_id"]]

            booking_time = booking["requested_ts"]

            try:
                # First apply format, capacity and precedence checks.
                validate_booking(
                    booking,
                    member,
                    rooms,
                    plans,
                    accepted_bookings,
                    active_freeze_events
                )

                usage = {
                    "carry_forward_used": 0,
                    "monthly_credits_used": 0,
                    "overage_credits": 0,
                    "overage_amount": 0,
                    "carry_forward_consumed_buckets": []
                }

                # Room bookings use the monthly credit ledger.
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
                    if ledger_key not in credit_ledgers:
                        credit_ledgers[ledger_key] = create_monthly_credit_ledger(
                            member,
                            plans,
                            billing_month,
                            active_freeze_events
                        )

                        # Record the monthly grant only when the ledger is first created.
                        ledger = credit_ledgers[ledger_key]

                        record_ledger_entry(
                            credit_ledger_entries,
                            ledger,
                            billing_month,
                            "GRANT",
                            "MONTHLY_PLAN",
                            ledger["monthly_credits"]
                        )

                    ledger = credit_ledgers[ledger_key]
                    required_credits = calculate_room_credits(
                        booking,
                        rooms[booking["resource"]]
                    )
                    # Remove expired carry-forward credits before using the ledger.
                    valid_buckets = []
                    expired_credits = 0

                    for bucket in ledger["carry_forward_buckets"]:
                        expiry_date = calculate_carry_forward_expiry(
                            bucket["created_date"]
                        )

                        if booking["start_ts"].date() > expiry_date:
                            expired_credits += bucket["credits"]
                        else:
                            valid_buckets.append(bucket)

                    # Update the ledger before recording the expiry movement.
                    ledger["carry_forward_buckets"] = valid_buckets

                    if expired_credits > 0:
                        record_ledger_entry(
                            credit_ledger_entries,
                            ledger,
                            booking["requested_ts"],
                            "EXPIRE",
                            booking_id,
                            expired_credits
                        )

                    # Calculate carry-forward first, then current credits.
                    usage = process_room_credit_usage(
                        ledger["carry_forward_buckets"],
                        ledger["remaining_monthly_credits"],
                        required_credits,
                        booking["start_ts"].date()
                    )

                    # BR-04: unpaid invoice blocks only overage bookings.
                    if (
                        usage["overage_credits"] > 0
                        and member["member_id"] in unpaid_invoice_members
                    ):
                        raise BookingValidationError(
                            "Unpaid previous invoice prevents overage booking",
                            "BR-04"
                        )

                    # Store the credit breakdown for this booking.
                    booking["credit_usage"] = {
                        "carry_forward_used": usage["carry_forward_used"],
                        "monthly_credits_used": usage["monthly_credits_used"],
                        "overage_credits": usage["overage_credits"],
                        "overage_amount": usage["overage_amount"],
                        "carry_forward_consumed_buckets": (
                            usage["carry_forward_consumed_buckets"]
                        )
                    }

                    # Update monthly ledger balances.
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
                    # Record each type of credit movement separately.
                    if usage["carry_forward_used"] > 0:
                        record_ledger_entry(
                            credit_ledger_entries,
                            ledger,
                            booking["requested_ts"],
                            "CONSUME_CARRY",
                            booking_id,
                            usage["carry_forward_used"]
                        )

                    if usage["monthly_credits_used"] > 0:
                        record_ledger_entry(
                            credit_ledger_entries,
                            ledger,
                            booking["requested_ts"],
                            "CONSUME",
                            booking_id,
                            usage["monthly_credits_used"]
                        )

                    if usage["overage_credits"] > 0:
                        record_ledger_entry(
                            credit_ledger_entries,
                            ledger,
                            booking["requested_ts"],
                            "OVERAGE",
                            booking_id,
                            usage["overage_credits"]
                        )
                # Accept the booking only after all checks pass.
                accepted_bookings.append(booking)

                print("ACCEPT:", booking_id)

                add_booking_decision(
                    booking_time,
                    booking,
                    "BOOK",
                    "ACCEPT",
                    credits=(
                        usage["carry_forward_used"]
                        + usage["monthly_credits_used"]
                        + usage["overage_credits"]
                    ),
                    from_carry=usage["carry_forward_used"],
                    from_current=usage["monthly_credits_used"],
                    overage=usage["overage_credits"]
                )

            except ValueError as error:
                print("REJECT:", booking_id, error)

                add_booking_decision(
                    booking_time,
                    booking,
                    "BOOK",
                    "REJECT",
                    getattr(error, "rule_id", "")
                )

        # --------------------------------------------------
        # CLOSE CYCLE
        # --------------------------------------------------
        elif action == "CLOSE_CYCLE":
            billing_month = datetime.strptime(
                arguments[0], "%Y-%m"
            ).date()

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

            # Process room no-shows for this billing month.
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

                    no_show_credits = booking.get(
                        "credit_usage", {}
                    )

                    forfeited_credits = (
                        no_show_credits.get("carry_forward_used", 0)
                        + no_show_credits.get("monthly_credits_used", 0)
                        + no_show_credits.get("overage_credits", 0)
                    )

                    add_booking_decision(
                        booking["start_ts"] + timedelta(minutes=15),
                        booking,
                        "NO_SHOW",
                        "REJECT",
                        "BR-07",
                        credits=forfeited_credits
                    )

            # Create carry-forward balances for every member.
            for member_id, member in members.items():
                ledger_key = (member_id, billing_month)

                if ledger_key not in credit_ledgers:
                    credit_ledgers[ledger_key] = create_monthly_credit_ledger(
                        member,
                        plans,
                        billing_month,
                        active_freeze_events
                    )

                    # Record the grant only when this month's ledger is created.
                    ledger = credit_ledgers[ledger_key]

                    record_ledger_entry(
                        credit_ledger_entries,
                        ledger,
                        billing_month,
                        "GRANT",
                        "MONTHLY_PLAN",
                        ledger["monthly_credits"]
                    )

                ledger = credit_ledgers[ledger_key]
                # Calculate the next month's date.
                next_month_date = date(
                    next_year,
                    next_month,
                    1
                )

                next_ledger_key = (
                    member_id,
                    next_month_date
                )

                # Create next month's ledger if it does not exist.
                if next_ledger_key not in credit_ledgers:
                    credit_ledgers[next_ledger_key] = create_monthly_credit_ledger(
                         member,plans,next_month_date,active_freeze_events)
                    
                    next_ledger = credit_ledgers[next_ledger_key]

                    # Record the monthly grant only when the ledger is first created.
                    record_ledger_entry(
                        credit_ledger_entries,
                        next_ledger,
                        next_month_date,
                        "GRANT",
                        "MONTHLY_PLAN",
                        next_ledger["monthly_credits"]
                )

                next_ledger = credit_ledgers[next_ledger_key]

                # Preserve existing carry-forward credits if they have not expired.
                valid_buckets = []
                expired_buckets = []
                ledger_entries = credit_ledger_entries
                
                for bucket in ledger["carry_forward_buckets"]:
                    expiry_date = calculate_carry_forward_expiry(
                    bucket["created_date"]
                )
                    if next_month_date <= expiry_date:
                        valid_buckets.append(bucket.copy())
                    else:
                        expired_buckets.append(bucket.copy())
                    
                # Remove all old carry-forward buckets from the current ledger.
                ledger["carry_forward_buckets"] = []
                    
                # Record expired credits after removing them.
                for bucket in expired_buckets:
                    record_ledger_entry(
                    ledger_entries,
                    ledger,
                    cycle_close_time,
                    "EXPIRE",
                    member_id,
                    bucket["credits"]
                    )

                # Transfer valid old carry-forward credits to the next month.
                for bucket in valid_buckets:
                    next_ledger["carry_forward_buckets"].append(bucket)

                    record_ledger_entry(
                        ledger_entries,
                    next_ledger,
                    cycle_close_time,
                    "CARRY_FORWARD",
                    member_id,
                    bucket["credits"]
                )

                 # Carry forward unused credits from the current month's grant.
                carry_bucket = create_carry_forward_bucket(
                    ledger,
                    billing_month )

                if carry_bucket is not None:
                    next_ledger["carry_forward_buckets"].append(carry_bucket)
                    
                    record_ledger_entry(
                    ledger_entries,
                    next_ledger,
                    cycle_close_time,
                    "CARRY_FORWARD",
                    member_id,
                    carry_bucket["credits"]
                )



            # Assess interest on invoices that are still unpaid.
            # Any new interest is included in this month's invoice.
            for invoice_id in list(unpaid_invoices.keys()):
                record_late_interest(
                    invoice_id,
                    cycle_close_time,
                    billing_month
                )

            # Generate one invoice for every member.
            for member_id, member in members.items():
                ledger_key = (member_id, billing_month)
                ledger = credit_ledgers[ledger_key]

                plan_fee = monthly_plan_fees.get(
                    ledger_key,
                    calculate_membership_allowance(
                        member, plans
                    )["plan_fee"]
                )

                if member["plan"] == "DAY_PASS":
                    plan_fee = 0


                room_overage = ledger["overage_amount"]
                # Calculate desk charges from successful check-in days.
                desk_days_used = len(
                    desk_checkin_days.get(ledger_key, set())
                )

                desk_overage = 0
                day_pass_amount = 0

                if member["plan"] == "FLEX":
                    extra_desk_days = max(
                        0,
                        desk_days_used - 10
                    )

                    desk_overage = extra_desk_days * 700

                elif member["plan"] == "DAY_PASS":
                    day_pass_amount = desk_days_used * 900

                # Late interest from an earlier invoice.
                late_interest_prev = late_interest_by_month.get(
                    ledger_key, 0
                )

                upgrade_amount = upgrade_charges.get(
                    ledger_key, 0
                )

                no_show_amount = no_show_fees.get(
                    ledger_key, 0
                )

                freeze_fee_total = 0
                freeze_waiver_total = 0

                for freeze in freeze_records:
                    if freeze["member_id"] != member_id:
                        continue
                    # DAY_PASS has no monthly plan fee to waive.
                    if member["plan"] == "DAY_PASS":
                        continue

                    waiver_details = calculate_freeze_waiver(
                        freeze["monthly_plan_fee"],
                        freeze["effective_date"],
                        freeze["freeze_days"]
                    )

                    for breakdown in waiver_details["monthly_breakdown"]:
                        if (
                            breakdown["billing_month"]
                            == billing_month.strftime("%Y-%m")
                        ):
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
                    desk_overage=desk_overage,
                    day_pass=day_pass_amount,
                    no_show_fees=no_show_amount,
                    freeze_fees=freeze_fee_total,
                    freeze_waiver=freeze_waiver_total,
                    late_interest_prev=late_interest_prev
                )

                invoices.append(invoice)
                                # Remember this invoice for future payment commands.
                unpaid_invoices[invoice_id] = invoice

                invoice_issue_dates[invoice_id] = cycle_close_time

                invoice_billing_months[invoice_id] = billing_month

                invoice_interest_accrued[invoice_id] = 0

                if invoice["amount_due"] > 0:
                    unpaid_invoice_members.add(member_id)

            print("CLOSE CYCLE:", billing_month, "processed")
        # --------------------------------------------------
        # PAYMENT
        # --------------------------------------------------
        elif action == "PAYMENT":
            invoice_id = arguments[0]

            payment_time = datetime.strptime(
                arguments[1],
                "%Y-%m-%d %H:%M:%S"
            )

            if invoice_id in unpaid_invoices:
                invoice = unpaid_invoices[invoice_id]
                member_id = invoice["member_id"]

                payment_month = date(
                    payment_time.year,
                    payment_time.month,
                    1
                )

                # Calculate any interest due before marking it paid.
                record_late_interest(
                    invoice_id,
                    payment_time,
                    payment_month
                )

                # Mark the invoice as paid.
                del unpaid_invoices[invoice_id]

                # Keep the member blocked only if another invoice
                # for that member is still unpaid.
                member_has_unpaid_invoice = any(
                    unpaid_invoice["member_id"] == member_id
                    for unpaid_invoice in unpaid_invoices.values()
                )

                if not member_has_unpaid_invoice:
                    unpaid_invoice_members.discard(member_id)

                print(
                    "PAYMENT:",
                    invoice_id,
                    "recorded"
                )

            else:
                print(
                    "PAYMENT:",
                    invoice_id,
                    "not found or already paid"
           )
        
        # --------------------------------------------------
        # PRINT BOOKINGS
        # --------------------------------------------------
        elif action == "PRINT_BOOKINGS":
            start_date = datetime.strptime(
                arguments[0], "%Y-%m-%d"
            ).date()

            end_date = datetime.strptime(
                arguments[1], "%Y-%m-%d"
            ).date()

            print_booking_register(
                accepted_bookings,
                start_date,
                end_date
            )

        # --------------------------------------------------
        # PRINT LEDGER
        # --------------------------------------------------
        elif action == "PRINT_LEDGER":
            member_id = arguments[0]

            report_date = datetime.strptime(
                arguments[1], "%Y-%m-%d"
            ).date()

            print_member_credit_ledger(
                credit_ledger_entries,
                member_id,
                report_date
            )

        # --------------------------------------------------
        # PRINT INVOICES
        # --------------------------------------------------
        elif action == "PRINT_INVOICES":
            billing_month = arguments[0]

            print_monthly_invoices(
                invoices,
                billing_month
            )


    return (
    accepted_bookings,
    booking_decisions,
    invoices,
    credit_ledger_entries
)


def main():
    # Load all project data
    plans = load_plans()
    members = load_members()
    rooms = load_rooms()
    bookings = load_bookings()
    events = load_plan_events()

    # Load commands in their original file order
    commands = load_commands()

    print("Project data loaded successfully.")
    print("Members:", len(members))
    print("Bookings:", len(bookings))
    print("Commands:", len(commands))

    # Process all commands
    (
        accepted_bookings,
        booking_decisions,
        invoices,
        credit_ledger_entries
    ) = process_commands(
        commands,
        bookings,
        members,
        rooms,
        plans,
        events
    )

    # Generate all three CSV reports
    write_reports(
        booking_decisions,
        credit_ledger_entries,
        invoices,
        "outputs"
    )

    print("Accepted bookings:", len(accepted_bookings))
    print("Booking decisions:", len(booking_decisions))
    print("Credit ledger entries:", len(credit_ledger_entries))
    print("Invoices generated:", len(invoices))
    print("Output folder: outputs/")


if __name__ == "__main__":
    main()
