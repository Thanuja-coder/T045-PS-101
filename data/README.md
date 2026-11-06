# PS-101 – Co-working Membership, Desk/Room Booking and Credit Ledger Engine — Sample Data Pack

Prepared by 10 SECONDS for Team T045.

## Files

| File | What it holds | Row count |
|---|---|---|
| `plans.csv` | The four plans with fee, desk-days, room credits, advance window and limits | 4 data rows |
| `rooms.csv` | Meeting rooms with seats and credits per 30 minutes | 5 data rows |
| `members.csv` | 20 members: plan, seats, billing start, opening carry-forward credits | 20 data rows |
| `bookings.csv` | 120 desk and room booking requests over January and February 2026 | 120 data rows |
| `plan_events.csv` | 15 upgrade / downgrade / freeze requests | 15 data rows |
| `commands.txt` | Bookings, check-ins, cancellations, plan events, cycle closes, payments and prints | 276 command lines (excluding comments) |

Row numbers quoted below are 1-based data-row numbers (the header is row 0). Line numbers for `commands.txt` are physical line numbers including comment lines.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with 2 places (no commas, no symbol); percentages as plain numbers (12.5 means 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix. An empty cell means "not applicable" and only occurs in columns whose notes say so.

### `plans.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| plan | enum | — | DAY_PASS, FLEX, DEDICATED, TEAM | — |
| monthly_fee | decimal | Rs | — | DAY_PASS: per day |
| unit | string | — | — | — |
| desk_days | string | — | — | number or UNLIMITED |
| room_credits | int | credits | — | TEAM: per seat, pooled |
| advance_days | int | days | — | — |
| max_future_room_bookings | int | — | — | FLEX only |
| min_seats | int | — | — | TEAM only |

### `rooms.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| room_id | string | — | — | — |
| room_type | string | — | — | — |
| seats | int | — | — | attendees above -> capacity breach |
| credits_per_30min | int | — | — | — |

### `members.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| member_id | string | Mnn | — | — |
| member_name | string | — | — | — |
| company | string | — | — | — |
| plan | enum | — | — | plan on 2026-01-01 |
| seats | int | — | — | — |
| billing_cycle_start | date | — | — | cycles are calendar months |
| dedicated_desk | string | — | — | DEDICATED only |
| opening_carry_credits | decimal | credits | — | carried from December 2025 |
| freeze_days_used_2026 | int | days | — | — |
| gstin | string | — | — | — |

### `bookings.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| booking_id | string | BK-nnn | — | — |
| member_id | string | — | members.csv | — |
| requested_ts | timestamp | — | — | BOOK is processed at this time |
| resource | string | — | HOT_DESK or room_id | — |
| start_ts | timestamp | — | — | — |
| end_ts | timestamp | — | — | — |
| attendees | int | — | — | rooms only |
| booked_by | string | — | — | TEAM seat |

### `plan_events.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| event_id | string | PE-nn | — | — |
| member_id | string | — | members.csv | — |
| requested_ts | timestamp | — | — | — |
| event_type | enum | — | UPGRADE, DOWNGRADE, FREEZE | — |
| effective_date | date | — | — | freeze start / change date |
| new_plan | enum | — | — | — |
| seats | int | — | — | — |
| freeze_days | int | days | — | — |

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands must be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. An empty argument (two pipes in a row) means "not supplied". Every command used in this pack:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `BOOK` | `booking_id` | Validate and accept / reject a booking request |
| `CHECKIN` | `booking_id|timestamp` | Check in (rooms: within 15 min of start; desks: that day) |
| `CANCEL` | `booking_id|timestamp` | Cancel with the refund ladder |
| `PLAN_EVENT` | `event_id` | Upgrade, downgrade or freeze |
| `CLOSE_CYCLE` | `YYYY-MM` | Close the month: invoices, carry-forward, expiry |
| `PAYMENT` | `invoice_id|timestamp` | Invoice payment (invoice id INV-<member>-<YYYYMM>) |
| `PRINT_BOOKINGS` | `from|to` | Booking register |
| `PRINT_LEDGER` | `member_id|date` | Credit ledger of a member up to a date |
| `PRINT_INVOICES` | `YYYY-MM` | Invoices of a month |

## Planted scenarios

Every edge case in the brief, mapped to the exact record where it occurs, followed by extra traps.

- **EC-01 Booking from 09:30 to 10:30 crossing into peak on a weekday**
  - BK-028: Wednesday 09:30-10:30 in a 4-seater: slot 09:30 off-peak = 1 credit, slot 10:00 peak = 1 x 1.5 -> rounded up to 2 -> 3 credits — `bookings.csv BK-028 (row 28)`
- **EC-02 Upgrade on the last day of a 31-day month**
  - PE-06: FLEX -> DEDICATED on 2026-01-31, the last day of a 31-day month: remaining days 1 / 31 -> charge (15,000 - 8,000) x 1 / 31 = 225.81 -> Rs 226; extra credits (40 - 20) x 1 / 31 = 0.65 -> 0 (rounded down). January invoice INV-M02-202601: 8,000 + 226 = 8,226 + 18% GST = Rs 9,707 — `plan_events.csv PE-06 (row 6)`
- **EC-03 Carry-forward of 12.5 credits (must round down to 12)**
  - M03 (TEAM, 3 seats, 180 pooled credits) uses 55 + 40 + 55 + 12.5 (Saturday board room at 0.5x) + 4 + 1 = 167.5 credits in January (BK-005 .. BK-060) -> 12.5 unused; the cap is 25% of 180 = 45 -> carry-forward 12 (rounded down to whole credits) into February — `bookings.csv BK-005 (row 5); bookings.csv BK-022 (row 22); bookings.csv BK-017 (row 17); bookings.csv BK-051 (row 51); bookings.csv BK-059 (row 59); bookings.csv BK-060 (row 60)`
- **EC-04 Cancellation exactly 24 h before start**
  - BK-040: booking of 3 credits starting 2026-01-22 09:30; CANCEL at 2026-01-21 09:30:00 = exactly 24 hours before -> not more than 24 h -> 50% band -> 1.5 rounded down -> 1 credit refunded — `bookings.csv BK-040 (row 40); commands.txt line 95`
- **EC-05 Freeze requested for 15 days spanning a cycle boundary**
  - PE-04: 15-day freeze 2026-01-25 .. 2026-02-08 crossing the month end: January waiver 8,000 x 7 / 31 = Rs 1,806 (plus the Rs 500 freeze fee), February waiver 8,000 x 8 / 28 = Rs 2,286; February credits 20 x 20 / 28 = 14.29 -> 14 (desk-days 10 x 20 / 28 -> 7). BK-070: hot-desk booking for 2026-02-03 -> REJECTED (frozen) — `plan_events.csv PE-04 (row 4); bookings.csv BK-070 (row 70)`
- **EC-06 TEAM plan with 3 seats where one seat uses all pooled credits**
  - M04 (TEAM, 3 seats, 60 x 3 = 180 pooled credits): seat-1 alone books BK-010, BK-013, BK-032, BK-052 = 55 + 55 + 40 + 30 = 180 credits, the whole pool; seat-2's booking BK-066 (2 credits) has no credits left -> accepted into overage (no unpaid invoice) -> 2 x Rs 150 = Rs 300 overage on INV-M04-202601 — `bookings.csv BK-010 (row 10); bookings.csv BK-013 (row 13); bookings.csv BK-032 (row 32); bookings.csv BK-052 (row 52); bookings.csv BK-066 (row 66)`
- **EC-07 Second no-show of the cycle on the same day as the first**
  - BK-078 (09:00) and BK-079 (15:00) on 2026-02-04 are never checked in -> two no-shows on the same day: credits forfeited on both, the second no-show of the cycle carries the Rs 200 fee — `bookings.csv BK-078 (row 78); bookings.csv BK-079 (row 79)`
- **EC-08 Invoice paid exactly on day 7 after issue**
  - INV-M07-202601 issued 2026-02-01, paid on 2026-02-08 (line 182) = day 7 -> not beyond 7 days -> no interest. Contrast INV-M08-202601 paid 2026-02-20 (line 241): 12 days late -> 1.5% x 12 / 30 of Rs 9,440 = Rs 57 added to the February invoice — `commands.txt lines 182, 241`
- **Extra traps (not in the brief, but realistic):**
  - BK-048: M09 (FLEX) already holds two future room bookings (BK-046, BK-047) -> third -> REJECTED (max 2 future bookings) — `bookings.csv BK-048 (row 48); bookings.csv BK-046 (row 46); bookings.csv BK-047 (row 47)`
  - BK-075: board room 09:00-13:00 = 2 x 5 + ceil(1.5 x 30) = 55 credits > M08's 25.0 available while the January invoice is unpaid -> REJECTED (unpaid invoice blocks overage); BK-076 within credits -> accepted — `bookings.csv BK-075 (row 75); bookings.csv BK-076 (row 76)`
  - BK-027: board room 2026-01-20 11:00, requested 9 days ahead by a FLEX member (window 7) AND overlapping M03's booking BK-017 -> overlap is checked first -> REJECTED with the overlap reason — `bookings.csv BK-027 (row 27); bookings.csv BK-017 (row 17)`
  - BK-018: M10 opens January with 5 carried credits; this 3-credit booking draws on them first (FIFO); the 2 carried credits left expire at the end of January, only unused January credits can carry — `bookings.csv BK-018 (row 18); members.csv M10 (row 10)`
  - PE-07: freeze requested while BK-071 (2026-02-04) is still in the future -> REJECTED. PE-12: DEDICATED -> FLEX downgrade requested 2026-02-10 -> takes effect only from the March cycle; February is billed as DEDICATED — `plan_events.csv PE-07 (row 7); bookings.csv BK-071 (row 71); plan_events.csv PE-12 (row 12)`

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these CSV files (header row, same conventions as above, rows sorted as stated). Where the brief is silent on a format detail the choice below is binding for evaluation.

### `booking_decisions.csv`

One row per BOOK / CANCEL / CHECKIN / no-show.

Columns, in order: `ts`, `booking_id`, `member_id`, `action`, `result`, `rule_id`, `credits`, `from_carry`, `from_current`, `overage`, `refund`

### `credit_ledger.csv`

One row per ledger movement.

Columns, in order: `member_id`, `ts`, `entry`, `reference`, `credits`, `carry_balance`, `current_balance`, `overage_credits`

### `invoices.csv`

One row per member per month.

Columns, in order: `invoice_id`, `member_id`, `plan_fee`, `upgrade_charges`, `room_overage`, `desk_overage`, `day_pass`, `no_show_fees`, `freeze_fees`, `freeze_waiver`, `subtotal`, `gst`, `total`, `late_interest_prev`, `amount_due`

Binding choices where the brief is silent: (1) cycles are calendar months for every member; credits for a booking come from the month of its start. (2) Credits per booking = off-peak slots + weekend slots x 0.5 + ceil(1.5 x peak slots), the round-up applied once per booking; weekend credits may end in .5. (3) Format checks (30-minute steps, 30 min to 4 h, attendees <= seats) come before the precedence list; the FLEX 2-future-bookings limit is part of the advance-window check. (4) Refund ladder: lead > 24 h 100%, 2 h <= lead <= 24 h floor(50%), < 2 h 0; refunds reverse overage first, then current, then carried credits. (5) The Rs 200 fee applies to the 2nd and every later room no-show of the month; desk bookings have no no-show fee. (6) A FLEX desk booking is overage when checked-in plus pending desk days already reach the allowance. (7) Freeze: days counted inclusive from effective_date; the Rs 500 fee is billed in the month of the request; later months' credit and desk-day grants are cut pro-rata (rounded down). (8) Carry-forward = floor(min(unused current-month credits, 25% of the month's plan grant)); carried credits never carry twice. (9) Invoice total = round(subtotal x 1.18); late interest = round(total x 1.5% x days beyond day 7 / 30), added untaxed to the next invoice.
