with source as (
    select * from {{ source('apc_wellness', 'members') }}
),

renamed as (
    select
        member_id
        , account_id
        , email
        , join_date::date as join_date
        , eligibility_status
        -- Postgres accepts 'True'/'False' text directly in a ::boolean cast, so this works cleanly straight off the raw TEXT columns
        , sponsored::boolean as sponsored
        , is_fitbit_seed::boolean as is_fitbit_seed
    from source
)

select * from renamed