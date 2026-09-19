with source as (
    select * from {{ source('apc_finance', 'borrowers') }}
),

renamed as (
    select
        borrower_id
        , email
        , join_date::date as join_date
        , credit_tier
    from source
)

select * from renamed