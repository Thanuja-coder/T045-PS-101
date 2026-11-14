# T045-PS-101
Co-working Membership, Desk/Room Booking and Credit Ledger Engine


# T045-PS-101
## Co-working Membership, Desk/Room Booking and Credit Ledger Engine

**Team ID:** T045  
**Team Members:** Thanuja Madhu Chandre Gowda and Thoshin S  
**Section:** CSDS B

### 1. Introduction

For this capstone project, we were asked to develop a backend engine for managing a co-working space.

When I understood the problem statement, I realised that managing a co-working space involves more than just booking desks and meeting rooms. The system also needs to manage different membership plans, room credits, booking restrictions, cancellations, plan changes and monthly invoices.

The main idea of our project is to process the commands provided through input files and generate the required booking decisions, credit ledgers and invoices.

This is a command-file-driven Python project. It does not have a user interface or a payment gateway.

### 2. Understanding the Project Logic

I divided the project into different modules so that each part handles a particular responsibility.

**Membership Plans**

The system supports four types of plans:

- **DAY_PASS:** A daily membership without room credits.
- **FLEX:** Includes 10 desk-days and 20 room credits per month.
- **DEDICATED:** Provides unlimited desk usage and 40 room credits.
- **TEAM:** Provides unlimited desk usage and 60 room credits per seat, with pooled credits.

Each plan has its own fee, allowances and booking restrictions.

**Booking Management**

Members can book hot desks and meeting rooms for specific dates and time periods.

Before accepting a booking, the system checks the applicable business rules. These include booking overlaps, advance booking limits, membership freeze status, unpaid invoices and credit availability.

The order of these checks is important because the first failed check determines the rejection reason.

**Room Credit Calculation**

Meeting room bookings consume credits based on the room capacity and booking duration.

The system also considers peak hours and weekend pricing. For example, a weekday booking that crosses into peak hours is calculated using its individual half-hour slots rather than applying one rate to the entire booking.

**Credit Ledger and Carry-Forward**

The credit ledger keeps track of the credits available to each member.

Credits are granted according to the membership plan. When a member uses a meeting room, the required credits are consumed from the ledger.

Unused room credits can be carried forward to the next cycle, subject to the 25% limit. Carried-forward credits are consumed before current-cycle credits, following the FIFO approach. Credits also expire according to the specified cycle rule.

If the available credits are not sufficient, the applicable overage is recorded for invoicing.

**Plan Changes and Membership Freeze**

The system handles plan upgrades, downgrades and membership freezes.

An upgrade takes effect on the same day, and the additional fee and credits are calculated proportionally. A downgrade takes effect from the next billing cycle.

During a freeze period, members cannot make bookings. The applicable fee waiver is calculated based on the freeze duration, and credits do not accrue during that period.

**Cancellation and No-Show**

When a member cancels a room booking, the refund depends on the time remaining before the booking starts.

The system also checks whether a member has checked in within the allowed time. If the member does not check in, the booking is treated according to the no-show rules.

**Invoice Generation**

Monthly invoices are generated for members based on their membership and usage.

The invoice calculation considers plan fees, applicable overage charges, no-show fees, freeze waivers and GST. Late payment interest is also handled according to the given business rules.

### 3. Project Structure

The project is divided into the following files:

| File / Folder | Purpose |
|---|---|
| `main.py` | Main program that connects the different modules and processes commands. |
| `data_loader.py` | Loads the input CSV files. |
| `command_parser.py` | Reads and processes commands from the command file. |
| `booking.py` | Handles booking validation and booking-related rules. |
| `credit_ledger.py` | Manages room credits, consumption, carry-forward and overage. |
| `membership.py` | Handles membership plans and member-related details. |
| `plan_manager.py` | Handles upgrades, downgrades and membership freezes. |
| `cancellation.py` | Handles cancellations and no-show rules. |
| `invoice.py` | Handles invoice calculations and charges. |
| `reports.py` | Generates the required CSV reports. |
| `data/` | Contains the input files. |
| `outputs/` | Contains the generated output files. |
| `tests/` | Contains test cases for checking the project logic. |

### 4. Technologies Used

- Python 3.10+
- CSV files for input and output
- Pytest for testing

### 5. How to Run the Project

**Step 1:** Install Python 3.10 or above.

**Step 2:** Open the project folder in VS Code.

**Step 3:** Open the terminal in the project root directory.

**Step 4:** Install the required package:

```bash
pip install -r requirements.txt
```

**Step 5:** Run the main program:

```bash
python -m src.main
```

The program reads the input data, processes the commands and generates the required output files inside the `outputs/` folder.

### 6. Generated Output Files

The project generates three main CSV files:

- **booking_decisions.csv:** Contains booking decisions such as ACCEPT and REJECT, along with the relevant booking details and rejection reasons.
- **credit_ledger.csv:** Maintains the member-wise credit transactions, including credit grants, consumption, carry-forward and overage.
- **invoices.csv:** Contains monthly invoice details, including applicable charges, GST and the final amount.

The project also supports commands to print booking registers, individual member ledgers and monthly invoices.

### 7. Testing

I used test cases to check the different parts of the project, including booking validation, credit calculations, carry-forward, cancellations, plan changes, freezes and invoice calculations.

After completing the implementation and report generation, I ran the complete test suite.

**Final test result: 139 tests passed.**

To run the tests:

```bash
pytest
```

### 8. What I Learned

Working on this project helped me understand how different business rules are connected in a backend system.

One of the important parts I worked on was the credit ledger, especially how carried-forward credits are consumed before current-cycle credits.

I also understood how peak-hour pricing is calculated when a booking covers both peak and off-peak time slots. Apart from this, I got practical experience with Python modules, CSV file handling, command processing and writing test cases.

Overall, this project helped me understand how to convert a given problem statement into a working backend application while following the specified business rules.