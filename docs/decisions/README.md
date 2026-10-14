# Decisions

One file per decision that would be expensive to rediscover, numbered in the
order they were made.

## What belongs here

A decision belongs here when a reasonable person looking at the code later would
ask "why is it done this way?" and the answer is not visible from the code itself.
Usually that means one of three shapes:

- **A measurement changed the design.** The data disagreed with the obvious
  approach, and the obvious approach is still the obvious one.
- **A trade-off was taken.** Something was given up on purpose.
- **A bug is now guarded.** Something broke once, and the guard looks
  unnecessary to anyone who did not see it break.

Bug fixes do not belong here — the commit message and the test cover those. What
belongs here is the reasoning that a test cannot express.

## The rule

**A record is never edited to reflect a new decision.** It is superseded: a new
record is added, and the old one gains a line at the top saying what replaced it.
A decision log that gets rewritten is a decision log that cannot be trusted about
anything older than the last change.

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-raw-columns-stay-text.md) | Raw columns stay TEXT; casting happens once, in staging | Accepted |
| [0002](0002-aggregate-to-the-order-grain.md) | Fact tables aggregate to the order grain before joining | Accepted |
| [0003](0003-lateness-in-whole-days.md) | Lateness is measured in whole days | Accepted |
| [0004](0004-the-customer-is-customer-unique-id.md) | The customer is `customer_unique_id`, not `customer_id` | Accepted |
| [0005](0005-postgres-on-host-port-5433.md) | PostgreSQL runs on host port 5433 | Accepted |
| [0006](0006-a-lane-is-a-pair-of-states.md) | Lateness is measured per seller-state to customer-state lane | Accepted |

## Format

Each record has a status, a date, and three sections: what the situation was, what
was decided, and what it costs. The consequences section is the point — a decision
with no downsides has not been thought about.
