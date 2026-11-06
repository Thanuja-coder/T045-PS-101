import csv
from decimal import Decimal 
from pathlib import Path
from datetime import date, datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
PLANS_FILE = PROJECT_DIR / 'data' / 'plans.csv'

def load_plans():
    plans={}
    with open(PLANS_FILE,'r',newline="")as file:
        reader=csv.DictReader(file)
        for row in reader:
            plan_name=row['plan'].strip()
            if row["desk_days"].strip() =="UNLIMITED":
                desk_days="UNLIMITED"
            elif row["desk_days"].strip() =="":
                desk_days=None
            else:
                desk_days=int(row["desk_days"].strip())

            max_bookings=row["max_future_room_bookings"].strip()
            min_seats=row["min_seats"].strip()

            plans[plan_name]={
                "plan":plan_name,
                "monthly_fee": Decimal(row["monthly_fee"]),
                "unit": row["unit"].strip(),
                "desk_days":desk_days,
                "room_credits": int(row["room_credits"]),
                "advance_days": int(row["advance_days"]),
                "max_future_room_bookings": (
                    int(max_bookings) if max_bookings else None
                ),
                "min_seats": int(min_seats) if min_seats else None
            }

    return plans

MEMBERS_FILE=PROJECT_DIR / 'data' / 'members.csv'

def load_members():
    members={}
    with open(MEMBERS_FILE,'r',newline="") as file:
        reader=csv.DictReader(file)
        for row in reader:
            member_id=row["member_id"].strip()
            company = row["company"].strip() or None
            dedicated_desk = row["dedicated_desk"].strip() or None
            gstin = row["gstin"].strip() or None

            member = {
                "member_id": member_id,
                "member_name": row["member_name"].strip(),
                "company": company,
                "plan": row["plan"].strip(),
                "seats": int(row["seats"]),
                "billing_cycle_start": date.fromisoformat(
                    row["billing_cycle_start"]
                ),
                "dedicated_desk": dedicated_desk,
                "opening_carry_credits": int(
                    row["opening_carry_credits"]
                ),
                "freeze_days_used_2026": int(
                    row["freeze_days_used_2026"]
                ),
                "gstin": gstin
            }

            if member_id in members:
                raise ValueError(f"Duplicate member ID: {member_id}")

            members[member_id] = member
    return members



def load_rooms():
    rooms = {}

    with open(PROJECT_DIR / "data" / "rooms.csv", "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            room_id = row["room_id"].strip()

            rooms[room_id] = {
                "room_id": room_id,
                "room_type": row["room_type"].strip(),
                "seats": int(row["seats"]),
                "credits_per_30min": int(row["credits_per_30min"])
            }

    return rooms


def load_bookings():
    bookings = {}

    with open(PROJECT_DIR / "data" / "bookings.csv", "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            booking_id = row["booking_id"].strip()

            bookings[booking_id] = {
                "booking_id": booking_id,
                "member_id": row["member_id"].strip(),
                "requested_ts": datetime.fromisoformat(row["requested_ts"]),
                "resource": row["resource"].strip(),
                "start_ts": datetime.fromisoformat(row["start_ts"]),
                "end_ts": datetime.fromisoformat(row["end_ts"]),
                "attendees": int(row["attendees"]) if row["attendees"].strip() else None,
                "booked_by": row["booked_by"].strip() or None
            }

    return bookings


def load_plan_events():
    events = {}

    with open(PROJECT_DIR / "data" / "plan_events.csv", "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            event_id = row["event_id"].strip()

            events[event_id] = {
                "event_id": event_id,
                "member_id": row["member_id"].strip(),
                "requested_ts": datetime.fromisoformat(row["requested_ts"]),
                "event_type": row["event_type"].strip(),
                "effective_date": date.fromisoformat(row["effective_date"]),
                "new_plan": row["new_plan"].strip() or None,
                "seats": int(row["seats"]) if row["seats"].strip() else None,
                "freeze_days": int(row["freeze_days"]) if row["freeze_days"].strip() else None
            }

    return events
