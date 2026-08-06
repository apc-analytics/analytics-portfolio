with source as (
    select * from {{ source('apc_wellness', 'campaigns') }}
),

renamed as (
    select
        campaign_id
        , campaign_name
        , channel
        , target_audience
        , start_date::date as start_date
        , end_date::date as end_date
        , status
        , budget::numeric(10,2) as budget
        , spend::numeric(10,2) as spend
        , impressions::int as impressions
        , clicks::int as clicks
        , conversions::int as conversions
    from
        source
)

select * from renamed