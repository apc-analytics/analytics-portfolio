/*
This model uses a useful SQL pattern worth knowing for interviews called the "islands and gaps" technique.
- For each member's active days, subtract each day's row number (ordered by date) from its actual calendar date.
- Consecutive active days all land on the exact same resulting value, since the date and the row number both increase by one each day,
    so that shared value becomes a natural grouping key for each unbroken streak, without needing any recursive logic.
 */

with workouts as (
    select * from {{ ref('stg_apc_wellness__workouts') }}
)

, islands as (
    select
        *
        , activity_date - (
            row_number() over (
                partition by member_id, is_active_day
                order by activity_date
            )
        ) * interval '1 day' as streak_group
    from
        workouts
)

, streaks as (
    select
        member_id
        , streak_group
        , min(activity_date) as streak_start_date
        , max(activity_date) as streak_end_date
        , count(*) as streak_length_days
    from
        islands
    where
        is_active_day = true
    group by
        member_id
        , streak_group
)

select
    member_id
    , streak_start_date
    , streak_end_date
    , streak_length_days
    , row_number() over (partition by member_id order by streak_end_date desc) as streak_recency_rank
from
    streaks

/* OUTPUT NOTES:
    Each row is one continuous active streak for a member (start date, end date, length in days).
    streak_recency_rank = 1 marks each member's most recent streak.
    Combined with checking whether streak_end_date is their most recent workout date, that tells you their current streak versus a past one that's since broken.
    The longest-ever streak is just max(streak_length_days) per member across all their rows here.
 */