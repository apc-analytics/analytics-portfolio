with

    as_of_date as (
        select max(created_at) as as_of_date
        from {{ ref('stg_apc_wellness__support_tickets') }}
    )

select
    count(st.ticket_id) as total_overall_tickets
    , round(avg(st.csat_rating), 1) as avg_overall_csat_rating
    , round(avg(st.resolved_at - st.created_at), 1) as overall_resolution_time_days
    , count(case when st.ticket_status = 'Open' then st.ticket_id end) as count_overall_open
    , round(avg(case when st.ticket_status = 'Open' then ad.as_of_date - st.created_at end), 1) as avg_overall_open_days
    , count(case when st.ticket_status = 'Pending Customer Response' then st.ticket_id end) as count_overall_pending
    , round(avg(case when st.ticket_status = 'Pending Customer Response' then ad.as_of_date - st.created_at end), 1) as avg_overall_pending_days
    , count(case when st.ticket_status = 'Closed' then st.ticket_id end) as count_overall_closed
from {{ ref('stg_apc_wellness__support_tickets') }} as st
    cross join as_of_date as ad