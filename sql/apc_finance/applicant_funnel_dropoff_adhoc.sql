-- 1. Overall funnel
-- Of all applications, what share end up funded vs. get zero offers vs. get offers but the borrower walks away?

-- 2. Credit tier's role
-- How much of the drop-off is explained by credit tier alone?
-- I'd expect Poor-credit applicants to get fewer offers, but I want the actual numbers, not an assumption.

-- 3. The "walked away" segment specifically
-- For applicants who got offers but didn't accept any, is there a pattern?
-- Fewer offers, worse average APR, something else?

-- 4. Purpose
-- Does loan purpose (debt consolidation vs. medical vs. home improvement, etc.) correlate with funding rate at all,
-- or is it purely a credit-

with

    offer_stats as (
        select
            application_id
            , count(*) as count_offers
            , round(avg(apr), 4) as avg_apr_offered
            , round(min(apr), 4) as min_apr_offered
            , round(max(apr), 4) as max_apr_offered
        from
            db_portfolio.stg_apc_finance.stg_apc_finance__loan_offers
        group by 1
    )

select
    a.application_id
    , b.credit_tier
    , a.loan_purpose
    , a.requested_amount
    , a.application_date
    , a.status
    , coalesce(os.count_offers, 0) as count_offers
    , os.avg_apr_offered
    , os.min_apr_offered
    , os.max_apr_offered
from
    db_portfolio.stg_apc_finance.stg_apc_finance__loan_applications as a
        left join db_portfolio.stg_apc_finance.stg_apc_finance__borrowers as b
            on a.borrower_id = b.borrower_id
        left join offer_stats as os
            on a.application_id = os.application_id;