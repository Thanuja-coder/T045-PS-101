# T045 – PS-101
## Decision Log

**Project:** Co-working Membership, Desk/Room Booking and Credit Ledger Engine  
**Team ID:** T045  
**Team Members:** Thanuja Madhu Chandre Gowda, Thoshin S  
**Section:** CSDS B

## 1. Introduction

While developing the project, we came across a few situations where we had two possible ways to implement a rule. We selected the option that matched the project requirements and recorded the reasons below.

## 2. Decisions

### 1. Using dictionaries and lists

**Options:** Using Python classes or using dictionaries and lists.

**Decision:** We used dictionaries and lists.

**Reason:** They were simple to use and made it easy to store and update the data.

### 2. Monthly billing cycle

**Options:** Using the member's joining date or using calendar months.

**Decision:** We used calendar months.

**Reason:** It made credit calculation, carry-forward and invoice generation easier.

### 3. TEAM plan credits

**Options:** Giving each seat separate credits or sharing credits between all seats.

**Decision:** We used one shared credit balance for the TEAM membership.

**Reason:** TEAM credits are pooled. For example, 3 seats receive 180 credits together.

### 4. Room credit calculation

**Options:** Rounding every half-hour slot separately or calculating the booking total.

**Decision:** We calculate credits using half-hour slots and round up the peak portion.

**Reason:** This follows the required calculation. For example, a 09:30–10:30 booking in a 4-seat room on a weekday costs 3 credits.

### 5. Carry-forward credits

**Options:** Carrying all unused credits or applying the 25% limit.

**Decision:** We carry forward only up to 25% of the monthly credits and round down.

**Reason:** This follows the carry-forward rule. For example, 12.5 credits becomes 12.

### 6. Which credits to use first

**Options:** Using current-month credits first or carried-forward credits first.

**Decision:** We use carried-forward credits first.

**Reason:** They expire earlier, so using them first avoids losing them.

### 7. Cancellation refund at exactly 24 hours

**Options:** Giving a full refund or giving a 50% refund.

**Decision:** We give a 50% refund.

**Reason:** Exactly 24 hours comes under the 2–24 hour refund category.

### 8. Refund rounding

**Options:** Rounding to the nearest credit or rounding down.

**Decision:** We round down.

**Reason:** The refund should not be more than the allowed amount. For example, 50% of 3 credits gives 1 credit.

### 9. Check-in time limit

**Options:** Accepting check-in exactly at 15 minutes or rejecting it.

**Decision:** We accept check-in exactly at 15 minutes.

**Reason:** The 15-minute check-in window includes the deadline.

### 10. No-show fee

**Options:** Charging from the first no-show or from the second no-show.

**Decision:** The first room no-show is free. From the second room no-show onwards, we charge ₹200.

**Reason:** This follows the final no-show rule. Separate bookings on the same day are counted separately.

### 11. Freeze across two months

**Options:** Calculating the full freeze waiver in one month or splitting it between months.

**Decision:** We calculate the waiver separately for each month.

**Reason:** Invoices are generated monthly, so the waiver must be added to the correct month's invoice.

### 12. Freeze waiver after payment

**Options:** Giving the waiver as a cash refund or adjusting it in a future invoice.

**Decision:** We keep it as a credit for the next invoice if the plan fee is already paid.

**Reason:** This avoids giving a cash refund for an already-paid invoice.

### 13. Membership upgrade

**Options:** Applying the upgrade from the next month or from the requested date.

**Decision:** We apply the upgrade from the requested date.

**Reason:** The extra fee and credits are calculated for the remaining days of that month.

### 14. Upgrade calculation

**Options:** Using a fixed 30-day month or the actual number of days in the month.

**Decision:** We use the actual number of days.

**Reason:** Months have different numbers of days. This gives the correct prorated fee and credits.

### 15. Membership downgrade

**Options:** Applying the downgrade immediately or from the next month.

**Decision:** We apply it from the next billing month.

**Reason:** The member can continue using the current plan until the end of the month.

### 16. Invoice late payment

**Options:** Charging interest from the seventh day or after the seven-day grace period.

**Decision:** We do not charge interest if payment is made exactly seven days after the invoice date.

**Reason:** Interest is applied only after the grace period.

### 17. Booking rejection order

**Options:** Showing all failed rules or stopping at the first failed rule.

**Decision:** We stop at the first failed rule, following the required order.

**Reason:** This keeps the rejection reason consistent with the project requirements.

### 18. Saving output

**Options:** Showing results only in the terminal or saving them in CSV files.

**Decision:** We generate CSV files.

**Reason:** It is easier to check booking decisions, credit balances and invoices in CSV format.

## 3. Conclusion

These are the main decisions we made while developing the project. We selected each approach based on the given requirements and used it in our implementation.