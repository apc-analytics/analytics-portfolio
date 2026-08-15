with

    subscriptions as (
        select * from {{ ref('stg_apc_wellness__subscriptions') }}
    )

    , orders as (
        select * from {{ ref('stg_apc_wellness__orders') }}
        where status = 'completed'
    )

    , months as (
        select generate_series(
            date_trunc('month', (select min(start_date) from subscriptions))
            , date_trunc('month', current_date)
            , interval '1 month'
        )::date as month_start
    )

    , mrr_by_month as (
        select
            m.month_start
            , sum(s.billed_amount) as mrr
            , count(distinct s.subscription_id) as active_subscriptions
        from months m
        left join subscriptions s
            on s.start_date <= (m.month_start + interval '1 month' - interval '1 day')::date
            and (s.end_date is null or s.end_date >= m.month_start)
        group by m.month_start
    )

    , one_time_by_month as (
        select
            date_trunc('month', order_date)::date as month_start
            , sum(amount) as one_time_revenue
            , count(*) as completed_orders
        from orders
        group by 1
    )

select
    m.month_start
    , coalesce(mrr.mrr, 0) as mrr
    , coalesce(mrr.active_subscriptions, 0) as active_subscriptions
    , coalesce(ot.one_time_revenue, 0) as one_time_revenue
    , coalesce(ot.completed_orders, 0) as completed_orders
    , coalesce(mrr.mrr, 0) + coalesce(ot.one_time_revenue, 0) as total_revenue
from months m
    left join mrr_by_month mrr on mrr.month_start = m.month_start
    left join one_time_by_month ot on ot.month_start = m.month_start
order by m.month_start