with source as (
    select * from {{ source('apc_wellness', 'accounts') }}
),

renamed as (
    select
        account_id
        , account_type
        , account_name
        , industry
        , status
        , nullif(per_member_rate, '')::numeric(6,2) as per_member_rate
        -- handles individual accounts, where per_member_rate is genuinely blank (not applicable) rather than a real zero; casting an empty string straight to numeric would just error
    from source
)

select * from renamed