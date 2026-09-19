with source as (
    select * from {{ source('apc_finance', 'loan_applications') }}
),

renamed as (
    select
        application_id
        , borrower_id
        , loan_purpose
        , requested_amount::numeric(10,2) as requested_amount
        , application_date::date as application_date
        , status
    from source
)

select * from renamed