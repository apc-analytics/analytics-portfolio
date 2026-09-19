select
    loan_purpose
    , status
    , count(*) as count_applications
    , round(100.0 * count(*) / sum(count(*)) over (partition by loan_purpose), 1) as pct_within_purpose
from {{ ref('int_apc_finance__application_funnel') }}
group by 1, 2
order by 1, 3 desc