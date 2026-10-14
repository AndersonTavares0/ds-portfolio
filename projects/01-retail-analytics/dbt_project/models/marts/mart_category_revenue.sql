-- Revenue by product category, in English.
--
-- Built from items, never from orders. A single order routinely spans several
-- categories, so attributing an order total to each of its categories would
-- count the same money more than once and the categories would not add up to
-- revenue.
--
-- `revenue_brl` is item price only. Freight is not attributable to a category in
-- this dataset — one shipment can carry items from several categories and the
-- freight is charged once for the whole order — so it is excluded rather than
-- spread with an invented rule.

select
    category_name_english                   as category,
    count(distinct order_id)                as orders,
    count(*)                                as items,
    count(distinct product_id)              as products,
    round(sum(price), 2)                    as revenue_brl,
    round(avg(price), 2)                    as avg_item_price_brl

from {{ ref('fct_order_items') }}
group by category_name_english
