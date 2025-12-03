# Kusto-Doctor

A package for validating KQL queries using Kustainer.

This project is inspired by timtim589's project [here](https://github.com/timtim589/KustainerValidation).

# Warning

**Early Development Stage**: This project is in its early development stage. Significant changes to the API, functionality, and project structure may occur without prior notice. Use at your own risk and expect potential breaking changes in future releases.

**Security Notice**: Due to the lack of existing libraries that support secure cluster management without management KQL commands, this library implements some functions using string concatenation to compose KQL queries, which could potentially lead to **KQL injection risks**. This tool is intended **exclusively for test environments** and should **never be used in production environments**. Always validate and sanitize any user inputs when using this library, and ensure proper access controls are in place in your test environment.

This project will explore alternative implementations that do not rely on string concatenation to compose KQL queries, aiming to provide safer methods for cluster management and query execution in future versions.


# Quick Start

## Installation

```bash
pip install kusto-doctor
```

## Prerequisites

Before using Kusto-Doctor, you need to have:
- A running Kusto cluster (e.g., [Kustainer](https://learn.microsoft.com/en-us/azure/data-explorer/kusto-emulator-overview) for local testing)
- Connection string configured in your environment (if Kustainer is used, the default one should work)

### Quick Setup with Docker

This repository includes a `docker-compose.yml` file that sets up Kustainer for local testing:

```bash
docker-compose up -d
```

This will start a Kustainer instance accessible at `http://localhost:8080`.

## Basic Usage

### 1. Create and Populate Tables

```python
from kusto_doctor.models import ColumnSchema, KustoDataType
from kusto_doctor.tables import create_table
from kusto_doctor.utils import buildKustoClient

with buildKustoClient() as client:
    schema = [
        ColumnSchema(ColumnName="Name", ColumnType=KustoDataType.string),
        ColumnSchema(ColumnName="Age", ColumnType=KustoDataType.int),
    ]
    create_table(
        client=client,
        database_name="TestDB",
        table_name="Users",
        schema=schema,
    )
```

### 2. Validate Queries from a Directory

```python
import logging
from datetime import datetime
from azure.kusto.data import ClientRequestProperties
from kusto_doctor.checks import check_directory_queries
from kusto_doctor.utils import buildKustoClient

logging.basicConfig(level=logging.INFO)

# Check all queries in a directory
with buildKustoClient() as client:
    properties = ClientRequestProperties()
    custom_datetime = datetime(2024, 10, 30, 0, 0, 0)
    properties.set_option("query_now", custom_datetime.isoformat())
    result = check_directory_queries(client, "path/to/queries", properties)
    logging.info(result)
```

### 3. Validate a List of Queries

```python
from kusto_doctor.checks import check_list_queries
from kusto_doctor.utils import buildKustoClient

with buildKustoClient() as client:
    test_queries = [
        ("valid query", "AuditLogs | take 10"),
        ("invalid query", "NonExistentTable | take 10"),
    ]
    result = check_list_queries(client, test_queries)
    print(result)
```

For more examples, check the [examples/](examples/) directory.


# Design

The dataflow:

```mermaid
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
```

# Todo

- [x] Create ingestions.py for ingesting data.
- [x] Create sources.py for default data sources.
- [x] Create utils.py for initialization and pretty print.
- [x] Create queries.py for loading queries.
- [x] Create checks.py that uses queries.py for batch checking.
- [ ] Create decorators for table preparation like resetting data.

