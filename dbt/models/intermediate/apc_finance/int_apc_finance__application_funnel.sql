with

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
from {{ ref('stg_apc_finance__loan_applications') }} as a
    left join {{ ref('stg_apc_finance__borrowers') }} as b
        on a.borrower_id = b.borrower_id
    left join offer_stats as os
        on a.application_id = os.application_id