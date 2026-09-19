select
    credit_tier
    , status
    , count(*) as count_applications
    , round(100.0 * count(*) / sum(count(*)) over (partition by credit_tier), 1) as pct_within_tier
from {{ ref('int_apc_finance__application_funnel') }}
group by 1, 2
order by 1, 3 desc