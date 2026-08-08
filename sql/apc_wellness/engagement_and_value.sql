with

    as_of_date as (
        select max(activity_date) as as_of_date
    from
        db_portfolio.stg_apc_wellness.stg_apc_wellness__workouts
    )

    , member_longest_streaks as (
        select
            member_id
            , max(streak_length_days) as longest_streak
        from
            db_portfolio.int_apc_wellness.int_apc_wellness__member_streaks
        group by 1
    )

    , most_recent_streaks as (
        select
            ms.member_id
            , ms.streak_length_days
            , (ad.as_of_date - ms.streak_end_date) as days_since_streak_end
            , case when (ad.as_of_date - ms.streak_end_date) = 0 then 1 else 0 end as is_current
        from
            db_portfolio.int_apc_wellness.int_apc_wellness__member_streaks as ms
                cross join as_of_date as ad
        where
            streak_recency_rank = 1
    )

    , member_orders as (
        select
            member_id
            , count(*) as count_orders
            , sum(amount) as total_orders_amount
        from
            db_portfolio.stg_apc_wellness.stg_apc_wellness__orders
        group by 1
    )

select
    a.account_type
    , p.tier
    , count(distinct m.member_id) as count_members
    , sum(s.billed_amount) as total_billed_amount
    , round((sum(s.billed_amount) / count(distinct m.member_id)), 2) as rev_per_member

    , count(case when mrs.is_current = 1 then m.member_id end) as count_mem_with_current_streak
    , max(case when mrs.is_current = 1 then mrs.streak_length_days end) as max_current_streak_length
    , round(avg(mls.longest_streak), 1) as avg_longest_streak_days

    , sum(mo.count_orders) as count_orders -- these are one-time purchases instead of subscriptions
from
    db_portfolio.stg_apc_wellness.stg_apc_wellness__members as m
        left join db_portfolio.stg_apc_wellness.stg_apc_wellness__accounts as a
            on m.account_id = a.account_id
        join db_portfolio.stg_apc_wellness.stg_apc_wellness__subscriptions as s
            on m.member_id = s.member_id
        join db_portfolio.stg_apc_wellness.stg_apc_wellness__plans as p
            on s.plan_id = p.plan_id
        left join member_orders as mo
            on m.member_id = mo.member_id
        left join most_recent_streaks as mrs
            on m.member_id = mrs.member_id
        left join member_longest_streaks as mls
            on m.member_id = mls.member_id
group by 1, 2;