"""
APC Wellness — account acquisition attribution generator.

Links a subset of accounts to the campaign that acquired them. Attribution
happens at the account level (not member level) — for individual accounts
this is equivalent anyway (1 account = 1 member), and for organizations,
an acquisition campaign (trade show, employer partnership) wins a
*contract*, not an individual employee.

Not every account gets attributed — real attribution tracking is always
incomplete (organic signups, referrals, word of mouth), so this generates
a realistic mix of tracked (~55%) and untracked accounts rather than
pretending 100% coverage.

An account is only eligible to be attributed to a campaign if:
- the campaign's target_audience matches the account's account_type
- the account's earliest member join_date falls within the campaign's
  run (or up to 45 days after it ends, allowing for a delayed signup)
Accounts with no eligible campaign are simply left unattributed.

Requires: accounts.csv, members.csv (from generate_accounts_members.py)
          campaigns.csv (from generate_campaigns.py)
Output: account_acquisition.csv, in the same folder as this script.

Usage:
    python generate_attribution.py
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT_DIR = Path(__file__).parent
PCT_ACCOUNTS_ATTRIBUTED = 0.55
DELAYED_CONVERSION_DAYS = 45


def load_csv(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def earliest_join_date_by_account(members: list) -> dict:
    result = {}
    for m in members:
        d = date.fromisoformat(m["join_date"])
        acct = m["account_id"]
        if acct not in result or d < result[acct]:
            result[acct] = d
    return result


def eligible_campaigns(campaigns: list, account_type: str, acquisition_date: date):
    eligible = []
    for c in campaigns:
        if c["target_audience"] != account_type:
            continue
        start = date.fromisoformat(c["start_date"])
        end = date.fromisoformat(c["end_date"])
        window_end = end + timedelta(days=DELAYED_CONVERSION_DAYS)
        if start <= acquisition_date <= window_end:
            eligible.append(c)
    return eligible


def main():
    accounts = load_csv(OUT_DIR / "accounts.csv")
    members = load_csv(OUT_DIR / "members.csv")
    campaigns = load_csv(OUT_DIR / "campaigns.csv")

    acquisition_dates = earliest_join_date_by_account(members)

    candidate_accounts = [a for a in accounts if a["account_id"] in acquisition_dates]
    target_count = int(len(candidate_accounts) * PCT_ACCOUNTS_ATTRIBUTED)
    shuffled = candidate_accounts[:]
    random.shuffle(shuffled)

    rows = []
    for account in shuffled:
        if len(rows) >= target_count:
            break
        acq_date = acquisition_dates[account["account_id"]]
        options = eligible_campaigns(campaigns, account["account_type"], acq_date)
        if not options:
            continue  # no eligible campaign for this account/date combo -> stays unattributed
        chosen = random.choice(options)
        rows.append({
            "account_id": account["account_id"],
            "campaign_id": chosen["campaign_id"],
        })

    with open(OUT_DIR / "account_acquisition.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["account_id", "campaign_id"])
        w.writeheader()
        w.writerows(rows)

    print(f"accounts attributed: {len(rows)} of {len(accounts)} ({len(rows) / len(accounts):.0%})")
    print("Wrote account_acquisition.csv")


if __name__ == "__main__":
    main()