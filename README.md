# Kusto-Doctor

A package for validating KQL queries using Kustainer.

This project is inspired by timtim589's project [here](https://github.com/timtim589/KustainerValidation).

# Design

The dataflow:

::: mermaid
flowchart LR
direction TB

subgraph sources[sources.py]
  file[local file]
  inline[inline]
end
models[models.py]
ingestions[ingestions.py]
queries[queries.py]
checks[checks.py]

sample[sample data]
query[KQL queries]

sample --> file & inline -- load sample --> ingestions

query --> file & inline -- load queries --> queries

queries & ingestions --> checks -- check through queries --> result
:::

# Todo

- [x] Create ingestions.py for ingesting data.
- [x] Create sources.py for default data sources.
- [x] Create utils.py for initialization and pretty print.
- [x] Create queries.py for loading queries.
- [x] Create checks.py that uses queries.py for batch checking.
- [ ] Create decorators for table preparation like resetting data.

