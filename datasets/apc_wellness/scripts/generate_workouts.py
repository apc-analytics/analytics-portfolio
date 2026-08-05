"""
APC Wellness — workouts generator (real FitBit data + synthetic augmentation).

Reads Kaggle's "FitBit Fitness Tracker Data" daily activity file
(dailyActivity_merged.csv from https://www.kaggle.com/datasets/arashnic/fitbit)
and:

1. Maps its ~30 distinct real users onto the 30 members flagged
   `is_fitbit_seed=True` in members.csv (from generate_accounts_members.py).
2. Shifts all dates onto a recent rolling window ending today, preserving
   each user's day-to-day sequence, so the data reads as "current" rather
   than frozen in 2016.
3. Generates statistically-similar synthetic daily activity for the
   remaining ~470 members, by bootstrap-sampling real days and jittering
   them — not fitting a parametric distribution, since real fitness data
   is skewed and a bootstrap preserves that shape without extra modeling.
4. Every member gets one row per day for each day in
   [max(join_date, window_start), today] — a single shared "current
   engagement" window, not lifetime history back to each join date.
   Members who joined partway through the window just start partway
   through the window's records.

Note: the source data is a passive daily activity summary (steps,
distance, active minutes, calories) — it has no discrete "workout type"
or "session" concept, so this script does not invent one. If a
`programs` / `program_enrollments` domain is added later, workout_type-
style detail would need to come from there, or from a different source.

Usage (pass one file, or both monthly export files to combine them):
    python generate_workouts.py --fitbit-csv "path/to/dailyActivity_merged.csv"
    python generate_workouts.py --fitbit-csv "path/to/month1/dailyActivity_merged.csv" "path/to/month2/dailyActivity_merged.csv"

Requires: members.csv already generated (run generate_accounts_members.py first)
Output: workouts.csv, in the same folder as this script
"""

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
random.seed(SEED)

OUT_DIR = Path(__file__).parent
WINDOW_DAYS = 60  # length of the shared "current engagement" window
JITTER_PCT = 0.15  # +/- jitter applied to bootstrapped synthetic values


def load_members(path: Path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load_real_activity(paths: list):
    """Load one or more real FitBit dailyActivity_merged.csv files (e.g. the
    two monthly export folders), keyed by real Id. Rows from all files for
    the same Id are pooled together before sorting by date, so passing both
    the retrospective and prospective months' files gives each real user up
    to ~62 days of history instead of ~31."""
    by_user = {}
    for path in paths:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                real_id = row["Id"]
                by_user.setdefault(real_id, []).append({
                    "date": row["ActivityDate"],
                    "steps": int(float(row["TotalSteps"])),
                    "distance_km": round(float(row["TotalDistance"]) * 1.60934, 2),
                    "very_active_minutes": int(float(row["VeryActiveMinutes"])),
                    "moderately_active_minutes": int(float(row["FairlyActiveMinutes"])),
                    "light_active_minutes": int(float(row["LightlyActiveMinutes"])),
                    "sedentary_minutes": int(float(row["SedentaryMinutes"])),
                    "calories_burned": int(float(row["Calories"])),
                })
    return by_user


def shift_dates_to_window(records: list, window_end: date) -> list:
    """Re-anchor a user's real day sequence onto the shared window, ending
    at window_end, preserving relative day-to-day order."""
    records = sorted(records, key=lambda r: r["date"])
    n = len(records)
    start = window_end - timedelta(days=n - 1)
    shifted = []
    for i, r in enumerate(records):
        new_row = dict(r)
        new_row["date"] = (start + timedelta(days=i)).isoformat()
        shifted.append(new_row)
    return shifted


def bootstrap_synthetic_day(pool: list) -> dict:
    """Sample a real day at random and jitter its values, clipping at 0."""
    base = random.choice(pool)
    out = {}
    for key in ("steps", "distance_km", "very_active_minutes",
                "moderately_active_minutes", "light_active_minutes",
                "sedentary_minutes", "calories_burned"):
        jitter = 1 + random.uniform(-JITTER_PCT, JITTER_PCT)
        val = base[key] * jitter
        out[key] = round(val, 2) if isinstance(base[key], float) else max(0, round(val))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fitbit-csv", required=True, nargs="+",
                         help="Path(s) to dailyActivity_merged.csv — pass both monthly export files to combine them")
    parser.add_argument("--members-csv", default=str(OUT_DIR / "members.csv"))
    args = parser.parse_args()

    members = load_members(Path(args.members_csv))
    real_activity = load_real_activity([Path(p) for p in args.fitbit_csv])
    real_user_ids = list(real_activity.keys())

    fitbit_seed_members = [m for m in members if m["is_fitbit_seed"] == "True"]
    other_members = [m for m in members if m["is_fitbit_seed"] != "True"]

    if len(real_user_ids) < len(fitbit_seed_members):
        raise SystemExit(
            f"Real FitBit file has {len(real_user_ids)} distinct users, "
            f"but {len(fitbit_seed_members)} members are flagged as seeds. "
            "Check the file or adjust FITBIT_SEED_COUNT in generate_accounts_members.py."
        )

    window_end = date.today()
    workout_rows = []
    workout_counter = 0

    # Real users -> the 30 seed members, dates shifted onto the shared window
    real_id_pool = random.sample(real_user_ids, len(fitbit_seed_members))
    all_real_pool = [row for rows in real_activity.values() for row in rows]  # for bootstrapping too

    for member, real_id in zip(fitbit_seed_members, real_id_pool):
        shifted = shift_dates_to_window(real_activity[real_id], window_end)
        join_date = date.fromisoformat(member["join_date"])
        for r in shifted:
            if date.fromisoformat(r["date"]) < join_date:
                continue
            workout_counter += 1
            workout_rows.append({
                "workout_id": f"wkt_{workout_counter:07d}",
                "member_id": member["member_id"],
                "activity_date": r["date"],
                "steps": r["steps"],
                "distance_km": r["distance_km"],
                "very_active_minutes": r["very_active_minutes"],
                "moderately_active_minutes": r["moderately_active_minutes"],
                "light_active_minutes": r["light_active_minutes"],
                "sedentary_minutes": r["sedentary_minutes"],
                "calories_burned": r["calories_burned"],
                "source": "real_fitbit",
            })

    # Synthetic members -> bootstrapped + jittered days across the same window
    window_start = window_end - timedelta(days=WINDOW_DAYS - 1)
    for member in other_members:
        join_date = date.fromisoformat(member["join_date"])
        member_start = max(join_date, window_start)
        d = member_start
        while d <= window_end:
            day = bootstrap_synthetic_day(all_real_pool)
            workout_counter += 1
            workout_rows.append({
                "workout_id": f"wkt_{workout_counter:07d}",
                "member_id": member["member_id"],
                "activity_date": d.isoformat(),
                **day,
                "source": "synthetic",
            })
            d += timedelta(days=1)

    fieldnames = ["workout_id", "member_id", "activity_date", "steps", "distance_km",
                  "very_active_minutes", "moderately_active_minutes", "light_active_minutes",
                  "sedentary_minutes", "calories_burned", "source"]
    with open(OUT_DIR / "workouts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(workout_rows)

    real_rows = sum(1 for r in workout_rows if r["source"] == "real_fitbit")
    synth_rows = len(workout_rows) - real_rows
    print(f"Real FitBit users found in source file: {len(real_user_ids)}")
    print(f"Workout rows written: {len(workout_rows)} ({real_rows} real, {synth_rows} synthetic)")
    print("Wrote workouts.csv")


if __name__ == "__main__":
    main()