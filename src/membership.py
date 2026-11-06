def validate_member(member,plans,members):
    member_id=member["member_id"]
    plan_name=member["plan"]
    seats=member["seats"]

    if member_id in members:
        raise ValueError(f"Member ID already exists: {member_id}")

    if plan_name not in plans:
        raise ValueError(f"Plan does not exist: {plan_name}")
    if seats < 1 :
        raise ValueError(f"Seats must be at least 1 for member ID: {member_id}")

    minimum_seats = plans[plan_name]["min_seats"]
    
    if minimum_seats is not None and seats < minimum_seats:
        raise ValueError(
            f"{plan_name} requires at least {minimum_seats} seats"
        )

    return True


def register_member(member, plans, members):
    validate_member(member, plans, members)

    members[member["member_id"]] = member

    return member



def calculate_membership_allowance(member, plans):
    plan_name = member["plan"]
    seats = member["seats"]

    plan = plans[plan_name]

    # Calculate room credits
    room_credits = plan["room_credits"]

    if plan["unit"] == "per seat per month":
        room_credits = room_credits * seats

    # Calculate plan fee
    plan_fee = plan["monthly_fee"]

    if plan["unit"] == "per seat per month":
        plan_fee = plan_fee * seats

    return {
        "member_id": member["member_id"],
        "plan": plan_name,
        "plan_fee": plan_fee,
        "fee_unit": plan["unit"],
        "desk_days": plan["desk_days"],
        "room_credits": room_credits,
        "opening_carry_credits": member["opening_carry_credits"]
    }
