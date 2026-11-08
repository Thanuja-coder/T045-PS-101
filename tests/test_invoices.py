
import unittest
from datetime import date
from decimal import Decimal

from src.invoice import calculate_freeze_waiver, calculate_freeze_adjustment, calculate_gst, calculate_late_interest
from src.invoice import calculate_invoice_subtotal
from src.invoice import calculate_invoice_total
from src.invoice import build_invoice_record

import csv
import tempfile
import os
from src.invoice import write_invoice_records

class TestFreezeWaiver(unittest.TestCase):

    def test_freeze_within_one_month(self):
        result = calculate_freeze_waiver(
            8000, date(2026, 11, 1), 15
        )

        self.assertEqual(
            result["total_waiver"], Decimal("4000")
        )
        self.assertEqual(
            result["monthly_breakdown"][0]["freeze_days"], 15
        )

    def test_freeze_across_two_months(self):
        result = calculate_freeze_waiver(
            8000, date(2026, 11, 25), 15
        )

        self.assertEqual(len(result["monthly_breakdown"]), 2)

        self.assertEqual(
            result["monthly_breakdown"][0]["freeze_days"], 6
        )
        self.assertEqual(
            result["monthly_breakdown"][1]["freeze_days"], 9
        )

        self.assertEqual(
            result["monthly_breakdown"][0]["waiver"],
            Decimal("1600")
        )
        self.assertEqual(
            result["monthly_breakdown"][1]["waiver"],
            Decimal("2323")
        )

    def test_freeze_in_february_leap_year(self):
        result = calculate_freeze_waiver(
            8000, date(2028, 2, 1), 15
        )

        self.assertEqual(
            result["monthly_breakdown"][0]["days_in_month"], 29
        )
        self.assertEqual(
            result["total_waiver"],
            Decimal("4138")
        )

    def test_zero_freeze_days_rejected(self):
        with self.assertRaises(ValueError):
            calculate_freeze_waiver(
                8000, date(2026, 11, 1), 0
            )

    def test_negative_monthly_fee_rejected(self):
        with self.assertRaises(ValueError):
            calculate_freeze_waiver(
                -8000, date(2026, 11, 1), 15
            )

    
    def test_freeze_adjustment_when_plan_fee_not_paid(self):
        result = calculate_freeze_adjustment(
            Decimal("4000"), False
        )

        self.assertEqual(result["freeze_fee"], Decimal("500"))
        self.assertEqual(result["account_credit"], Decimal("0"))
        self.assertEqual(result["invoice_waiver"], Decimal("4000"))

    def test_freeze_adjustment_when_plan_fee_already_paid(self):
        result = calculate_freeze_adjustment(
            Decimal("4000"), True
        )

        self.assertEqual(result["freeze_fee"], Decimal("500"))
        self.assertEqual(result["account_credit"], Decimal("4000"))
        self.assertEqual(result["invoice_waiver"], Decimal("0"))

    def test_zero_freeze_waiver(self):
        result = calculate_freeze_adjustment(
            Decimal("0"), True
        )

        self.assertEqual(result["account_credit"], Decimal("0"))
        self.assertEqual(result["freeze_fee"], Decimal("500"))

    def test_negative_freeze_waiver_rejected(self):
        with self.assertRaises(ValueError):
            calculate_freeze_adjustment(
                Decimal("-100"), True
            )
    def test_readme_ec05_freeze_example(self):
        result = calculate_freeze_waiver(
            8000, date(2026, 1, 25), 15
        )

        january = result["monthly_breakdown"][0]
        february = result["monthly_breakdown"][1]

        self.assertEqual(january["billing_month"], "2026-01")
        self.assertEqual(january["freeze_days"], 7)
        self.assertEqual(january["waiver"], Decimal("1806"))

        self.assertEqual(february["billing_month"], "2026-02")
        self.assertEqual(february["freeze_days"], 8)
        self.assertEqual(february["waiver"], Decimal("2286"))

        self.assertEqual(
            result["total_waiver"],
            Decimal("4092")
        )

    from decimal import Decimal
    from src.invoice import calculate_gst

    def test_gst_for_normal_subtotal(self):
        self.assertEqual(
            calculate_gst(Decimal("8000")),
            Decimal("1440")
        )

    def test_gst_for_subtotal_with_paise(self):
        self.assertEqual(
            calculate_gst(Decimal("8226")),
            Decimal("1481")
        )

    def test_gst_for_zero_subtotal(self):
        self.assertEqual(
            calculate_gst(Decimal("0")),
            Decimal("0")
        )

    def test_negative_subtotal_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_gst(Decimal("-100"))


    from src.invoice import calculate_late_interest


class TestLateInterest(unittest.TestCase):

    def test_late_interest_for_12_days(self):
        self.assertEqual(
            calculate_late_interest(Decimal("9440"), 12),
            Decimal("57")
        )

    def test_no_interest_with_zero_late_days(self):
        self.assertEqual(
            calculate_late_interest(Decimal("9440"), 0),
            Decimal("0")
        )

    def test_negative_late_days(self):
        with self.assertRaises(ValueError):
            calculate_late_interest(Decimal("9440"), -1)

    def test_negative_invoice_total(self):
        with self.assertRaises(ValueError):
            calculate_late_interest(Decimal("-9440"), 12)

class TestInvoiceSubtotal(unittest.TestCase):

    def test_invoice_with_all_charges(self):
        subtotal = calculate_invoice_subtotal(
            plan_fee=Decimal("8000"),
            upgrade_charges=Decimal("226"),
            room_overage=Decimal("300"),
            desk_overage=Decimal("700"),
            day_pass=Decimal("900"),
            no_show_fees=Decimal("200"),
            freeze_fees=Decimal("500"),
            freeze_waiver=Decimal("1806")
        )

        self.assertEqual(subtotal, Decimal("9020"))

    def test_invoice_without_extra_charges(self):
        subtotal = calculate_invoice_subtotal(
            plan_fee=Decimal("8000")
        )

        self.assertEqual(subtotal, Decimal("8000"))

    def test_freeze_waiver_is_deducted(self):
        subtotal = calculate_invoice_subtotal(
            plan_fee=Decimal("8000"),
            freeze_waiver=Decimal("1806")
        )

        self.assertEqual(subtotal, Decimal("6194"))

    def test_negative_charge_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_invoice_subtotal(
                plan_fee=Decimal("-8000")
            )

class TestInvoiceTotal(unittest.TestCase):

    def test_invoice_total_with_gst(self):
        self.assertEqual(
            calculate_invoice_total(Decimal("8450")),
            Decimal("9971")
        )

    def test_invoice_total_for_8000(self):
        self.assertEqual(
            calculate_invoice_total(Decimal("8000")),
            Decimal("9440")
        )

    def test_zero_subtotal(self):
        self.assertEqual(
            calculate_invoice_total(Decimal("0")),
            Decimal("0")
        )

    def test_negative_subtotal(self):
        with self.assertRaises(ValueError):
            calculate_invoice_total(Decimal("-100"))


class TestBuildInvoiceRecord(unittest.TestCase):

    def test_basic_invoice_record(self):
        invoice = build_invoice_record(
            invoice_id="INV-M01-202601",
            member_id="M01",
            plan_fee=Decimal("8000")
        )

        self.assertEqual(invoice["subtotal"], Decimal("8000"))
        self.assertEqual(invoice["gst"], Decimal("1440"))
        self.assertEqual(invoice["total"], Decimal("9440"))
        self.assertEqual(invoice["amount_due"], Decimal("9440"))

    def test_invoice_with_all_charges(self):
        invoice = build_invoice_record(
            invoice_id="INV-M02-202601",
            member_id="M02",
            plan_fee=Decimal("8000"),
            upgrade_charges=Decimal("226"),
            room_overage=Decimal("300"),
            desk_overage=Decimal("100"),
            day_pass=Decimal("900"),
            no_show_fees=Decimal("200"),
            freeze_fees=Decimal("500"),
            freeze_waiver=Decimal("1806"),
            late_interest_prev=Decimal("57")
        )

        self.assertEqual(invoice["subtotal"], Decimal("8420"))
        self.assertEqual(invoice["gst"], Decimal("1516"))
        self.assertEqual(invoice["total"], Decimal("9936"))
        self.assertEqual(invoice["amount_due"], Decimal("9993"))

    def test_invoice_has_required_columns_in_order(self):
        invoice = build_invoice_record(
            invoice_id="INV-M03-202601",
            member_id="M03",
            plan_fee=Decimal("8000")
        )

        expected_columns = [
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

        self.assertEqual(list(invoice.keys()), expected_columns)


class TestWriteInvoiceRecords(unittest.TestCase):

    def test_write_invoice_records(self):
        invoices = [
            build_invoice_record(
                invoice_id="INV-M01-202601",
                member_id="M01",
                plan_fee=Decimal("8000")
            ),
            build_invoice_record(
                invoice_id="INV-M02-202601",
                member_id="M02",
                plan_fee=Decimal("15000")
            )
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "invoices.csv")

            write_invoice_records(invoices, file_path)

            with open(file_path, "r", newline="") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["invoice_id"], "INV-M01-202601")
            self.assertEqual(rows[1]["invoice_id"], "INV-M02-202601")

    def test_invoice_csv_column_order(self):
        invoice = build_invoice_record(
            invoice_id="INV-M01-202601",
            member_id="M01",
            plan_fee=Decimal("8000")
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "invoices.csv")

            write_invoice_records([invoice], file_path)

            with open(file_path, "r", newline="") as file:
                reader = csv.reader(file)
                header = next(reader)

            expected_columns = list(invoice.keys())
            self.assertEqual(header, expected_columns)

    def test_write_empty_invoice_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "invoices.csv")

            write_invoice_records([], file_path)

            self.assertTrue(os.path.exists(file_path))
if __name__ == "__main__":
    unittest.main()
