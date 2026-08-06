with source as (
    select * from {{ source('apc_wellness', 'workouts') }}
),

renamed as (
    select
        workout_id
        , member_id
        , activity_date::date as activity_date
        , steps::int as steps
        , distance_km::numeric(6,2) as distance_km
        , very_active_minutes::int as very_active_minutes
        , moderately_active_minutes::int as moderately_active_minutes
        , light_active_minutes::int as light_active_minutes
        , sedentary_minutes::int as sedentary_minutes
        , calories_burned::int as calories_burned
        , source."source" as data_source
        /*
         the raw workouts table has a column literally named source (holding real_fitbit/synthetic),
         which collides with the CTE also named source.
         So that one line needs the explicit source."source" qualification
         to disambiguate the CTE from the column of the same name.
         */
        , case
            when very_active_minutes::int + moderately_active_minutes::int >= 15
            then true
            else false
        end as is_active_day
    from source
)

select * from renamed