# Documentation

The documentation here is part of the deliverable, not overhead. A number whose
definition is not written down is a number two people will compute two different
ways and both be confident about.

| Document | Answers the question |
|---|---|
| [Architecture](architecture.md) | How the pieces fit together, and why they are separated this way |
| [Metrics](metrics.md) | What every number in the report actually means — and what it does not mean |
| [Data dictionary](data-dictionary.md) | Every table and column, with its grain and its caveats |
| [Decisions](decisions/README.md) | Why the code looks the way it does — one record per decision |

## Where to start

- **Reviewing the analysis?** Read the [report](../site/reports/01-retail-analytics/01-business-analytics.qmd), then [Metrics](metrics.md) when a number needs pinning down.
- **Reviewing the engineering?** Read [Architecture](architecture.md), then [Decisions](decisions/README.md).
- **Trying to reproduce a figure?** [Running it](../README.md#running-it) has the commands; the [data dictionary](data-dictionary.md) says which table the figure came from.
- **Wondering why something is done a strange way?** It is probably in [Decisions](decisions/README.md), including the cases where the strange way is the right one.

## Conventions

- Documents here describe **what is true now**. When a decision changes, the record of the old one stays and a new one is added — history is not edited.
- Every claim about the data in these documents was measured against the database, not recalled. Where a number appears, the query that produced it is reproducible from the models.
- Limitations live next to the thing they limit, and are repeated in the project README. They are deliberately not tucked away in an appendix.
