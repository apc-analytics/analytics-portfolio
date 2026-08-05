"""
APC Wellness — synthetic accounts, members, plans, subscriptions generator.

Generates the base population for the fictional APC Wellness warehouse:
- 12 employer/health-plan accounts + ~100 individual self-pay accounts
- ~500 total members, 30 of which are reserved (via `is_fitbit_seed`) to
  later be mapped onto the real FitBit Fitness Tracker Data users in
  generate_workouts.py
- 2 plans (Standard, Premium)
- One subscription per member, billed per-enrolled-member (org contracts
  bill at a negotiated per-member rate; individuals bill at plan list price)

Run this first. Output: accounts.csv, members.csv, plans.csv, subscriptions.csv
in the same folder as this script.

Usage:
    python generate_accounts_members.py
"""

import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

SEED = 42
random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

OUT_DIR = Path(__file__).parent
TOTAL_MEMBERS_TARGET = 500
FITBIT_SEED_COUNT = 30  # members later mapped to real FitBit users

# Employer accounts: (name, industry, member_count)
EMPLOYER_SIZES = [120, 95, 70, 55, 45, 40, 32, 28, 20, 15, 12, 10]  # sums to 542... trimmed below

INDUSTRIES = [
    "Retail", "Logistics", "Manufacturing", "Financial Services",
    "Technology", "Healthcare", "Hospitality", "Education",
    "Professional Services", "Construction", "Insurance", "Media",
]

PLAN_ROWS = [
    {"plan_id": "plan_standard", "plan_name": "Standard", "tier": "standard", "monthly_price": 14.99},
    {"plan_id": "plan_premium", "plan_name": "Premium", "tier": "premium", "monthly_price": 24.99},
]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def random_join_date() -> date:
    # Company "founded" ~2 years ago; joins spread across that window,
    # weighted toward more recent (growth over time).
    days_ago = int(random.triangular(0, 730, 60))
    return date.today() - timedelta(days=days_ago)


def build_employer_accounts():
    accounts, members = [], []
    sizes = EMPLOYER_SIZES[:]
    # trim total employer-sponsored members down to ~400
    target_employer_total = 400
    scale = target_employer_total / sum(sizes)
    sizes = [max(8, round(s * scale)) for s in sizes]

    for i, size in enumerate(sizes):
        account_id = new_id("acct")
        industry = INDUSTRIES[i % len(INDUSTRIES)]
        account_name = f"{fake.company()} {random.choice(['Inc.', 'Group', 'Holdings', 'Co.'])}"
        per_member_rate = round(random.uniform(8.0, 15.0), 2)
        accounts.append({
            "account_id": account_id,
            "account_type": "organization",
            "account_name": account_name,
            "industry": industry,
            "status": "active",
            "per_member_rate": per_member_rate,
        })
        for _ in range(size):
            members.append(_build_member(account_id, sponsored=True))
    return accounts, members


def build_individual_accounts(count: int):
    accounts, members = [], []
    for _ in range(count):
        account_id = new_id("acct")
        accounts.append({
            "account_id": account_id,
            "account_type": "individual",
            "account_name": None,
            "industry": None,
            "status": "active",
            "per_member_rate": None,
        })
        members.append(_build_member(account_id, sponsored=False))
    return accounts, members


def _build_member(account_id: str, sponsored: bool) -> dict:
    return {
        "member_id": new_id("mem"),
        "account_id": account_id,
        "email": fake.unique.email(),
        "join_date": random_join_date().isoformat(),
        "eligibility_status": "enrolled",  # billing model = per enrolled/active member only
        "sponsored": sponsored,
        "is_fitbit_seed": False,  # set True on 30 rows after generation
    }


def assign_plans_and_subscriptions(accounts_by_id: dict, members: list):
    subscriptions = []
    for m in members:
        plan = random.choices(PLAN_ROWS, weights=[0.75, 0.25])[0]  # most on Standard
        acct = accounts_by_id[m["account_id"]]
        if m["sponsored"]:
            billed_amount = acct["per_member_rate"]
        else:
            billed_amount = plan["monthly_price"]
        start = date.fromisoformat(m["join_date"])
        subscriptions.append({
            "subscription_id": new_id("sub"),
            "member_id": m["member_id"],
            "plan_id": plan["plan_id"],
            "start_date": start.isoformat(),
            "end_date": "",
            "status": "active",
            "billed_amount": billed_amount,
        })
    return subscriptions


def main():
    employer_accounts, employer_members = build_employer_accounts()
    remaining = TOTAL_MEMBERS_TARGET - len(employer_members)
    individual_accounts, individual_members = build_individual_accounts(remaining)

    accounts = employer_accounts + individual_accounts
    members = employer_members + individual_members

    # Mark 30 members (spread across both account types) as FitBit seeds
    seed_pool = random.sample(members, FITBIT_SEED_COUNT)
    for m in seed_pool:
        m["is_fitbit_seed"] = True

    accounts_by_id = {a["account_id"]: a for a in accounts}
    subscriptions = assign_plans_and_subscriptions(accounts_by_id, members)

    # --- write CSVs ---
    with open(OUT_DIR / "plans.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PLAN_ROWS[0].keys())
        w.writeheader()
        w.writerows(PLAN_ROWS)

    with open(OUT_DIR / "accounts.csv", "w", newline="") as f:
        fieldnames = ["account_id", "account_type", "account_name", "industry", "status", "per_member_rate"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(accounts)

    with open(OUT_DIR / "members.csv", "w", newline="") as f:
        fieldnames = ["member_id", "account_id", "email", "join_date", "eligibility_status", "sponsored", "is_fitbit_seed"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(members)

    with open(OUT_DIR / "subscriptions.csv", "w", newline="") as f:
        fieldnames = ["subscription_id", "member_id", "plan_id", "start_date", "end_date", "status", "billed_amount"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(subscriptions)

    print(f"accounts: {len(accounts)} ({len(employer_accounts)} orgs, {len(individual_accounts)} individuals)")
    print(f"members: {len(members)} ({FITBIT_SEED_COUNT} flagged as FitBit seeds)")
    print(f"subscriptions: {len(subscriptions)}")
    print("Wrote accounts.csv, members.csv, plans.csv, subscriptions.csv")


if __name__ == "__main__":
    main()