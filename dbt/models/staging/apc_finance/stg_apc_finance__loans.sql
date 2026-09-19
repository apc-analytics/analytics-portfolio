with source as (
    select * from {{ source('apc_finance', 'loans') }}
),

renamed as (
    select
        loan_id
        , offer_id
        , borrower_id
        , lender_id
        , funded_amount::numeric(10,2) as funded_amount
        , apr::numeric(6,4) as apr
        , term_months::int as term_months
        , funded_date::date as funded_date
        , origination_fee_pct::numeric(6,4) as origination_fee_pct
        , origination_fee_amount::numeric(10,2) as origination_fee_amount
    from source
)

select * from renamed