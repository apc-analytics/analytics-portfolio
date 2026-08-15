with

    as_of_date as (
        select max(created_at) as as_of_date
        from {{ ref('stg_apc_wellness__support_tickets') }}
    )

    , overall as (
        select * from {{ ref('mart_apc_wellness__tickets_overall') }}
    )

select
    st.ticket_priority
    , o.avg_overall_csat_rating
    , count(st.ticket_id) as total_tickets
    , round(avg(st.csat_rating), 1) as avg_csat_rating
    , round(avg(st.resolved_at - st.created_at), 1) as resolution_time_days
    , count(case when st.ticket_status = 'Open' then st.ticket_id end) as count_open
    , round(avg(case when st.ticket_status = 'Open' then ad.as_of_date - st.created_at end), 1) as avg_open_days
    , count(case when st.ticket_status = 'Pending Customer Response' then st.ticket_id end) as count_pending
    , round(avg(case when st.ticket_status = 'Pending Customer Response' then ad.as_of_date - st.created_at end), 1) as avg_pending_days
    , count(case when st.ticket_status = 'Closed' then st.ticket_id end) as count_closed
from {{ ref('stg_apc_wellness__support_tickets') }} as st
    cross join overall as o
    cross join as_of_date as ad
group by 1, 2
order by 2 desc