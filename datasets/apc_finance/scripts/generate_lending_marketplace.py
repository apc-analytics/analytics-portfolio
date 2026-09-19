"""
APC Finance — lending marketplace generator.

Generates the full funnel for a fictional personal lending marketplace:
borrowers -> loan_applications -> loan_offers (from competing lenders)
-> loans (the one accepted offer, if any).

Fully synthetic — no public dataset fits a multi-lender marketplace's
competing-offer structure, so realistic dynamics are built in directly:

- Each lender has a minimum credit tier it will consider and its own APR
  band, so better-credit applications draw more competition and lower
  rates, worse-credit applications draw fewer offers (sometimes zero).
- Not every eligible lender bids on every application it could (a
  per-lender participation chance), adding realistic variability beyond
  just tier eligibility.
- Acceptance is weighted toward the lowest-APR offer but not
  deterministic, and a real share of borrowers decline every offer they
  receive rather than convert — matching genuine marketplace drop-off.
- origination_fee_pct/amount on `loans` represents APC Finance's own cut
  from the lender when a loan funds (the marketplace's revenue), not a
  fee charged to the borrower.
- No repayment/performance data exists anywhere in this generator,
  deliberately: a marketplace's business ends at funding, so tracking
  what happens after isn't something this company's data would contain.

Usage:
    python generate_lending_marketplace.py
"""

import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT_DIR = Path(__file__).parent
TOTAL_BORROWERS = 750
COMPANY_AGE_DAYS = 730

CREDIT_TIERS = ["Excellent", "Good", "Fair", "Poor"]
CREDIT_TIER_WEIGHTS = [0.15, 0.35, 0.35, 0.15]
CREDIT_TIER_RANK = {"Poor": 0, "Fair": 1, "Good": 2, "Excellent": 3}

LOAN_PURPOSES = ["debt_consolidation", "medical", "home_improvement", "major_purchase", "other"]
LOAN_PURPOSE_WEIGHTS = [0.40, 0.15, 0.20, 0.15, 0.10]
# (min_amount, max_amount) per purpose
PURPOSE_AMOUNT_RANGES = {
    "debt_consolidation": (5000, 35000),
    "medical": (1000, 15000),
    "home_improvement": (3000, 40000),
    "major_purchase": (2000, 25000),
    "other": (1000, 20000),
}

TERM_MONTHS_OPTIONS = [12, 24, 36, 48, 60]
TERM_MONTHS_WEIGHTS = [0.10, 0.20, 0.35, 0.20, 0.15]

NUM_APPLICATIONS_WEIGHTS = {1: 0.65, 2: 0.25, 3: 0.10}
LENDER_PARTICIPATION_CHANCE = 0.70  # of eligible lenders, chance each one actually bids
PCT_BORROWER_ACCEPTS_AN_OFFER = 0.75  # chance a borrower with 1+ offers accepts one

# (lender_name, min_credit_tier, apr_min, apr_max, origination_fee_pct)
LENDERS = [
    ("Meridian Personal Loans", "Excellent", 0.059, 0.099, 0.020),
    ("Northstar Lending Co.", "Excellent", 0.065, 0.110, 0.018),
    ("Bluegate Financial", "Good", 0.089, 0.150, 0.022),
    ("Harborline Credit Union", "Good", 0.079, 0.140, 0.015),
    ("Crestview Lending", "Good", 0.095, 0.165, 0.025),
    ("Pinnacle Consumer Finance", "Fair", 0.130, 0.220, 0.030),
    ("Ashford Capital Partners", "Fair", 0.140, 0.230, 0.028),
    ("Summit Bridge Lending", "Fair", 0.120, 0.210, 0.032),
    ("Redwood Trust Loans", "Poor", 0.220, 0.359, 0.045),
    ("Ironclad Financial", "Poor", 0.199, 0.359, 0.040),
]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def random_join_date(today: date) -> date:
    days_ago = int(random.triangular(0, COMPANY_AGE_DAYS, 60))
    return today - timedelta(days=days_ago)


def build_borrowers(today: date):
    borrowers = []
    for _ in range(TOTAL_BORROWERS):
        borrowers.append({
            "borrower_id": new_id("brw"),
            "email": f"borrower{uuid.uuid4().hex[:8]}@example.net",
            "join_date": random_join_date(today).isoformat(),
            "credit_tier": random.choices(CREDIT_TIERS, weights=CREDIT_TIER_WEIGHTS)[0],
        })
    return borrowers


def build_lenders():
    lenders = []
    for name, min_tier, apr_min, apr_max, fee_pct in LENDERS:
        lenders.append({
            "lender_id": new_id("lnd"),
            "lender_name": name,
            "min_credit_tier": min_tier,
            "apr_min": apr_min,
            "apr_max": apr_max,
            "origination_fee_pct": fee_pct,
            "status": "active",
        })
    return lenders


def eligible_lenders(lenders: list, borrower_tier: str):
    borrower_rank = CREDIT_TIER_RANK[borrower_tier]
    return [l for l in lenders if CREDIT_TIER_RANK[l["min_credit_tier"]] <= borrower_rank]


def build_application(borrower: dict, today: date) -> dict:
    join_date = date.fromisoformat(borrower["join_date"])
    span_days = max((today - join_date).days, 0)
    app_date = join_date + timedelta(days=random.randint(0, span_days)) if span_days else join_date
    purpose = random.choices(LOAN_PURPOSES, weights=LOAN_PURPOSE_WEIGHTS)[0]
    min_amt, max_amt = PURPOSE_AMOUNT_RANGES[purpose]
    requested_amount = round(random.uniform(min_amt, max_amt), 2)
    return {
        "application_id": new_id("app"),
        "borrower_id": borrower["borrower_id"],
        "loan_purpose": purpose,
        "requested_amount": requested_amount,
        "application_date": app_date.isoformat(),
        "status": None,  # filled in after offers/acceptance are resolved
    }


def build_offer(application: dict, lender: dict, today: date) -> dict:
    app_date = date.fromisoformat(application["application_date"])
    offer_date = app_date + timedelta(days=random.randint(0, 3))
    if offer_date > today:
        offer_date = today
    offered_amount = round(application["requested_amount"] * random.uniform(0.80, 1.05), 2)
    apr = round(random.uniform(lender["apr_min"], lender["apr_max"]), 4)
    term_months = random.choices(TERM_MONTHS_OPTIONS, weights=TERM_MONTHS_WEIGHTS)[0]
    return {
        "offer_id": new_id("off"),
        "application_id": application["application_id"],
        "borrower_id": application["borrower_id"],
        "lender_id": lender["lender_id"],
        "offered_amount": offered_amount,
        "apr": apr,
        "term_months": term_months,
        "offer_date": offer_date.isoformat(),
        "status": "pending",  # updated to accepted/declined below
    }


def choose_accepted_offer(offers: list) -> dict:
    """Weight acceptance toward lower APR, without being fully deterministic."""
    ranked = sorted(offers, key=lambda o: o["apr"])
    weights = [1 / (i + 1) for i in range(len(ranked))]
    return random.choices(ranked, weights=weights)[0]


def main():
    today = date.today()
    borrowers = build_borrowers(today)
    lenders = build_lenders()

    applications, offers, loans = [], [], []

    for borrower in borrowers:
        num_apps = random.choices(
            list(NUM_APPLICATIONS_WEIGHTS.keys()),
            weights=list(NUM_APPLICATIONS_WEIGHTS.values()),
        )[0]
        for _ in range(num_apps):
            app = build_application(borrower, today)
            app_offers = []
            for lender in eligible_lenders(lenders, borrower["credit_tier"]):
                if random.random() < LENDER_PARTICIPATION_CHANCE:
                    app_offers.append(build_offer(app, lender, today))

            if not app_offers:
                app["status"] = "no_offers"
            elif random.random() < PCT_BORROWER_ACCEPTS_AN_OFFER:
                accepted = choose_accepted_offer(app_offers)
                for o in app_offers:
                    o["status"] = "accepted" if o["offer_id"] == accepted["offer_id"] else "declined"
                app["status"] = "funded"
                funded_date = date.fromisoformat(accepted["offer_date"]) + timedelta(days=random.randint(0, 7))
                if funded_date > today:
                    funded_date = today
                loans.append({
                    "loan_id": new_id("loan"),
                    "offer_id": accepted["offer_id"],
                    "borrower_id": app["borrower_id"],
                    "lender_id": accepted["lender_id"],
                    "funded_amount": accepted["offered_amount"],
                    "apr": accepted["apr"],
                    "term_months": accepted["term_months"],
                    "funded_date": funded_date.isoformat(),
                    "origination_fee_pct": next(l["origination_fee_pct"] for l in lenders if l["lender_id"] == accepted["lender_id"]),
                })
            else:
                for o in app_offers:
                    o["status"] = "declined"
                app["status"] = "offers_declined"

            applications.append(app)
            offers.extend(app_offers)

    for loan in loans:
        loan["origination_fee_amount"] = round(loan["funded_amount"] * loan["origination_fee_pct"], 2)

    with open(OUT_DIR / "borrowers.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["borrower_id", "email", "join_date", "credit_tier"])
        w.writeheader()
        w.writerows(borrowers)

    with open(OUT_DIR / "lenders.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["lender_id", "lender_name", "min_credit_tier", "apr_min", "apr_max", "origination_fee_pct", "status"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(lenders)

    with open(OUT_DIR / "loan_applications.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["application_id", "borrower_id", "loan_purpose", "requested_amount", "application_date", "status"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(applications)

    with open(OUT_DIR / "loan_offers.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["offer_id", "application_id", "borrower_id", "lender_id", "offered_amount", "apr", "term_months", "offer_date", "status"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(offers)

    with open(OUT_DIR / "loans.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["loan_id", "offer_id", "borrower_id", "lender_id", "funded_amount", "apr", "term_months", "funded_date", "origination_fee_pct", "origination_fee_amount"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(loans)

    status_counts = {}
    for a in applications:
        status_counts[a["status"]] = status_counts.get(a["status"], 0) + 1

    print(f"borrowers: {len(borrowers)}")
    print(f"lenders: {len(lenders)}")
    print(f"applications: {len(applications)} -> {status_counts}")
    print(f"offers: {len(offers)}")
    print(f"loans funded: {len(loans)}")
    print(f"total origination fee revenue: ${sum(l['origination_fee_amount'] for l in loans):,.2f}")
    print("Wrote borrowers.csv, lenders.csv, loan_applications.csv, loan_offers.csv, loans.csv")


if __name__ == "__main__":
    main()