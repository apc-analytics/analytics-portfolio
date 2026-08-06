"""
APC Wellness — synthetic orders generator.

Generates one-time purchase orders (not recurring subscription billing —
that's the subscriptions table) for a subset of members: coaching
sessions, challenge entry fees, fitness assessments, and virtual event
tickets.

Not every member orders something — about 35% of members place at least
one order, and those who do place 1-4 over their tenure. Order dates are
constrained to fall between the member's join_date and today.

Run this after generate_accounts_members.py (it reads members.csv).
Output: orders.csv, in the same folder as this script.

Usage:
    python generate_orders.py
"""

import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT_DIR = Path(__file__).parent

# order_type -> (base price, jitter fraction)
ORDER_TYPES = {
    "coaching_session": (49.99, 0.10),
    "challenge_entry_fee": (9.99, 0.05),
    "fitness_assessment": (29.99, 0.08),
    "virtual_event_ticket": (14.99, 0.05),
}

ORDER_TYPE_WEIGHTS = [0.30, 0.35, 0.20, 0.15]  # matches ORDER_TYPES order

PCT_MEMBERS_WITH_ORDERS = 0.35
STATUS_WEIGHTS = {"completed": 0.90, "refunded": 0.07, "canceled": 0.03}


def new_id() -> str:
    return f"ord_{uuid.uuid4().hex[:12]}"


def random_order_date(join_date: date, today: date) -> date:
    span_days = max((today - join_date).days, 0)
    if span_days == 0:
        return join_date
    return join_date + timedelta(days=random.randint(0, span_days))


def build_order(member_id: str, join_date: date, today: date) -> dict:
    order_type, (base_price, jitter) = random.choices(
        list(ORDER_TYPES.items()), weights=ORDER_TYPE_WEIGHTS
    )[0]
    amount = round(base_price * (1 + random.uniform(-jitter, jitter)), 2)
    status = random.choices(
        list(STATUS_WEIGHTS.keys()), weights=list(STATUS_WEIGHTS.values())
    )[0]
    return {
        "order_id": new_id(),
        "member_id": member_id,
        "order_type": order_type,
        "order_date": random_order_date(join_date, today).isoformat(),
        "amount": amount,
        "status": status,
    }


def main():
    members_path = OUT_DIR / "members.csv"
    if not members_path.exists():
        raise SystemExit(f"{members_path} not found — run generate_accounts_members.py first.")

    with open(members_path, newline="", encoding="utf-8") as f:
        members = list(csv.DictReader(f))

    today = date.today()
    ordering_members = random.sample(members, int(len(members) * PCT_MEMBERS_WITH_ORDERS))

    orders = []
    for m in ordering_members:
        join_date = date.fromisoformat(m["join_date"])
        num_orders = random.choices([1, 2, 3, 4], weights=[0.50, 0.30, 0.15, 0.05])[0]
        for _ in range(num_orders):
            orders.append(build_order(m["member_id"], join_date, today))

    with open(OUT_DIR / "orders.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["order_id", "member_id", "order_type", "order_date", "amount", "status"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(orders)

    print(f"members with orders: {len(ordering_members)} of {len(members)} ({PCT_MEMBERS_WITH_ORDERS:.0%})")
    print(f"total orders: {len(orders)}")
    print("Wrote orders.csv")


if __name__ == "__main__":
    main()