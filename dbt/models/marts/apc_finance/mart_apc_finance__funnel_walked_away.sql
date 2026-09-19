select
    status
    , count(*) as count_applications
    , round(avg(count_offers), 1) as avg_count_offers
    , round(avg(avg_apr_offered), 4) as avg_of_avg_apr
    , round(avg(min_apr_offered), 4) as avg_of_best_apr
from {{ ref('int_apc_finance__application_funnel') }}
where status in ('funded', 'offers_declined')
group by 1