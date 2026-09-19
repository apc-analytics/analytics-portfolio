with source as (
    select * from {{ source('apc_finance', 'loan_offers') }}
),

renamed as (
    select
        offer_id
        , application_id
        , borrower_id
        , lender_id
        , offered_amount::numeric(10,2) as offered_amount
        , apr::numeric(6,4) as apr
        , term_months::int as term_months
        , offer_date::date as offer_date
        , status
    from source
)

select * from renamed