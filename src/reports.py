
import csv
from pathlib import Path


BOOKING_DECISION_COLUMNS = [
    "ts",
    "booking_id",
    "member_id",
    "action",
    "result",
    "rule_id",
    "credits",
    "from_carry",
    "from_current",
    "overage",
    "refund"
]

CREDIT_LEDGER_COLUMNS = [
    "member_id",
    "ts",
    "entry",
    "reference",
    "credits",
    "carry_balance",
    "current_balance",
    "overage_credits"
]

INVOICE_COLUMNS = [
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


def write_csv(file_path, columns, records):
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore"
        )

        writer.writeheader()
        writer.writerows(records)



def write_reports(
    booking_decisions,
    credit_ledger_entries,
    invoices,
    output_folder="outputs"
):
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate booking decisions report
    write_csv(
        output_path / "booking_decisions.csv",
        BOOKING_DECISION_COLUMNS,
        booking_decisions
    )

    # Generate credit ledger report
    write_csv(
        output_path / "credit_ledger.csv",
        CREDIT_LEDGER_COLUMNS,
        credit_ledger_entries
    )

    # Generate monthly invoices report
    write_csv(
        output_path / "invoices.csv",
        INVOICE_COLUMNS,
        invoices
    )

    print("All three output CSV files generated successfully.")


def get_booking_register(bookings, member_id, report_date):
    report_date = str(report_date)

    records = []

    for booking in bookings:
        booking_date = booking["start_ts"].date()

        if (
            booking["member_id"] == member_id
            and str(booking_date) == report_date
        ):
            records.append(booking)

    return records


def get_credit_ledger(ledger_entries, member_id, report_date):
    report_date = str(report_date)

    records = []

    for entry in ledger_entries:
        entry_date = str(entry["ts"])[:10]

        if (
            entry["member_id"] == member_id
            and entry_date == report_date
        ):
            records.append(entry)

    return records



def print_booking_register(bookings, start_date, end_date):
    print("\n========== BOOKING REGISTER ==========")
    print("Period:", start_date, "to", end_date)

    found = False

    for booking in bookings:
        booking_date = booking["start_ts"].date()

        if start_date <= booking_date <= end_date:
            found = True

            print(
                booking["booking_id"],
                "| Member:", booking["member_id"],
                "| Resource:", booking["resource"],
                "| Start:", booking["start_ts"],
                "| End:", booking["end_ts"]
            )

    if not found:
        print("No bookings found for this period.")

    print("======================================")


def print_member_credit_ledger(ledger_entries, member_id, report_date):
    print("\n========== CREDIT LEDGER ==========")
    print("Member:", member_id)
    print("Up to:", report_date)

    found = False

    for entry in ledger_entries:
        entry_date = entry["ts"]

        if isinstance(entry_date, str):
            entry_date = entry_date[:10]
        else:
            entry_date = entry_date.date() if hasattr(
                entry_date, "date"
            ) else entry_date

        if (
            entry["member_id"] == member_id
            and entry_date <= report_date
        ):
            found = True

            print(
                entry["ts"],
                "|", entry["entry"],
                "| Reference:", entry["reference"],
                "| Credits:", entry["credits"],
                "| Carry:", entry["carry_balance"],
                "| Current:", entry["current_balance"],
                "| Overage:", entry["overage_credits"]
            )

    if not found:
        print("No ledger entries found.")

    print("===================================")


def print_monthly_invoices(invoices, billing_month):
    print("\n========== MONTHLY INVOICES ==========")
    print("Billing month:", billing_month)

    found = False

    for invoice in invoices:
        invoice_month = invoice["invoice_id"][-6:]

        if invoice_month == billing_month.replace("-", ""):
            found = True

            print(
                invoice["invoice_id"],
                "| Member:", invoice["member_id"],
                "| Subtotal:", invoice["subtotal"],
                "| GST:", invoice["gst"],
                "| Total:", invoice["total"],
                "| Amount Due:", invoice["amount_due"]
            )

    if not found:
        print("No invoices found for this month.")

    print("======================================")
