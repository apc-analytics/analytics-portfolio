with subscriptions as (
    select * from {{ ref('stg_apc_wellness__subscriptions') }}
    where status = 'active'
),

members as (
    select * from {{ ref('stg_apc_wellness__members') }}
),

attribution as (
    select * from {{ ref('stg_apc_wellness__account_acquisition') }}
),

campaigns as (
    select * from {{ ref('stg_apc_wellness__campaigns') }}
),

attributed_mrr as (
    select
        attribution.campaign_id
        , sum(subscriptions.billed_amount) as attributed_mrr
        , count(distinct subscriptions.subscription_id) as attributed_subscriptions
    from
        subscriptions
            inner join members
                on members.member_id = subscriptions.member_id
            inner join attribution
                on attribution.account_id = members.account_id
    group by
        attribution.campaign_id
)

select
    campaigns.campaign_id
    , campaigns.campaign_name
    , campaigns.channel
    , campaigns.target_audience
    , campaigns.spend
    , campaigns.conversions
    , coalesce(attributed_mrr.attributed_mrr, 0) as attributed_mrr
    , coalesce(attributed_mrr.attributed_subscriptions, 0) as attributed_subscriptions
    , case
        when coalesce(attributed_mrr.attributed_subscriptions, 0) > 0
        then round(campaigns.spend / attributed_mrr.attributed_subscriptions, 2)
    end as spend_per_attributed_subscription
    , case
        when coalesce(attributed_mrr.attributed_mrr, 0) > 0
        then round(campaigns.spend / attributed_mrr.attributed_mrr, 2)
    end as payback_period_months
from
    campaigns
        left join attributed_mrr
            on attributed_mrr.campaign_id = campaigns.campaign_id
order by
    attributed_mrr desc nulls last

/*
spend_per_attributed_subscription is a rough CAC (customer acquisition cost) — total campaign spend divided by how many still-active subscriptions trace back to it.
payback_period_months divides spend by monthly recurring revenue, which gives "how many months of MRR it takes to recover this campaign's cost"
Both are NULL rather than 0 or an error when a campaign has zero attributed subscriptions, since "cost per subscription" is undefined, not zero, when there are no subscriptions to divide by.
 */