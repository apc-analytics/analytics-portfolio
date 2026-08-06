with source as (
    select * from {{ source('apc_wellness', 'support_tickets') }}
),

renamed as (
    select
        ticket_id
        , member_id
        , case lower(ticket_type)
            when 'technical issue' then 'App/device sync issue'
            when 'billing inquiry' then 'Billing & subscription question'
            when 'product inquiry' then 'Program/feature question'
            when 'cancellation request' then 'Cancellation request'
            when 'refund request' then 'Refund request'
            else ticket_type
        end as ticket_category
        , ticket_status
        , ticket_priority
        , ticket_channel
        , nullif(csat_rating, '')::int as csat_rating
        , created_at::date as created_at
        , nullif(resolved_at, '')::date as resolved_at
    from
        source
)

select * from renamed