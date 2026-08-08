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

    , order_categories as (
        select
            order_type
            , case
                when order_type = 'fitness_assessment' then 1
                when order_type = 'coaching_session' then 1
                when order_type = 'challenge_entry_fee' then 1
                when order_type = 'challenge_entry_fee' then 0
                else 0
                end as is_one_time_order
            , count(*)
            , sum(amount) as total_amount
        from
            db_portfolio.stg_apc_wellness.stg_apc_wellness__orders
        group by 1
    )

select
    a.account_type
    , p.tier
    , count(distinct m.member_id) as count_members
    , sum(s.billed_amount) as total_billed_amount
    , round((sum(s.billed_amount) / 12), 2) as monthly_billed_amount
    , round((sum(s.billed_amount) / count(distinct m.member_id)), 2) as rev_per_member

    , count(case when mrs.is_current = 1 then m.member_id end) as count_mem_with_current_streak
    , max(case when mrs.is_current = 1 then mrs.streak_length_days end) as max_current_streak_length
    , max(mls.longest_streak) as longest_streak_days

    , count(case
                when o.order_type IN('fitness_assessment', 'coaching_session', 'challenge_entry_fee')
                    then o.order_id end) as count_one_time_orders
from
    db_portfolio.stg_apc_wellness.stg_apc_wellness__members as m
        left join db_portfolio.stg_apc_wellness.stg_apc_wellness__accounts as a
            on m.account_id = a.account_id
        join db_portfolio.stg_apc_wellness.stg_apc_wellness__subscriptions as s
            on m.member_id = s.member_id
        join db_portfolio.stg_apc_wellness.stg_apc_wellness__plans as p
            on s.plan_id = p.plan_id
        left join db_portfolio.stg_apc_wellness.stg_apc_wellness__orders as o
            on m.member_id = o.member_id
        left join most_recent_streaks as mrs
            on m.member_id = mrs.member_id
        left join member_longest_streaks as mls
            on m.member_id = mls.member_id
group by 1, 2;