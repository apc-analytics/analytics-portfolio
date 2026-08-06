with source as (
    select * from {{ source('apc_wellness', 'plans') }}
),

renamed as (
    select
        plan_id
        , plan_name
        , tier
        , monthly_price::numeric(6,2) as monthly_price
    from source
)

select * from renamed