# PS-101 – Co-working Membership, Desk/Room Booking and Credit Ledger Engine

**Team:** T045  
**Project ID:** T045-PS-101  
**Section:** CSDS B  
**Language:** Python 3.10+

## 1. Project Overview

This project is a command-file-driven backend system for managing memberships, desk and meeting-room bookings, room credits, plan changes, cancellations, freezes and monthly invoices for a co-working space.

The application reads member, plan, room, booking and plan-event data from CSV files. It then processes commands in the order provided in `data/commands.txt`, applies the project business rules and generates CSV output files.

The project is implemented as a Python backend. It does not include a web interface or a payment gateway.

## 2. Main Features

- Load membership plans, members, rooms, bookings and plan events from input files.
- Validate desk and meeting-room booking requests.
- Check room capacity, booking duration, overlapping bookings and advance-booking limits.
- Calculate room-credit usage, including peak-time and weekend rates.
- Maintain monthly credit balances, FIFO credit usage, carry-forward credits and expiry.
- Process membership upgrades, downgrades and freezes.
- Apply cancellation refunds and no-show rules.
- Calculate room and desk overage charges.
- Generate monthly invoices with GST and applicable late-payment interest.
- Generate booking decisions, credit-ledger records and invoice reports.

## 3. Technologies Used

- **Python 3.10+** – application logic and file processing.
- **CSV files** – input data and generated reports.
- **Python `unittest` / pytest** – automated testing.

The application logic primarily uses Python's standard library.

## 4. Project Structure

```text
T045-PS-101/
│
├── data/
│   ├── members.csv
│   ├── plans.csv
│   ├── rooms.csv
│   ├── bookings.csv
│   ├── plan_events.csv
│   ├── commands.txt
│   └── README.md
│
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── data_loader.py
│   ├── command_parser.py
│   ├── membership.py
│   ├── booking.py
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
│   ├── invoices.csv
│   └── bookings_register.csv
│
├── docs/
│   ├── design_document.md
│   └── decision_log.md
│
├── README.md
└── requirements.txt
```

The `outputs/` directory contains files generated when the application is run. The exact files present may depend on the commands and reports produced by the current implementation.

## 5. Input Files

The application reads its input data from the `data/` directory.

| File | Description |
|---|---|
| `members.csv` | Member details, membership plan, seat count and opening credit information |
| `plans.csv` | Plan fees, desk-day allowances, room-credit allowances and booking limits |
| `rooms.csv` | Meeting-room details, capacity and credit rates |
| `bookings.csv` | Booking request details |
| `plan_events.csv` | Membership upgrade, downgrade and freeze events |
| `commands.txt` | Commands that determine the order in which operations are processed |
| `README.md` | Sample data pack format and planted-scenario reference |

Commands in `commands.txt` are processed in file order. Refer to `data/README.md` for the sample data format, command arguments, output column definitions and planted scenarios.

## 6. Setup and Installation

### Prerequisites

- Python 3.10 or later
- pip
- Git (if cloning the repository)

### Clone the repository

```bash
git clone https://github.com/Thanuja-coder/T045-PS-101.git
cd T045-PS-101
```

### Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install the testing dependency

If `requirements.txt` is present and lists the project dependencies, install them using:

```bash
pip install -r requirements.txt
```

If pytest is not installed in the environment, install it using:

```bash
python -m pip install pytest
```

## 7. How to Run the Project

Run the following command from the **root project directory**:

```bash
python -m src.main
```

The application loads the input data, processes the commands and generates the output files in the `outputs/` directory.

A successful run displays a data-loading confirmation and the number of members, bookings and commands loaded. Booking and command results are also printed while processing.

## 8. Generated Output Files

| Output file | Description |
|---|---|
| `booking_decisions.csv` | Records booking, check-in, cancellation and no-show decisions |
| `credit_ledger.csv` | Records credit grants, usage, refunds, carry-forward and related ledger movements |
| `invoices.csv` | Contains monthly invoice details, charges, GST, totals and late interest |
| `bookings_register.csv` | Contains the booking register/report generated by the application |

The three main evaluation CSV files are `booking_decisions.csv`, `credit_ledger.csv` and `invoices.csv`. Their column order and formats should follow the sample data pack specification in `data/README.md`.

## 9. Running the Tests

Run the complete test suite from the root project directory:

```bash
python -m pytest
```

To run an individual test module:

```bash
python -m pytest tests/test_booking.py
```

The test suite covers the project's membership, booking, credit-ledger, cancellation, plan-management, invoice and edge-case behaviour.

## 10. Business Rules and Design Documents

The system follows the business rules provided in the PS-101 project brief and the documented clarifications for the sample data pack.

Refer to:

- **Design document:** architecture, domain design, business-rule register and diagrams.
- **Decision log:** implementation decisions and recorded assumptions.
- **Sample data README:** input formats, command definitions, expected evaluation output formats and planted scenarios.

## 11. Team

**Team ID:** T045  
**Project ID:** T045-PS-101  
**Section:** CSDS B
