with

    subscriptions as (
        select * from {{ ref('stg_apc_wellness__subscriptions') }}
        where status = 'active'
    )

    , members as (
        select * from {{ ref('stg_apc_wellness__members') }}
    )

    , accounts as (
        select * from {{ ref('stg_apc_wellness__accounts') }}
    )

    , plans as (
        select * from {{ ref('stg_apc_wellness__plans') }}
    )

    , joined as (
        select
            a.account_type
            , p.plan_name
            , s.subscription_id
            , s.billed_amount
        from subscriptions s
            inner join members m on m.member_id = s.member_id
            inner join accounts a on a.account_id = m.account_id
            inner join plans p on p.plan_id = s.plan_id
    )

select
    account_type
    , plan_name
    , count(distinct subscription_id) as active_subscriptions
    , sum(billed_amount) as mrr
from joined
group by account_type, plan_name
order by account_type, plan_name