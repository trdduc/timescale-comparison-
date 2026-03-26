# Satellite Ephemeris CSV Generator

A command-line tool that generates synthetic satellite ephemeris data (position and velocity over time) for database load testing and development purposes.

## What it does

The script simulates orbital motion for one or more satellites over a configurable time period, writing each record to a CSV file. Each row contains:

| Column | Description |
|--------|-------------|
| `ephemeris_id` | Satellite identifier (integer, starting at 1) |
| `time` | Timestamp of the record (`YYYY-MM-DD HH:MM:SS`) |
| `x`, `y`, `z` | Position components in km |
| `vx`, `vy`, `vz` | Velocity components in km/s |

The orbital physics are simplified (circular orbits with a minor z-axis oscillation), making this suitable for generating realistic-looking bulk data rather than scientifically accurate simulations.

---

## Requirements

- Python 3.x (no external dependencies — only standard library modules)

---

## Usage

```bash
python csv_sv_generator.py [OPTIONS]
```

Run with `--help` to see all options:

```bash
python csv_sv_generator.py --help
```

---

## Arguments

| Flag | Long form | Type | Default | Description |
|------|-----------|------|---------|-------------|
| `-f` | `--file` | string | `efemerides_datos.csv` | Output CSV file path/name |
| `-s` | `--satellites` | int | `100` | Number of satellites to simulate |
| `-d` | `--days` | int | `7` | Duration of data in days |
| `-i` | `--interval` | int | `10` | Time interval in seconds between records |
| `-date` | `--start-date` | string | `2026-01-01` | Start date in `YYYY-MM-DD` format |
| `-m` | `--mode` | choice | `distributed` | Row ordering mode: `distributed` or `linear` (see below) |

---

## Generation Modes

The `--mode` flag controls the order in which rows are written to the CSV. This is important depending on how you intend to load the data.

### `distributed` (default)
Rows are grouped **by satellite**. All time steps for satellite 1 are written first, then all time steps for satellite 2, and so on.

```
sat_id=1, t=00:00
sat_id=1, t=00:10
sat_id=1, t=00:20
...
sat_id=2, t=00:00
sat_id=2, t=00:10
...
```

Best for: bulk inserts per satellite, partitioned tables, or when you query by satellite ID.

---

### `linear`
Rows are ordered **by timestamp**. At each time step, one row per satellite is written before advancing to the next time step.

```
sat_id=1, t=00:00
sat_id=2, t=00:00
sat_id=3, t=00:00
...
sat_id=1, t=00:10
sat_id=2, t=00:10
...
```

Best for: time-series databases, streaming ingestion, or when you query by time range across all satellites.

---

## Examples

### Generate a small test file (defaults)
```bash
python csv_sv_generator.py
```
Produces `efemerides_datos.csv` with 100 satellites × 7 days × 10s interval = **6,048,000 rows**.

---

### Custom output file and fewer satellites
```bash
python csv_sv_generator.py -f test_output.csv -s 10 -d 1
```
10 satellites, 1 day, 10s interval → 8,640 rows.

---

### High-frequency data with a specific start date
```bash
python csv_sv_generator.py -s 50 -d 3 -i 1 --start-date 2025-06-01 -f high_freq.csv
```
50 satellites, 3 days, 1-second interval → 12,960,000 rows.

---

### Time-ordered output for a time-series database
```bash
python csv_sv_generator.py -m linear -s 200 -d 7 -i 30 -f timeseries_load.csv
```
200 satellites, 7 days, 30s interval in time-linear order → 4,032,000 rows.

---

### Low-volume smoke test
```bash
python csv_sv_generator.py -s 5 -d 1 -i 3600 -f smoke_test.csv
```
5 satellites, 1 day, 1-hour interval → 120 rows. Good for quickly checking column format before a big run.

---

## Row count formula

To estimate the output size before running:

```
total_rows = num_satellites × floor((days × 24 × 3600) / interval_seconds)
```

The script prints this estimate at startup along with all active configuration values.

---

## Output format

The CSV has **no header row** by default. If your database loader expects a header, open the script and uncomment the relevant `writer.writerow(...)` line in the function you are using:

```python
# writer.writerow(["ephemeris_id", "time", "x", "y", "z", "vx", "vy", "vz"])
```

---

## Progress reporting

- In `distributed` mode: progress is printed every 10 satellites (or at the last satellite).
- In `linear` mode: progress is printed approximately every 10% of time steps.
