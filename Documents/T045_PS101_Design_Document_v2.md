# T045 -- PS-101

## Co-working Membership, Desk/Room Booking and Credit Ledger Engine

### Design Document -- Version 2.0 (Implementation-Aligned)

**Team ID:** T045\
**Team Members:** Thanuja Madhu Chandre Gowda, Thoshin S\
**Section:** CSDS B\
**Language:** Python 3.10+\
**Application Type:** Command-file-driven backend engine\
**Repository:** `Thanuja-coder/T045-PS-101`\
**Status:** Implemented; aligned with the current Python implementation\
**Last updated:** 14 November 2026

------------------------------------------------------------------------

## Document purpose

This document replaces the initial proposed design with a description of
the current implementation. It distinguishes implemented behaviour from
design intentions and avoids describing classes or interfaces that the
project does not currently use.

The application is a Python command-file-driven backend. It reads
member, resource, booking and command data, processes operations through
Python modules and writes CSV outputs. It does not include a graphical
user interface or payment gateway.

## 1. Project Overview

The system manages co-working memberships, desk and meeting-room
bookings, room-credit balances, membership changes, freezes,
cancellations, no-shows, invoices and reports.

The application loads the supplied data, processes commands from
`data/commands.txt`, applies the relevant business rules and generates
output files.

### 1.1 Project objectives

-   Load member, resource and booking data from input files.
-   Process commands from a text file.
-   Validate desk and meeting-room booking requests.
-   Calculate room credits using room capacity, half-hour slots and
    time-based multipliers.
-   Maintain monthly credit balances, carry-forward credits, FIFO
    consumption and overage.
-   Process cancellations, check-ins and no-shows.
-   Process membership upgrades, downgrades and freezes.
-   Generate invoices with applicable charges, waivers, GST and late
    interest.
-   Produce CSV outputs for booking decisions, credit ledger, booking
    register and invoices.

### 1.2 Current execution

Run the application from the repository root:

``` bash
python -m src.main
```

The application loads the input data and processes the commands in the
command file. The current sample dataset contains 20 members, 120
bookings and 276 commands. These are sample-data counts, not fixed
limits in the implementation.

## 2. Glossary

  -----------------------------------------------------------------------
  Term                                Meaning
  ----------------------------------- -----------------------------------
  Member                              A person or organization
                                      represented by a member record.

  Member ID                           Identifier used to associate
                                      memberships, bookings, ledgers and
                                      invoices.

  DAY_PASS                            Daily plan costing ₹900/day, with
                                      no monthly room-credit allowance.

  FLEX                                Monthly plan costing ₹8,000, with
                                      10 desk-days and 20 room credits.

  DEDICATED                           Monthly plan costing ₹15,000, with
                                      unlimited desk usage and 40 room
                                      credits.

  TEAM                                Plan costing ₹12,000 per seat per
                                      month, minimum 3 seats, with 60
                                      room credits per seat pooled for
                                      the member/team.

  Hot desk                            Shared desk resource, subject to
                                      the hot-desk capacity of 40.

  Dedicated desk                      Fixed desk associated with a
                                      DEDICATED membership.

  Meeting room                        A room with a configured capacity
                                      and credit rate.

  Booking                             A reservation for a resource over a
                                      date/time range.

  Credit                              Unit used to account for
                                      meeting-room usage.

  Carry-forward                       Eligible unused room credits moved
                                      into the following billing cycle,
                                      subject to the cap and expiry rule.

  FIFO                                First In, First Out; eligible
                                      carried-forward credits are used
                                      before current-cycle credits.

  Overage                             Charge for usage beyond the
                                      available eligible allowance.

  Peak period                         Weekday time from 10:00 to 13:00,
                                      charged at 1.5 times the base slot
                                      credits.

  Weekend multiplier                  Weekend slots are charged at 0.5
                                      times the base slot credits.

  Freeze                              A temporary membership pause.
                                      Booking validation blocks bookings
                                      during a freeze.

  No-show                             A room booking for which the member
                                      has not checked in within the
                                      15-minute check-in window.

  Invoice                             Monthly record of plan fees, usage
                                      charges, fees, waiver, GST and
                                      amount due.

  Billing cycle                       The month identified by the
                                      billing-month value used by the
                                      application.
  -----------------------------------------------------------------------

## 3. Implemented System Architecture

### 3.1 High-level flow

``` mermaid
flowchart TD
    A["Input files"] --> B["Data loader"]
    C["commands.txt"] --> D["Command parser"]
    B --> E["Application controller: main.py"]
    D --> E
    E --> F["Membership and plan manager"]
    E --> G["Booking validation and booking processing"]
    E --> H["Credit ledger"]
    E --> I["Cancellation and no-show processing"]
    E --> J["Invoice processing"]
    E --> K["Reports and output writing"]
    F --> E
    G --> H
    I --> H
    J --> K
    E --> L["CSV output files"]
```

### 3.2 Current module responsibilities

  -----------------------------------------------------------------------
  Module                              Current responsibility
  ----------------------------------- -----------------------------------
  `src/main.py`                       Main application controller. Loads
                                      data, processes commands,
                                      coordinates booking, membership,
                                      credit, cancellation and invoice
                                      operations, and writes outputs.

  `src/data_loader.py`                Loads the input data files into the
                                      structures used by the application.

  `src/command_parser.py`             Reads command-file lines, skips
                                      blank lines and comments, and
                                      splits commands using the `|`
                                      delimiter.

  `src/booking.py`                    Validates room bookings, including
                                      duration, overlap, advance window,
                                      FLEX future-booking limit, freeze
                                      restrictions and hot-desk capacity
                                      checks.

  `src/membership.py`                 Validates membership data,
                                      registers members, calculates plan
                                      allowances and computes upgrade
                                      details.

  `src/plan_manager.py`               Handles plan upgrades, scheduled
                                      downgrades and membership freeze
                                      operations.

  `src/credit_ledger.py`              Calculates room-credit
                                      requirements, carry-forward limits,
                                      credit usage, FIFO consumption,
                                      overage and credit restoration.

  `src/cancellation.py`               Calculates cancellation refunds,
                                      checks no-show eligibility and
                                      calculates no-show fees.

  `src/invoice.py`                    Calculates freeze waivers and
                                      adjustments, GST, invoice subtotals
                                      and totals, late interest, invoice
                                      records and invoice CSV output.

  `src/reports.py`                    Report/output functionality as
                                      implemented in the current project.

  `tests/`                            Automated unit and
                                      integration-oriented tests for the
                                      implemented rules.
  -----------------------------------------------------------------------

### 3.3 Current project structure

``` text
T045-PS-101/
│
├── data/
│   ├── members.csv
│   ├── resources.csv
│   ├── bookings.csv
│   └── commands.txt
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── data_loader.py
│   ├── command_parser.py
│   ├── booking.py
│   ├── membership.py
│   ├── credit_ledger.py
│   ├── plan_manager.py
│   ├── cancellation.py
│   ├── invoice.py
│   └── reports.py
│
├── tests/
│   ├── test_booking.py
│   ├── test_cancellation.py
│   ├── test_credits.py
│   ├── test_invoices.py
│   ├── test_membership.py
│   ├── test_plan_manager.py
│   └── test_edge_cases.py
│
├── outputs/
│   ├── booking_decisions.csv
│   ├── credit_ledger.csv
│   ├── bookings_register.csv
│   └── invoices.csv
│
├── docs/
│   ├── design_document.md
│   └── decision_log.md
│
├── README.md
└── requirements.txt
```

The exact files present in the repository should be kept in sync with
this tree if the project structure changes.

## 4. Data and Processing Design

### 4.1 Data representation

The implementation uses Python data structures such as dictionaries and
lists to represent members, resources, bookings, ledger entries and
invoices. The design document therefore describes the data fields and
relationships without claiming that dedicated Python classes are used.

### 4.2 Main records

  -----------------------------------------------------------------------
  Record                              Main information used
  ----------------------------------- -----------------------------------
  Member                              Member ID, plan, plan
                                      start/effective dates, membership
                                      status and TEAM seat count where
                                      applicable.

  Resource                            Resource ID/type, room capacity and
                                      room credit rate, or desk resource
                                      details.

  Booking                             Booking ID, member ID, resource ID,
                                      start/end timestamps, status and
                                      credit/refund information.

  Credit ledger entry                 Member ID, timestamp, entry type,
                                      reference, credits and resulting
                                      balances.

  Invoice                             Invoice ID, member ID, plan fee,
                                      charges, waiver, subtotal, GST,
                                      total, prior late interest and
                                      amount due.

  Booking decision                    Timestamp, booking ID, member ID,
                                      action/result, rule ID and
                                      credit/refund amounts.
  -----------------------------------------------------------------------

### 4.3 TEAM pooled-credit model

TEAM room credits are calculated as 60 credits per seat. For a
three-seat TEAM membership, the monthly allowance is 180 credits.

The application keeps the monthly credit ledger associated with the
member and billing month. Bookings for that member in the same month use
the shared monthly ledger. The pool is therefore shared at member/team
level rather than maintained as separate per-seat balances.

## 5. Membership Plans

  ------------------------------------------------------------------------------
  Plan                          Fee Desk            Room credits  Advance window
                                    benefit                      
  ----------- --------------------- ----------- ---------------- ---------------
  DAY_PASS                 ₹900/day Daily                      0   As configured
                                    access                                by the
                                                                      applicable
                                                                   booking rules

  FLEX                 ₹8,000/month 10                  20/month          7 days
                                    desk-days                    

  DEDICATED           ₹15,000/month Unlimited           40/month         30 days
                                    desk; fixed                  
                                    desk                         

  TEAM          ₹12,000/seat/month; Unlimited     60/seat/month,         60 days
                    minimum 3 seats desk                  pooled 
  ------------------------------------------------------------------------------

TEAM allowance is calculated using the number of seats. For three seats,
the plan has 180 pooled room credits and a monthly plan fee of ₹36,000.

## 6. Business Rules and Implemented Behaviour

### 6.1 Membership and allowances

-   Supported plans are DAY_PASS, FLEX, DEDICATED and TEAM.
-   Plan fees and allowances follow the plan register above.
-   TEAM requires at least three seats.
-   TEAM room credits and plan fees scale by seat count.
-   Upgrade charges are prorated using the actual number of days in the
    effective month.
-   The effective date is included in the remaining-day calculation.
-   Downgrades are scheduled for the next calendar billing cycle.

### 6.2 Room booking duration and room rates

-   Room bookings must be at least 30 minutes.
-   Room duration must use 30-minute increments.
-   A room booking cannot exceed 4 hours.
-   The configured room rates are:

  Room capacity     Base credits per 30 minutes
  --------------- -----------------------------
  4 seats                                     1
  8 seats                                     2
  20 seats                                    5

### 6.3 Peak and weekend pricing

-   Weekday slots in the 10:00--13:00 peak period use a 1.5 multiplier.
-   Weekend slots use a 0.5 multiplier.
-   Other weekday slots use the normal base credit rate.
-   The booking is split into half-hour slots and the slot categories
    are counted.
-   In the current implementation, the peak portion is rounded up with
    `math.ceil` and added to the off-peak and weekend portions.

**Implementation detail:** `calculate_room_credits()` in
`src/credit_ledger.py` performs this calculation. For the 4-seat room
example from 09:30 to 10:30 on a weekday, the off-peak slot costs 1
credit and the peak slot costs 1.5, rounded up to 2; the total is 3
credits.

### 6.4 Carry-forward and credit usage

-   The carry-forward cap is 25% of the monthly room-credit grant.
-   The cap is rounded down using `math.floor`.
-   For a monthly grant of 50 credits, 25% is 12.5 and the maximum
    carry-forward is 12 credits.
-   Carry-forward credits are consumed before current-cycle credits.
-   Carried-forward credits are tracked separately so their balance and
    expiry can be maintained.
-   Eligible unused credits are subject to the next-cycle expiry rule.
-   If eligible credits are insufficient and the member is allowed to
    use overage, the excess is recorded as overage.

Relevant functions in `src/credit_ledger.py` include: -
`calculate_carry_forward_limit()` - `process_room_credit_usage()` -
`restore_booking_credits()` - `calculate_room_credits()`

### 6.5 Overage

-   Room-credit overage is charged at ₹150 per credit.
-   FLEX desk-day overage is charged at ₹700 per day.
-   Overage is recorded for invoicing.
-   The booking validation flow checks the unpaid-invoice restriction
    before the credit and overage decision, according to the required
    precedence.

### 6.6 Booking validation

The booking validator applies the required checks in this order:

1.  Resource/time overlap.
2.  Advance booking window, including the FLEX limit on future room
    bookings.
3.  Freeze restriction.
4.  Unpaid-invoice restriction.
5.  Credit availability, with carry-forward credits consumed first.
6.  Overage eligibility and calculation.

The first failing check determines the booking rejection result and
associated rule information. The relevant validation functions are in
`src/booking.py`, with application-level coordination in `src/main.py`.

### 6.7 Cancellation refunds

The current refund ladder is:

  Time before booking start                       Refund
  ---------------------------------- -------------------
  More than 24 hours                                100%
  2 hours through exactly 24 hours     50%, rounded down
  Less than 2 hours                                   0%

A cancellation of a booking that has already been checked in is rejected
by the application flow. When a positive refund is applicable, the
application restores the eligible credits and records the refund in the
ledger. The restoration logic is implemented in
`restore_booking_credits()` in `src/credit_ledger.py`.

**Boundary decision:** Exactly 24 hours is treated as the 50% refund
case. This is verified by the cancellation test.

### 6.8 Check-in and no-show

-   A member must check in within 15 minutes after the booking start.
-   Check-in exactly at the 15-minute deadline is valid.
-   A booking without a valid check-in after the deadline can be treated
    as a no-show during cycle-close processing.
-   No-show counting is maintained by member and billing month.
-   The first room no-show in a billing month has no fee.
-   The second and subsequent room no-shows in that billing month incur
    a ₹200 fee under the current implementation.
-   Multiple no-shows on the same day are counted as separate bookings.
-   Processed no-shows are tracked to prevent the same booking from
    being counted repeatedly during later processing.
-   Desk bookings do not incur the room no-show fee under the current
    rule.

Relevant functions are `check_booking_no_show()` and
`calculate_no_show_fee()` in `src/cancellation.py`. The cycle-close
counting and fee recording are coordinated in `src/main.py`.

### 6.9 Membership freeze

-   Minimum freeze duration: 15 days.
-   Maximum freeze duration: 60 days per calendar year.
-   Freeze fee: ₹500.
-   Bookings are blocked during the freeze period.
-   The freeze cannot start when the applicable future-booking
    restriction is violated.
-   Plan-fee waiver is calculated proportionally by the number of freeze
    days in each calendar month.
-   A freeze spanning a month boundary is split into monthly portions.
-   The current freeze adjustment policy applies a ₹500 fee and treats
    the waiver according to whether the plan fee has already been paid:
    -   If the plan fee is unpaid, the waiver reduces the invoice.
    -   If the plan fee is already paid, the waiver is recorded as an
        account credit for a future invoice rather than as a cash
        refund.
-   Credits do not accrue for the freeze period according to the freeze
    allowance handling.

Relevant functions are in `src/plan_manager.py`, `src/membership.py` and
`src/invoice.py`, including `calculate_freeze_waiver()` and
`calculate_freeze_adjustment()`.

### 6.10 Upgrade and downgrade

-   An upgrade is effective on the requested effective date.
-   The additional plan fee is prorated using the remaining days in the
    month divided by the actual number of days in that month.
-   The effective date is included in the remaining-day count.
-   The amount is rounded to the nearest rupee using the implemented
    Decimal rounding.
-   Additional room credits are prorated and rounded down.
-   `calendar.monthrange()` is used so 28-, 29-, 30- and 31-day months
    are handled.
-   A downgrade becomes effective in the next calendar billing month.

Relevant functions are in `src/membership.py` and `src/plan_manager.py`,
including `calculate_upgrade_details()`.

### 6.11 Invoices, GST and late interest

The invoice subtotal includes applicable plan fees, upgrade charges,
room overage, desk overage, day-pass charges, no-show fees and freeze
fees, less the freeze waiver.

``` text
subtotal = plan_fee
         + upgrade_charges
         + room_overage
         + desk_overage
         + day_pass
         + no_show_fees
         + freeze_fees
         - freeze_waiver
```

-   GST is 18% of the subtotal.
-   Invoice total is subtotal plus GST, rounded according to the invoice
    calculation.
-   Late interest is 1.5% per month simple interest on the invoice
    total, using the implemented late-day calculation.
-   The first seven calendar days after issue are a grace period.
-   Payment exactly seven days after issue results in zero late days and
    no late interest.
-   Late interest is calculated in the payment/cycle processing flow in
    `src/main.py`; invoice arithmetic functions are in `src/invoice.py`.

Important invoice functions include: - `calculate_invoice_subtotal()` -
`calculate_gst()` - `calculate_invoice_total()` -
`calculate_late_interest()` - `build_invoice_record()` -
`write_invoice_records()`

## 7. Edge-Case Verification Register

The following table maps the eight required edge cases to the
implementation. "Handled" means the current logic supports the scenario;
it does not mean every scenario has a separate end-to-end integration
test.

  --------------------------------------------------------------------------------------------
  ID                Required scenario Implementation location              Current
                                                                           verification status
  ----------------- ----------------- ------------------------------------ -------------------
  EC-01             Weekday booking   `calculate_room_credits()` in        Logic and
                    from 09:30 to     `src/credit_ledger.py`               slot-calculation
                    10:30 crosses                                          test inspected;
                    into peak time                                         expected total is 3
                                                                           credits for the
                                                                           4-seat example.

  EC-02             Upgrade on the    `calculate_upgrade_details()` in     Uses actual month
                    last day of a     `src/membership.py`                  length and includes
                    31-day month                                           the effective date;
                                                                           31-day boundary
                                                                           test was added and
                                                                           reported passing.

  EC-03             Carry-forward     `calculate_carry_forward_limit()` in `math.floor()`
                    value is 12.5     `src/credit_ledger.py`               returns 12; a
                    credits                                                dedicated
                                                                           exact-12.5 test was
                                                                           suggested but was
                                                                           not confirmed as
                                                                           added.

  EC-04             Cancellation      `calculate_cancellation_refund()` in Existing boundary
                    exactly 24 hours  `src/cancellation.py`                test verifies 50%
                    before booking                                         refund.

  EC-05             A 15-day freeze   `calculate_freeze_waiver()` in       Tests cover a
                    spans two billing `src/invoice.py`                     freeze split across
                    months                                                 November/December
                                                                           and
                                                                           January/February.

  EC-06             TEAM with 3 seats `calculate_membership_allowance()`   TEAM allowance
                    uses the pooled   and monthly ledger handling in       tests and a
                    180 credits       `src/main.py`                        180-credit usage
                                                                           test were reported
                                                                           passing.

  EC-07             Second room       `check_booking_no_show()`,           Code counts
                    no-show occurs on `calculate_no_show_fee()` and        bookings by
                    the same day as   cycle-close counting in              member/month, not
                    the first         `src/main.py`                        by day; exact
                                                                           same-day end-to-end
                                                                           test was not
                                                                           confirmed.

  EC-08             Invoice paid      `record_late_interest()` in          Main logic
                    exactly 7 days    `src/main.py` and                    subtracts the 7-day
                    after issue       `calculate_late_interest()` in       grace period;
                                      `src/invoice.py`                     existing
                                                                           zero-late-days test
                                                                           verifies ₹0
                                                                           interest.
  --------------------------------------------------------------------------------------------

## 8. Output Files

The application generates CSV outputs in the `outputs/` directory.

### 8.1 `booking_decisions.csv`

Contains the result of booking-related commands and relevant
credit/refund details.

Expected columns:

``` text
ts, booking_id, member_id, action, result, rule_id, credits,
from_carry, from_current, overage, refund
```

### 8.2 `credit_ledger.csv`

Contains credit grants, consumption, carry-forward usage, restoration
and related balance information.

Expected columns:

``` text
member_id, ts, entry, reference, credits, carry_balance,
current_balance, overage_credits
```

### 8.3 `bookings_register.csv`

Contains the booking register generated by the application. The exact
columns are defined by the report-writing implementation and should be
kept aligned with the generated CSV.

### 8.4 `invoices.csv`

Contains the monthly invoice records.

Column order:

``` text
invoice_id, member_id, plan_fee, upgrade_charges, room_overage,
desk_overage, day_pass, no_show_fees, freeze_fees, freeze_waiver,
subtotal, gst, total, late_interest_prev, amount_due
```

## 9. Command Processing

The command parser reads `data/commands.txt`. It skips blank lines and
comment lines and separates command fields using `|`.

The application controller in `src/main.py` handles the supported
command operations. The current command processing includes booking,
check-in, cancellation, plan events, cycle close, payment and
booking-register/report operations.

The command names and argument order must follow the supplied command
file format. The illustrative commands from the initial design document
should not be treated as the authoritative syntax unless they match the
actual parser and input data.

## 10. Testing and Current Verification

The project uses Python's `unittest`-compatible test suite and is run
with `pytest`.

Test modules cover booking validation, cancellation and no-shows, credit
calculations, invoices, membership rules and plan management.

The previously reported full-suite baseline was:

``` text
139 passed, 1 warning
```

After that baseline, additional tests were added for the 31-day upgrade
boundary and TEAM pooled-credit usage; the user reported the relevant
tests passing. Do not treat the earlier count of 139 as the current
total after those additions.

The application was also run with:

``` bash
python -m src.main
```

The user confirmed that the required output files were generated
successfully.

### 10.1 Verification approach

For changes to existing implementation:

1.  Identify the relevant business rule and implementation function.
2.  Inspect the current code and relevant tests.
3.  Make the smallest necessary change only when a requirement is not
    met.
4.  Run the relevant test module.
5.  Run the full test suite after a meaningful group of changes.
6.  Run the application and inspect the generated output files.

Tests should verify required behaviour without adding duplicate tests
that do not provide meaningful additional coverage.

## 11. Implementation Timeline

The project was developed according to the following seven-day plan.

  -----------------------------------------------------------------------
  Day                     Main target             Implementation focus
  ----------------------- ----------------------- -----------------------
  Day 1                   Design, diagrams, BR    Initial design and
                          register and GitHub     project setup.
                          setup                   

  Day 2                   Dataset integration,    Data loading,
                          registration,           member/plan handling
                          membership and parser   and command parsing.

  Day 3                   Booking engine,         Booking checks,
                          validation and capacity overlap, advance
                                                  windows, freeze and
                                                  capacity.

  Day 4                   Credit ledger, peak     Slot-based credit
                          pricing, FIFO and       calculation,
                          overage                 carry-forward and usage
                                                  accounting.

  Day 5                   Cancellation, no-show,  Refunds, no-show fees,
                          upgrades, downgrades    membership changes and
                          and freeze              freeze handling.

  Day 6                   Invoices, GST, reports  Invoice calculation,
                          and integration         CSV generation and
                                                  integration.

  Day 7                   Edge cases, full        Edge-case review,
                          testing, README and     application run and
                          demo preparation        output verification.
  -----------------------------------------------------------------------

## 12. Design Decisions and Boundaries

The following decisions describe the current implementation:

1.  The application is a command-file-driven Python backend; no web UI
    or payment gateway is included.
2.  The application uses dictionaries and lists for its working records
    rather than requiring a class-based domain model.
3.  A TEAM member's room credits are pooled in a shared monthly ledger.
4.  The upgrade effective date is included in the remaining-day
    calculation.
5.  Exactly 24 hours before a booking receives a 50% cancellation
    refund.
6.  The first room no-show in a billing month is free; the second and
    subsequent room no-shows incur ₹200 each under the current
    implementation.
7.  A check-in exactly 15 minutes after booking start is valid.
8.  Freeze waivers are split by calendar month; if the plan fee has
    already been paid, the waiver becomes an account credit.
9.  The seven-day invoice grace period means payment exactly seven days
    after issue has no late interest.
10. Carry-forward limits are rounded down to a whole credit.

## 13. Items to Recheck Before Final Submission

These are verification tasks, not claims that the current implementation
is incomplete:

-   Confirm that the exact 12.5-to-12 carry-forward boundary has a
    dedicated test if the evaluator expects a test specifically for that
    example.
-   Consider an end-to-end same-day double-no-show test if additional
    integration coverage is required.
-   Confirm the final generated CSV headers against the official
    expected output format.
-   Confirm that the final README run instructions and repository file
    tree match the submitted version.
-   Run the full test suite and `python -m src.main` from a clean
    checkout before submission.

------------------------------------------------------------------------

**End of Design Document -- Version 2.0**
