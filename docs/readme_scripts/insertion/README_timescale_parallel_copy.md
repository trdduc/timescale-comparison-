# Parallel CSV Loader for PostgreSQL / TimescaleDB

A high-performance, multi-process tool that loads CSV data into a PostgreSQL (or TimescaleDB) table using parallel `COPY` workers. Designed for bulk ingestion benchmarking and large dataset loading.

## How it works

The script runs three types of processes concurrently:

1. **Main process** — reads the input CSV file (or stdin) line by line and fills a shared work queue in batches.
2. **DB workers** — each worker pulls batches from the queue and inserts them into the database using PostgreSQL's native `COPY FROM STDIN` command, which is significantly faster than `INSERT`.
3. **Reporter process** — runs in the background, printing ingestion metrics to the console at a configurable interval and optionally writing them to a CSV file for later visualization.

```
Input CSV / stdin
      │
      ▼
 Main process  ──── batches ──▶  Queue
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
               DB worker 1   DB worker 2   DB worker N
                    │              │              │
                    └──────────────┴──────────────┘
                                   │
                              PostgreSQL table
```

---

## Requirements

```bash
pip install psycopg2-binary
```

Python 3.x standard library handles everything else (`multiprocessing`, `csv`, `argparse`, etc.).

---

## Usage

```bash
python timescale_parallel_copy.py --table <table_name> [OPTIONS]
```

`--table` is the only required argument. Everything else has a sensible default.

---

## Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--table` | string | *(required)* | Target table name (always inserted into the `public` schema) |
| `--db-url` | string | `host=localhost dbname=test user=postgres` | PostgreSQL connection DSN (libpq format) |
| `--file` | string | *(stdin)* | Input CSV file path. If omitted, reads from standard input |
| `--workers` | int | `1` | Number of parallel DB worker processes |
| `--batch-size` | int | `5000` | Number of rows per `COPY` batch |
| `--reporting-period` | int | `10` | How often (in seconds) to print progress metrics to console |
| `--out-metrics` | string | *(none)* | If set, saves per-period metrics to this CSV file for analysis |

---

## Examples

### Minimal — load a file with one worker
```bash
python timescale_parallel_copy.py \
  --table ephemeris \
  --file data.csv
```

---

### Parallel load with 4 workers
```bash
python timescale_parallel_copy.py \
  --table ephemeris \
  --file data.csv \
  --workers 4
```
Each worker maintains its own database connection and inserts independently. Good starting point: match worker count to available CPU cores or DB connection limit.

---

### Custom batch size and connection string
```bash
python timescale_parallel_copy.py \
  --table ephemeris \
  --file data.csv \
  --workers 4 \
  --batch-size 20000 \
  --db-url "host=mydb.internal port=5432 dbname=satellites user=loader password=secret"
```
Larger batch sizes reduce per-commit overhead but increase memory use. A value between 5,000–50,000 is typical for time-series data.

---

### Save metrics to a CSV for charting
```bash
python timescale_parallel_copy.py \
  --table ephemeris \
  --file data.csv \
  --workers 8 \
  --reporting-period 5 \
  --out-metrics run_stats.csv
```
The metrics file can be imported into any spreadsheet or plotting tool to visualize throughput over time.

---

### Pipe from another process (stdin mode)
```bash
cat data.csv | python timescale_parallel_copy.py --table ephemeris --workers 4
```
When `--file` is not provided, the script reads from stdin, making it composable in shell pipelines.

---

## Console output

While running, the reporter prints a line every `--reporting-period` seconds:

```
at 30s, period rows 142500, period rate 14250.00 r/s, overall 13980.00 r/s, tradeoff 2.31 MB/s, overall 2.27 MB/s, avg batch latency 0.034s, max 0.051s
```

| Field | Description |
|-------|-------------|
| `period rows` | Rows inserted in the last reporting window |
| `period rate` | Rows/sec during the last window |
| `overall` (rows) | Rows/sec since start |
| `tradeoff` (MB/s) | Data throughput during the last window |
| `overall` (MB/s) | Data throughput since start |
| `avg batch latency` | Average time per `COPY` commit across workers in this window |
| `max batch latency` | Slowest single batch commit in this window |

---

## Metrics CSV columns

When `--out-metrics` is used, the output file contains one row per reporting period:

| Column | Description |
|--------|-------------|
| `timestamp` | Wall-clock time of the measurement |
| `elapsed_sec` | Seconds since the job started |
| `period_rate_rows_sec` | Rows/sec in the last period |
| `overall_rate_rows_sec` | Rows/sec since start |
| `period_throughput_mb_sec` | MB/sec in the last period |
| `overall_throughput_mb_sec` | MB/sec since start |
| `total_rows` | Cumulative rows inserted |
| `total_mb` | Cumulative data inserted (MB) |
| `avg_batch_latency_s` | Average `COPY` commit time this period |
| `max_batch_latency_s` | Slowest `COPY` commit this period |
| `avg_batch_row_rate` | Average rows/sec per batch this period |
| `max_batch_row_rate` | Fastest batch rows/sec this period |

---

## Final summary

At completion, the script always prints a summary regardless of `--out-metrics`:

```
--- COMPLETED ---
Total rows: 6048000
Total data: 983.45 MB
Total time: 68.21s
Final rate: 88667.42 rows/sec
Final throughput: 14.42 MB/sec
```

---

## Notes and limitations

- The target schema is hardcoded to `public`. To use a different schema, edit the `db_worker` call in the `__main__` block.
- The column list passed to `COPY` is currently empty, meaning PostgreSQL expects the CSV columns to match the table definition exactly, in order. To specify columns explicitly, edit the `columns` argument in the same `db_worker` call.
- The CSV delimiter is hardcoded to `,`. Edit the `split_char` argument in `db_worker` to change it.
- If a batch fails, the worker rolls back that batch and prints an error, but continues processing — the rest of the load is not aborted.
- Worker count beyond the database's `max_connections` limit will cause connection errors. Check your DB config before setting `--workers` high.
