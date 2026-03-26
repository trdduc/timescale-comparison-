import sys
import time
import argparse
import multiprocessing
import psycopg2
import csv
import queue as stdlib_queue
from io import StringIO
from datetime import datetime

def report_worker(row_count, byte_count, metrics_queue, start_time, reporting_period, metrics_file=None):
    """Handles console reporting and saves metrics to CSV for visualization."""
    prev_time = start_time
    prev_rows = 0
    prev_bytes = 0

    # Assign metrics file if requested
    csv_writer = None
    if metrics_file:
        f = open(metrics_file, 'w', newline='')
        csv_writer = csv.writer(f)
        csv_writer.writerow([
            'timestamp', 'elapsed_sec',
            'period_rate_rows_sec', 'overall_rate_rows_sec',
            'period_throughput_mb_sec', 'overall_throughput_mb_sec',
            'total_rows', 'total_mb',
            'avg_batch_latency_s', 'max_batch_latency_s',
            'avg_batch_row_rate', 'max_batch_row_rate'
        ])

    total_batches = 0
    total_batch_latency = 0.0

    try:
        while True:
            time.sleep(reporting_period)
            curr_rows = row_count.value
            curr_bytes = byte_count.value
            now = time.time()

            # Drain worker batch metrics queue
            batch_latencies = []
            batch_row_rates = []
            while True:
                try:
                    ts, batch_latency, rows, bytes_written, batch_row_rate, batch_mb_rate = metrics_queue.get_nowait()
                    batch_latencies.append(batch_latency)
                    batch_row_rates.append(batch_row_rate)
                    total_batches += 1
                    total_batch_latency += batch_latency
                except stdlib_queue.Empty:
                    break

            total_took = now - start_time
            period_took = now - prev_time

            p_rate = (curr_rows - prev_rows) / period_took if period_took > 0 else 0
            o_rate = curr_rows / total_took if total_took > 0 else 0

            p_throughput_mb = ((curr_bytes - prev_bytes) / 1024 / 1024) / period_took if period_took > 0 else 0
            o_throughput_mb = (curr_bytes / 1024 / 1024) / total_took if total_took > 0 else 0

            avg_batch_latency = (sum(batch_latencies) / len(batch_latencies)) if batch_latencies else 0
            max_batch_latency = max(batch_latencies) if batch_latencies else 0
            avg_batch_row_rate = (sum(batch_row_rates) / len(batch_row_rates)) if batch_row_rates else 0
            max_batch_row_rate = max(batch_row_rates) if batch_row_rates else 0

            mins, secs = divmod(int(total_took), 60)
            t_str = f"{mins}m{secs}s" if mins > 0 else f"{secs}s"
            print(f"at {t_str}, period rows {curr_rows - prev_rows}, period rate {p_rate:.2f} r/s, overall {o_rate:.2f} r/s, tradeoff {p_throughput_mb:.2f} MB/s, overall {o_throughput_mb:.2f} MB/s, avg batch latency {avg_batch_latency:.3f}s, max {max_batch_latency:.3f}s")

            if csv_writer:
                csv_writer.writerow([
                    datetime.now().isoformat(), round(total_took, 2),
                    round(p_rate, 2), round(o_rate, 2),
                    round(p_throughput_mb, 2), round(o_throughput_mb, 2),
                    curr_rows, round(curr_bytes / 1024 / 1024, 2),
                    round(avg_batch_latency, 4), round(max_batch_latency, 4),
                    round(avg_batch_row_rate, 2), round(max_batch_row_rate, 2)
                ])
                f.flush()

            prev_rows = curr_rows
            prev_bytes = curr_bytes
            prev_time = now

    except Exception as e:
        if metrics_file:
            f.close()

def db_worker(queue, metrics_queue, conn_str, schema, table, columns, split_char, row_count, byte_count):
    """Inserts batches into the database and emits per-batch timing metrics."""
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cols_part = f"({columns})" if columns else ""
    copy_query = f"COPY {schema}.{table} {cols_part} FROM STDIN WITH DELIMITER '{split_char}' CSV"

    while True:
        batch = queue.get()
        if batch is None:
            break

        batch_data = "\n".join(batch)
        buffer = StringIO(batch_data)

        try:
            batch_start = time.perf_counter()
            cur.copy_expert(copy_query, buffer)
            conn.commit()
            batch_end = time.perf_counter()

            batch_latency = batch_end - batch_start
            rows = len(batch)
            bytes_written = len(batch_data.encode('utf-8'))
            row_rate = rows / batch_latency if batch_latency > 0 else float('inf')
            mb_rate = (bytes_written / 1024 / 1024) / batch_latency if batch_latency > 0 else float('inf')

            with row_count.get_lock():
                row_count.value += rows
            with byte_count.get_lock():
                byte_count.value += bytes_written

            # Emit per-batch metrics to reporting process
            metrics_queue.put((datetime.now().isoformat(), batch_latency, rows, bytes_written, row_rate, mb_rate))

        except Exception as e:
            conn.rollback()
            print(f"\n[ERROR WORKER] {e}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", default="host=localhost dbname=test user=postgres", help="Database connection DSN")
    parser.add_argument("--table", required=True)
    parser.add_argument("--file", help="Input CSV file")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--reporting-period", type=int, default=10)
    parser.add_argument("--out-metrics", help="CSV file name for metrics/visualization (e.g., stats.csv)")
    args = parser.parse_args()

    # Configure workflow
    data_queue = multiprocessing.Queue(maxsize=args.workers * 2)
    metrics_queue = multiprocessing.Queue(maxsize=args.workers * 100)
    row_count = multiprocessing.Value('l', 0) # 'l' for long integers
    byte_count = multiprocessing.Value('l', 0) # 'l' for long integers
    start_time = time.time()

    # Start reporting process
    reporter = multiprocessing.Process(
        target=report_worker,
        args=(row_count, byte_count, metrics_queue, start_time, args.reporting_period, args.out_metrics),
        daemon=True
    )
    reporter.start()

    # Start insertion workers
    procs = []
    for _ in range(args.workers):
        p = multiprocessing.Process(
            target=db_worker,
            args=(data_queue, metrics_queue, args.db_url, "public", args.table, "", ",", row_count, byte_count)
        )
        p.start()
        procs.append(p)

    # Read file and fill queue
    input_f = open(args.file, 'r') if args.file else sys.stdin
    try:
        current_batch = []
        for line in input_f:
            current_batch.append(line.strip())
            if len(current_batch) >= args.batch_size:
                data_queue.put(current_batch)
                current_batch = []
        if current_batch:
            data_queue.put(current_batch)
    finally:
        if args.file:
            input_f.close()

    # Shutdown all processes
    for _ in range(args.workers):
        data_queue.put(None)
    for p in procs:
        p.join()
  
    total_time = time.time() - start_time
    total_mb = byte_count.value / 1024 / 1024
    throughput_mb_sec = total_mb / total_time if total_time > 0 else 0
    print(f"\n--- COMPLETED ---")
    print(f"Total rows: {row_count.value}")
    print(f"Total data: {total_mb:.2f} MB")
    print(f"Total time: {total_time:.2f}s")
    print(f"Final rate: {row_count.value / total_time:.2f} rows/sec")
    print(f"Final throughput: {throughput_mb_sec:.2f} MB/sec")
