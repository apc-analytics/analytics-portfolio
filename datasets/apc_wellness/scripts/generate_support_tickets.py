"""
APC Wellness — support tickets generator.

Samples down from Kaggle's "Customer Support Ticket Dataset" (CC0,
suraj520/customer-support-ticket-dataset, 8,469 rows) rather than
augmenting like generate_workouts.py did — we need far fewer tickets
than the source has, so this pulls a random subset without replacement.

Only categorical fields are kept from the source (Ticket Type, Status,
Priority, Channel, Satisfaction Rating) — preserving whatever real
correlations exist between them. Everything about the fictional
company's context (which member, when) is generated fresh:

- The source has no actual ticket-creation-date column, and its "First
  Response Time" / "Time to Resolution" fields are known to be
  inconsistently populated / sometimes store absolute timestamps
  despite their names — none of that fits our fictional timeline, so
  we don't try to reuse it.
- created_at is generated between the member's join_date and today.
- resolved_at is only generated when the sampled row's Ticket Status
  looks resolved/closed, offset from created_at by a priority-based
  resolution time (critical/high resolve faster than low).
- Ticket Type stays as the *source's* original category labels
  (Technical issue, Billing inquiry, etc.) — recontextualizing those
  into APC Wellness-appropriate categories happens in the dbt staging
  model, not here, so the raw table stays a faithful copy of what we
  actually loaded.

Run this after generate_accounts_members.py (it reads members.csv).
Output: support_tickets.csv, in the same folder as this script.

Usage:
    python generate_support_tickets.py --tickets-csv "path/to/customer_support_tickets.csv"
"""

import argparse
import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT_DIR = Path(__file__).parent
PCT_MEMBERS_WITH_TICKETS = 0.20
NUM_TICKETS_WEIGHTS = {1: 0.60, 2: 0.25, 3: 0.10, 4: 0.05}

# priority (lowercased, substring match) -> (min_days, max_days) to resolve
RESOLUTION_DAYS_BY_PRIORITY = {
    "critical": (0, 1),
    "high": (1, 3),
    "medium": (2, 5),
    "low": (3, 10),
}
DEFAULT_RESOLUTION_DAYS = (2, 6)  # fallback if priority value is unrecognized

RESOLVED_STATUS_KEYWORDS = ("closed", "resolved")


def new_id() -> str:
    return f"tkt_{uuid.uuid4().hex[:12]}"


def load_real_tickets(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({
                "ticket_type": row["Ticket Type"],
                "ticket_status": row["Ticket Status"],
                "ticket_priority": row["Ticket Priority"],
                "ticket_channel": row["Ticket Channel"],
                "csat_rating": row["Customer Satisfaction Rating"].strip(),
            })
    return rows


def resolution_window(priority: str):
    p = (priority or "").lower()
    for key, window in RESOLUTION_DAYS_BY_PRIORITY.items():
        if key in p:
            return window
    return DEFAULT_RESOLUTION_DAYS


def build_ticket(member_id: str, join_date: date, today: date, sampled: dict) -> dict:
    span_days = max((today - join_date).days, 0)
    created_at = join_date + timedelta(days=random.randint(0, span_days)) if span_days else join_date

    is_resolved = any(kw in sampled["ticket_status"].lower() for kw in RESOLVED_STATUS_KEYWORDS)
    resolved_at = ""
    if is_resolved:
        min_d, max_d = resolution_window(sampled["ticket_priority"])
        resolved_at_date = created_at + timedelta(days=random.randint(min_d, max_d))
        if resolved_at_date > today:
            resolved_at_date = today
        resolved_at = resolved_at_date.isoformat()

    return {
        "ticket_id": new_id(),
        "member_id": member_id,
        "ticket_type": sampled["ticket_type"],
        "ticket_status": sampled["ticket_status"],
        "ticket_priority": sampled["ticket_priority"],
        "ticket_channel": sampled["ticket_channel"],
        "csat_rating": sampled["csat_rating"],
        "created_at": created_at.isoformat(),
        "resolved_at": resolved_at,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickets-csv", required=True, help="Path to the Kaggle customer support tickets CSV")
    parser.add_argument("--members-csv", default=str(OUT_DIR / "members.csv"))
    args = parser.parse_args()

    with open(args.members_csv, newline="", encoding="utf-8") as f:
        members = list(csv.DictReader(f))

    real_tickets = load_real_tickets(Path(args.tickets_csv))

    today = date.today()
    ticketing_members = random.sample(members, int(len(members) * PCT_MEMBERS_WITH_TICKETS))

    # decide total ticket count needed, then sample that many real rows without replacement
    counts = random.choices(
        list(NUM_TICKETS_WEIGHTS.keys()),
        weights=list(NUM_TICKETS_WEIGHTS.values()),
        k=len(ticketing_members),
    )
    total_needed = sum(counts)
    if total_needed > len(real_tickets):
        raise SystemExit(
            f"Need {total_needed} real ticket rows but source only has {len(real_tickets)}. "
            "Lower PCT_MEMBERS_WITH_TICKETS or NUM_TICKETS_WEIGHTS."
        )
    sampled_pool = random.sample(real_tickets, total_needed)

    tickets = []
    pool_idx = 0
    for member, n in zip(ticketing_members, counts):
        join_date = date.fromisoformat(member["join_date"])
        for _ in range(n):
            sampled = sampled_pool[pool_idx]
            pool_idx += 1
            tickets.append(build_ticket(member["member_id"], join_date, today, sampled))

    fieldnames = ["ticket_id", "member_id", "ticket_type", "ticket_status", "ticket_priority",
                  "ticket_channel", "csat_rating", "created_at", "resolved_at"]
    with open(OUT_DIR / "support_tickets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(tickets)

    resolved_count = sum(1 for t in tickets if t["resolved_at"])
    print(f"members with tickets: {len(ticketing_members)} of {len(members)} ({PCT_MEMBERS_WITH_TICKETS:.0%})")
    print(f"total tickets: {len(tickets)} ({resolved_count} resolved, {len(tickets) - resolved_count} open/pending)")
    print("Wrote support_tickets.csv")


if __name__ == "__main__":
    main()