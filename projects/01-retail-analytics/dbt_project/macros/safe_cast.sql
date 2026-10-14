-- Safe casts for columns that arrive as TEXT.
--
-- The loader writes every raw column as TEXT and keeps empty cells as empty
-- strings rather than NULLs, so the raw table is a faithful copy of the CSV.
-- That means a plain `cast(col as timestamp)` explodes on a real file:
--
--     invalid input syntax for type timestamp: ""
--
-- Converting `''` to NULL is the correct fix, and doing it in one macro keeps
-- the rule in a single readable place instead of repeated in every model.

{% macro safe_timestamp(column) %}
    cast(nullif(trim({{ column }}), '') as timestamp)
{% endmacro %}


{% macro safe_integer(column) %}
    cast(nullif(trim({{ column }}), '') as integer)
{% endmacro %}


{% macro safe_numeric(column, precision=12, scale=2) %}
    cast(nullif(trim({{ column }}), '') as numeric({{ precision }}, {{ scale }}))
{% endmacro %}
