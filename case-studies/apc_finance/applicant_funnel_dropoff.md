# Where Do We Lose Applicants?

**Company:** APC Finance — a personal lending marketplace connecting borrowers to competing offers from multiple partner lenders
**Warehouse:** `db_portfolio` (`stg_apc_finance`, `int_apc_finance`, `mart_apc_finance` schemas)
**Stack:** PostgreSQL 18 · dbt Core

## The Ask

The Head of Growth wanted to understand exactly where applicants are lost
between submission and funding, and whether it's something the business
can actually influence:

1. Overall funnel - Of all applications, what share end up funded
   vs. get zero offers vs. get offers but the borrower walks away?
2. Credit tier's role - How much of the drop-off is explained by
   credit tier alone?
3. The "walked away" segment specifically - For applicants who got
   offers but didn't accept any, is there a pattern such as fewer offers,
   worse average APR, something else?
4. Purpose - Does loan purpose correlate with funding rate at all,
   or is it purely a credit-tier story?

## Building the Query

This started as an ad-hoc SQL exploration
([`sql/apc_finance/applicant_funnel_dropoff_adhoc.sql`](../../sql/apc_finance/applicant_funnel_dropoff_adhoc.sql)),
written and reviewed before being promoted into a permanent intermediate
model and four marts.

### Choosing the Grain

Three of the four questions (overall funnel, credit tier, purpose) are
answerable straight from `loan_applications` joined to `borrowers`,
which are both already at a safe 1:1 grain. Question 3 is the one that forces a
decision since it needs to know *how many* offers an application received and *what
those offers' APRs looked like*, and `loan_offers` is one-to-many with
`loan_applications`. A single application can have anywhere from zero
to several competing offers. Joining that directly into anything else
would silently duplicate every other number on the row, the same fan-out
risk guarded against throughout this whole warehouse.

The approach: pre-aggregate `loan_offers` down to one row per `application_id`
first (count, average, min, and max APR) before it touches anything
else:

```sql
offer_stats as (
    select
        application_id
        , count(*) as count_offers
        , round(avg(apr), 4) as avg_apr_offered
        , round(min(apr), 4) as min_apr_offered
        , round(max(apr), 4) as max_apr_offered
    from {{ ref('stg_apc_finance__loan_offers') }}
    group by 1
)
```

That settles the target grain for the reusable piece: **one row per
application**, matching `loan_applications`' own natural grain, carrying
the application's own attributes alongside the offer-aggregated numbers.
`count_offers` is coalesced to `0` for applications with no offers at
all, but the APR columns are deliberately left `NULL` in that case
rather than `0`, since "average APR of zero offers" is undefined, not
zero.

Once the base grain existed, the four parts of the brief turned out to
need four different `group by` clauses: overall share, share within
each credit tier, share within each purpose, and a direct two-group
comparison. Each one with a different percentage denominator. Getting the
denominator right matters here specifically because the credit-tier breakdown
needs percent-*within-that-tier*, and not percent-of-the-whole-population,
computed with a window function partitioned per tier:

```sql
select
    credit_tier
    , status
    , count(*) as count_applications
    , round(100.0 * count(*) / sum(count(*)) over (partition by credit_tier), 1) as pct_within_tier
from {{ ref('int_apc_finance__application_funnel') }}
group by 1, 2
```

Promoted into
[`int_apc_finance__application_funnel`](../../dbt/models/intermediate/apc_finance/int_apc_finance__application_funnel.sql)
(the reusable base) and four marts:
* [`funnel_overall`](../../dbt/models/marts/apc_finance/mart_apc_finance__funnel_overall.sql),
* [`funnel_by_credit_tier`](../../dbt/models/marts/apc_finance/mart_apc_finance__funnel_by_credit_tier.sql),
* [`funnel_by_purpose`](../../dbt/models/marts/apc_finance/mart_apc_finance__funnel_by_purpose.sql), and
* [`funnel_walked_away`](../../dbt/models/marts/apc_finance/mart_apc_finance__funnel_walked_away.sql)

This uses the same reasoning as the support ticket case study: four
different grains, each queryable directly rather than reconstructed by
hand from a single combined table. Fifty tests across the five models pass,
including `unique` on `int_apc_finance__application_funnel.application_id`
and `relationships` tests confirming every application traces back to a
real borrower.

## Results

### Overall Funnel

**70.9% of applications fund.** 27.8% receive offers but the borrower
declines all of them. Only 1.3% get zero offers at all — the honest
baseline every other number in this analysis sits against.

### Credit Tier

| Credit Tier | Funded | Offers Declined | No Offers |
|---|---|---|---|
| Excellent | 70.1% | 29.9% | 0% |
| Good | 70.1% | 29.9% | 0% |
| Fair | 73.9% | 25.6% | 0.5% |
| Poor | 66.5% | 26.2% | **7.3%** |

For the credit tier, the real signal is access, and not conversion.
The funded rate is nearly flat across every tier with a roughly 7-point spread that is not very dramatic.
What does move sharply is `no_offers`: 0% for Excellent and Good, and a clear jump to **7.3% for Poor**.
Poor-credit applicants aren't converting worse once they have real options in front
of them since they're far more likely to never see any options at all.
That is a sharper and more useful finding than the brief's own framing assumed, and
it's directly explainable from the warehouse's own lender data: only 2 of
the 10 partner lenders will even consider a Poor-tier applicant.

### Purpose

| Loan Purpose | Funded |
|---|---|
| Debt consolidation | 73.4% |
| Medical | 72.1% |
| Major purchase | 70.3% |
| Home improvement | 67.4% |
| Other | 68.2% |

A 67.4%–73.4% range is essentially noise, and not a real pattern. This is
expected given how the underlying data works: loan purpose only ever
determines the requested amount range in this warehouse, never lender
eligibility or acceptance likelihood, so there's no mechanism by which it
could drive funding rate. Directly answers question 4: it isn't "purpose
vs. credit tier" as competing explanations for drop-off. Credit tier's
real effect is specifically about access (whether any offers exist at
all), and purpose plays essentially no role in either access or
conversion.

### The Walked-Away Segment

The brief's third question regarding whether applicants who declined every offer
show a pattern (fewer offers, worse APR) is the one that this data
structurally cannot answer:

| | Funded | Offers Declined |
|---|---|---|
| Avg. offers received | 4.5 | 4.5 |
| Avg. APR across offers | 20.62% | 20.71% |
| Avg. best APR available | 14.73% | 14.72% |

Funded and declined applicants look statistically identical on every
dimension available. There is no difference at all, and this
isn't a null finding about borrower psychology.
Instead, it's a direct, consequence of how this warehouse's data was generated.
Whether a borrower accepted an offer was modeled as a flat probability,
applied the same way regardless of whether the available offers were
excellent or terrible, so there was never a real relationship between
offer quality and walk-away behavior for this analysis to find.
The conclusion here is "this warehouse cannot answer whether offer quality
predicts walk-away," not "offer quality doesn't predict walk-away."
These are different claims, and only the first one is actually supported
by anything here.

## Recommendation

1. Recruit more lenders willing to serve Poor-credit applicants.
   7.3% of Poor-tier applications get zero offers. This is the single clearest,
   most actionable number in this analysis, and it is directly due to
   having only 2 of 10 partner lenders in that segment. This is a lender
   supply problem, not a borrower behavior problem. Fortunately, it is fixable.
2. Don't organize growth efforts around loan purpose. It shows no
   meaningful relationship to funding outcomes. This is worth ruling out
   explicitly so no effort is spent chasing a lever that doesn't move
   anything.
3. The walked-away question needs real data instead of a data model fix.
   Understanding why committed applicants (i.e., people who already received
   competitive offers) decline anyway is an important question,
   but it requires something this warehouse doesn't have, which is an actual
   borrower-side signal (why they said no), likely through direct
   follow-up or survey data, and not something derivable from offer
   characteristics alone.