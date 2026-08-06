"""
APC Wellness — marketing campaigns generator.

Generates a one-row-per-campaign performance snapshot (spend, impressions,
clicks, conversions over each campaign's whole run) — not tied to
individual members, per the decision that this domain represents
campaign performance rather than attribution.

Campaigns split into two audiences with genuinely different cost/scale
profiles, matching the hybrid B2B2C model:
- individual: paid_social, search_ads, email, referral_program, content_seo
  (broad reach, lower cost, lower per-lead value)
- organization: sales_outreach, employer_partnership, trade_show, linkedin_ads
  (narrow reach, higher cost, higher per-lead value)

Fully synthetic — no public dataset fits fictional campaign performance,
so this has no "real data" counterpart to load, unlike workouts/tickets.

Usage:
    python generate_campaigns.py
"""

import csv
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT_DIR = Path(__file__).parent
NUM_CAMPAIGNS = 32
COMPANY_AGE_DAYS = 730  # matches the ~2 year join_date window used elsewhere

INDIVIDUAL_CHANNELS = ["paid_social", "search_ads", "email", "referral_program", "content_seo"]
ORG_CHANNELS = ["sales_outreach", "employer_partnership", "trade_show", "linkedin_ads"]

THEMES = ["New Year Reset", "Summer Movement", "Back to Routine", "Spring Momentum",
          "Q1 Push", "Q2 Growth", "Q3 Expansion", "Q4 Renewal", "Referral Boost",
          "Habit Streak", "Fresh Start", "Year-End Wellness"]


def new_id() -> str:
    return f"camp_{uuid.uuid4().hex[:12]}"


def random_date_range(today: date):
    start_offset = random.randint(0, COMPANY_AGE_DAYS - 14)
    start = today - timedelta(days=COMPANY_AGE_DAYS) + timedelta(days=start_offset)
    length = random.randint(14, 60)
    end = min(start + timedelta(days=length), today)
    return start, end


def build_individual_campaign(today: date) -> dict:
    channel = random.choice(INDIVIDUAL_CHANNELS)
    start, end = random_date_range(today)
    budget = round(random.uniform(500, 5000), 2)
    spend = round(budget * random.uniform(0.85, 1.05), 2)
    impressions = random.randint(10_000, 500_000)
    ctr = random.uniform(0.005, 0.03)
    clicks = round(impressions * ctr)
    conversion_rate = random.uniform(0.01, 0.08)
    conversions = round(clicks * conversion_rate)
    return _finalize(channel, "individual", start, end, budget, spend, impressions, clicks, conversions, today)


def build_org_campaign(today: date) -> dict:
    channel = random.choice(ORG_CHANNELS)
    start, end = random_date_range(today)
    budget = round(random.uniform(2000, 15000), 2)
    spend = round(budget * random.uniform(0.85, 1.05), 2)
    impressions = random.randint(500, 20_000)
    ctr = random.uniform(0.01, 0.05)
    clicks = round(impressions * ctr)
    conversion_rate = random.uniform(0.05, 0.20)  # smaller funnel, converts better per click
    conversions = round(clicks * conversion_rate)
    return _finalize(channel, "organization", start, end, budget, spend, impressions, clicks, conversions, today)


def _finalize(channel, audience, start, end, budget, spend, impressions, clicks, conversions, today):
    theme = random.choice(THEMES)
    status = "completed" if end < today else "active"
    return {
        "campaign_id": new_id(),
        "campaign_name": f"{theme} — {channel.replace('_', ' ').title()}",
        "channel": channel,
        "target_audience": audience,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "status": status,
        "budget": budget,
        "spend": spend,
        "impressions": impressions,
        "clicks": max(clicks, 0),
        "conversions": max(conversions, 0),
    }


def main():
    today = date.today()
    campaigns = []
    for _ in range(NUM_CAMPAIGNS):
        if random.random() < 0.65:  # skew toward individual campaigns (more frequent, lower cost)
            campaigns.append(build_individual_campaign(today))
        else:
            campaigns.append(build_org_campaign(today))

    fieldnames = ["campaign_id", "campaign_name", "channel", "target_audience", "start_date",
                  "end_date", "status", "budget", "spend", "impressions", "clicks", "conversions"]
    with open(OUT_DIR / "campaigns.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(campaigns)

    individual_count = sum(1 for c in campaigns if c["target_audience"] == "individual")
    print(f"campaigns: {len(campaigns)} ({individual_count} individual, {len(campaigns) - individual_count} organization)")
    print("Wrote campaigns.csv")


if __name__ == "__main__":
    main()