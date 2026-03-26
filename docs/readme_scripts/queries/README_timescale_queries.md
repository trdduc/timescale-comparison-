# PostgreSQL / TimescaleDB Query Benchmark

A multi-threaded query benchmarking tool that measures cold and warm execution latency for a set of SQL queries against a PostgreSQL or TimescaleDB database. Results are saved to CSV for analysis or visualization.

## What it does

The script reads a `.sql` file where each line is one query, then executes every query **twice** — once for the cold run (no cached plan or data) and once for the warm run (OS page cache and DB plan cache are warm) — recording the latency of each. Results are written to a CSV file.

Two execution modes are available:

- **Parallel mode** (default): queries are distributed across multiple threads, each with its own database connection. Good for simulating concurrent load or speeding up large query sets.
- **Ordered mode** (`--ordered`): queries run sequentially on a single connection in the exact order they appear in the file, and each result is tagged with a `Q1`, `Q2`, … ID. Good for controlled, reproducible benchmarks where order and isolation matter.

---

## Requirements

```bash
pip install psycopg2-binary
```

---

## Usage

```bash
python timescale_queries.py --query-file <file.sql> [OPTIONS]
```

`--query-file` is the only required argument.

---

## Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--query-file` | string | *(required)* | Path to `.sql` file — one query per line |
| `--db-url` | string | `db.csv name=benchmark user=postgres password=pass host=localhost` | PostgreSQL libpq connection string |
| `--output` | string | `metrics/query_results.csv` | Output CSV file path. If no directory is given, `metrics/` is used automatically |
| `--workers` | int | `1` | Number of concurrent threads (ignored in `--ordered` mode) |
| `--ordered` | flag | off | Run queries sequentially in order and tag each result with a query ID |

---

## Query file format

A plain text `.sql` file with **one query per line**. Blank lines are skipped.

```sql
SELECT count(*) FROM ephemeris WHERE sat_id = 1;
SELECT * FROM ephemeris WHERE time > NOW() - INTERVAL '1 day' LIMIT 100;
SELECT sat_id, avg(x) FROM ephemeris GROUP BY sat_id;
```

Multi-line queries are not supported — each query must fit on a single line.

---

## Examples

### Basic benchmark — single thread, ordered output
```bash
python timescale_queries.py \
  --query-file queries.sql \
  --ordered \
  --db-url "host=localhost dbname=satellites user=postgres password=secret"
```
Each query runs in order, tagged Q1, Q2, … Results saved to `metrics/query_results.csv`.

---

### Parallel benchmark — 8 concurrent workers
```bash
python timescale_queries.py \
  --query-file queries.sql \
  --workers 8 \
  --db-url "host=localhost dbname=satellites user=postgres password=secret" \
  --output metrics/parallel_run.csv
```
Queries are distributed across 8 threads. Useful for stress-testing concurrent query throughput.

---

### Custom output path
```bash
python timescale_queries.py \
  --query-file queries.sql \
  --ordered \
  --output results/timescale_ordered.csv
```
The `results/` directory is created automatically if it does not exist.

---

## Output CSV format

### Parallel mode (default)

| Column | Description |
|---|---|
| `query` | The full query text |
| `cold_latency_ms` | Execution time of the first run (ms) |
| `warm_latency_ms` | Execution time of the second run (ms) |
| `num_rows` | Number of rows returned |

### Ordered mode (`--ordered`)

Same as above, with an extra leading column:

| Column | Description |
|---|---|
| `query_id` | Sequential label: `Q1`, `Q2`, `Q3`, … |
| `query` | The full query text |
| `cold_latency_ms` | Execution time of the first run (ms) |
| `warm_latency_ms` | Execution time of the second run (ms) |
| `num_rows` | Number of rows returned |

---

## Console output

Before running, the script validates the DB connection and exits early with a clear message if it fails — saving time on large query sets.

During execution, each query logs its progress:

```
cold run for Q1.
warm run for Q1.
cold run for Q2.
warm run for Q2.
...
```

At the end, a summary is printed:

```
------------------------------
Benchmark completed in 4.83 seconds.
Average COLD: 142.30 ms
Average WARM: 38.91 ms
Average ROWS: 5400
------------------------------
```

The gap between cold and warm averages is the key indicator of caching effectiveness.

---

## Notes

- Connections use `autocommit = True` to eliminate transaction overhead from pure read benchmarks. If your queries include writes, be aware there is no rollback.
- In parallel mode, query order in the output CSV is non-deterministic — threads complete in whatever order the OS schedules them. Use `--ordered` if result order matters.
- If a query fails, the error is printed and that query is skipped; the rest of the benchmark continues.
- The output directory (`metrics/` by default) is created automatically if it does not exist.
