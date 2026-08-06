with source as (
    select * from {{ source('apc_wellness', 'orders') }}
),

renamed as (
    select
        order_id
        , member_id
        , order_type
        , order_date::date as order_date
        , amount::numeric(6,2) as amount
        , status
    from
        source
)

select * from renamed