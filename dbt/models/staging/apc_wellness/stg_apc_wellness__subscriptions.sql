with source as (
    select * from {{ source('apc_wellness', 'subscriptions') }}
),

renamed as (
    select
        subscription_id
        , member_id
        , plan_id
        , start_date::date as start_date
        , nullif(end_date, '')::date as end_date
        , status
        , billed_amount::numeric(6,2) as billed_amount
        -- Same nullif treatment for end_date, since active subscriptions were written with a blank end date, not a real value
    from source
)

select * from renamed