select
    status
    , count(*) as count_applications
    , round(100.0 * count(*) / sum(count(*)) over (), 1) as pct_of_total
from {{ ref('int_apc_finance__application_funnel') }}
group by 1
order by 2 desc