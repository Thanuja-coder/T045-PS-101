
import calendar
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP


def calculate_freeze_waiver(monthly_plan_fee, freeze_start, freeze_days):
    if monthly_plan_fee < 0:
        raise ValueError("Monthly plan fee cannot be negative")

    if freeze_days <= 0:
        raise ValueError("Freeze days must be greater than zero")

    monthly_plan_fee = Decimal(str(monthly_plan_fee))

    freeze_end = freeze_start + timedelta(days=freeze_days - 1)

    month_days = {}
    current_date = freeze_start

    # Count how many freeze days fall in each calendar month.
    while current_date <= freeze_end:
        month_key = (current_date.year, current_date.month)

        if month_key not in month_days:
            month_days[month_key] = 0

        month_days[month_key] += 1
        current_date += timedelta(days=1)

    monthly_breakdown = []
    total_waiver = Decimal("0")

    # Calculate and round the waiver separately for each month.
    for (year, month), days_frozen in month_days.items():
        days_in_month = calendar.monthrange(year, month)[1]

        waiver = (
            monthly_plan_fee * days_frozen / Decimal(days_in_month)
        )

        waiver = waiver.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )

        monthly_breakdown.append({
            "billing_month": f"{year}-{month:02d}",
            "freeze_days": days_frozen,
            "days_in_month": days_in_month,
            "waiver": waiver
        })

        total_waiver += waiver

    return {
        "monthly_breakdown": monthly_breakdown,
        "total_waiver": total_waiver
    }


def calculate_freeze_adjustment(freeze_waiver, plan_fee_paid):
    freeze_waiver = Decimal(str(freeze_waiver))

    if freeze_waiver < 0:
        raise ValueError("Freeze waiver cannot be negative")

    freeze_fee = Decimal("500")

    if plan_fee_paid:
        account_credit = freeze_waiver
        invoice_waiver = Decimal("0")
    else:
        account_credit = Decimal("0")
        invoice_waiver = freeze_waiver

    return {
        "freeze_fee": freeze_fee,
        "account_credit": account_credit,
        "invoice_waiver": invoice_waiver
    }


def calculate_gst(subtotal):
    if subtotal < 0:
        raise ValueError("Subtotal cannot be negative")

    gst = subtotal * Decimal("0.18")
    gst = gst.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    return gst


def calculate_late_interest(invoice_total, days_beyond_grace_period):
    if invoice_total < 0:
        raise ValueError("Invoice total cannot be negative")

    if days_beyond_grace_period < 0:
        raise ValueError("Late days cannot be negative")

    interest = (
        invoice_total
        * Decimal("0.015")
        * Decimal(days_beyond_grace_period)
        / Decimal("30")
    )

    interest = interest.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    return interest

def calculate_invoice_subtotal(
    plan_fee,
    upgrade_charges=Decimal("0"),
    room_overage=Decimal("0"),
    desk_overage=Decimal("0"),
    day_pass=Decimal("0"),
    no_show_fees=Decimal("0"),
    freeze_fees=Decimal("0"),
    freeze_waiver=Decimal("0")
):
    charges = [
        plan_fee,
        upgrade_charges,
        room_overage,
        desk_overage,
        day_pass,
        no_show_fees,
        freeze_fees,
        freeze_waiver
    ]

    for charge in charges:
        if charge < 0:
            raise ValueError("Invoice amounts cannot be negative")

    subtotal = (
        plan_fee
        + upgrade_charges
        + room_overage
        + desk_overage
        + day_pass
        + no_show_fees
        + freeze_fees
        - freeze_waiver
    )

    if subtotal < 0:
        raise ValueError("Invoice subtotal cannot be negative")

    return subtotal

def calculate_invoice_total(subtotal):
    if subtotal < 0:
        raise ValueError("Subtotal cannot be negative")

    total = subtotal * Decimal("1.18")

    total = total.quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP
    )

    return total


def build_invoice_record(
    invoice_id,
    member_id,
    plan_fee,
    upgrade_charges=Decimal("0"),
    room_overage=Decimal("0"),
    desk_overage=Decimal("0"),
    day_pass=Decimal("0"),
    no_show_fees=Decimal("0"),
    freeze_fees=Decimal("0"),
    freeze_waiver=Decimal("0"),
    late_interest_prev=Decimal("0")
):
    subtotal = calculate_invoice_subtotal(
        plan_fee,
        upgrade_charges,
        room_overage,
        desk_overage,
        day_pass,
        no_show_fees,
        freeze_fees,
        freeze_waiver
    )

    gst = calculate_gst(subtotal)
    total = subtotal + gst

    amount_due = total + late_interest_prev

    invoice = {
        "invoice_id": invoice_id,
        "member_id": member_id,
        "plan_fee": plan_fee,
        "upgrade_charges": upgrade_charges,
        "room_overage": room_overage,
        "desk_overage": desk_overage,
        "day_pass": day_pass,
        "no_show_fees": no_show_fees,
        "freeze_fees": freeze_fees,
        "freeze_waiver": freeze_waiver,
        "subtotal": subtotal,
        "gst": gst,
        "total": total,
        "late_interest_prev": late_interest_prev,
        "amount_due": amount_due
    }

    return invoice


import csv

def write_invoice_records(invoices, file_path):
    columns = [
        "invoice_id",
        "member_id",
        "plan_fee",
        "upgrade_charges",
        "room_overage",
        "desk_overage",
        "day_pass",
        "no_show_fees",
        "freeze_fees",
        "freeze_waiver",
        "subtotal",
        "gst",
        "total",
        "late_interest_prev",
        "amount_due"
    ]

    with open(file_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)

        writer.writeheader()

        for invoice in invoices:
            writer.writerow(invoice)
