with source as (
    select * from {{ source('apc_finance', 'lenders') }}
),

renamed as (
    select
        lender_id
        , lender_name
        , min_credit_tier
        , apr_min::numeric(6,4) as apr_min
        , apr_max::numeric(6,4) as apr_max
        , origination_fee_pct::numeric(6,4) as origination_fee_pct
        , status
    from source
)

select * from renamed