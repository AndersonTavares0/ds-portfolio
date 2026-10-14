# 0001 — Raw columns stay TEXT; casting happens once, in staging

**Status:** Accepted
**Date:** 2026-10-14

## Situation

The nine source CSVs arrive as text. A pandas or SQL reader would happily infer
types on the way in, which is the default in almost every tutorial and looks like
the helpful thing to do.

It is not helpful, for two reasons that both showed up in practice:

- **Inference is lossy and silent.** The zip-code prefix `01001` is read as the
  integer `1001`. Nothing errors. Months later a geographic join returns nothing
  and the investigation starts from the wrong end.
- **Empty cells are empty strings, not NULL.** The loader reads with
  `keep_default_na=False`, so a blank timestamp is `''`. A bare
  `cast(col as timestamp)` then fails on real data with
  `invalid input syntax for type timestamp: ""` — which is exactly what happened
  the first time `dbt build` ran against the real 126 MB load.

## Decision

Every column in the `raw` schema is TEXT. Casting, renaming and normalising happen
in `analytics_staging`, once per column, in code that is reviewable and tested.

Casts go through three macros rather than being written inline:

```jinja
{% macro safe_timestamp(column) %} cast(nullif(trim({{ column }}), '') as timestamp) {% endmacro %}
{% macro safe_integer(column) %}   cast(nullif(trim({{ column }}), '') as integer) {% endmacro %}
{% macro safe_numeric(column, precision=12, scale=2) %} cast(nullif(trim({{ column }}), '') as numeric({{ precision }}, {{ scale }})) {% endmacro %}
```

## Consequences

- **Costs:** 126 MB is loaded and stored as text, so the `raw` schema is larger
  than it needs to be. There is one extra layer between the file and an answer,
  and a bad cast is now a thing that can be written rather than a thing the reader
  does for you.
- **Buys:** one place to look when a type is wrong, one place to test, and a
  guarantee that a zip-code prefix is never silently treated as a number. The
  `safe_*` macros made the empty-string failure impossible to reintroduce in a
  single model while leaving eight others broken — the fix was one file, not nine.
- **Note:** the raw column named `product_name_lenght` keeps its misspelling in
  the source declaration, so it stays visible what upstream actually sent. It is
  renamed to `name_length` in staging, where a reader expects readable names.
