import psycopg2
import time
import csv
import argparse
import threading
import os
from queue import Queue, Empty

# --- Argument Configuration ---
parser = argparse.ArgumentParser(description="PostgreSQL/TimescaleDB Query Benchmark (High Performance Mode)")
parser.add_argument("--query-file", required=True, help="Path to .sql file with queries")
parser.add_argument("--output", default="metrics/query_results.csv", help="Output CSV file")
parser.add_argument("--workers", type=int, default=1, help="Number of concurrent threads")
parser.add_argument("--db-url", default="db.csv name=benchmark user=postgres password=pass host=localhost", help="Database connection string")
parser.add_argument("--ordered", action="store_true", help="Run queries sequentially in order (single worker) and add query IDs")
args = parser.parse_args()

results_lock = threading.Lock()

def check_db_connection(conn_str):
    try:
        conn = psycopg2.connect(conn_str)
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Database connection test failed: {e}")
        return False


def run_benchmark(query_queue, global_results, lock):
    """Function that executes each worker in a separate thread"""
    local_data = [] # Accumulate here to avoid blocking the data bus
    
    try:
        conn = psycopg2.connect(args.db_url)
        # Important: Autocommit to avoid transaction overhead if only queries
        conn.autocommit = True 
        cursor = conn.cursor()
    except Exception as e:
        print(f"[-] Worker connection error: {e}")
        return

    while True:
        try:
            # Get query from queue without indefinitely blocking
            query = query_queue.get_nowait()
        except Empty:
            break # Queue is empty

        query = query.strip()
        if not query:
            query_queue.task_done()
            continue

        try:
            print("cold run .")
            start_cold = time.perf_counter()
            cursor.execute(query)
            if cursor.description is not None:  # query returns rows
                rows = cursor.fetchall()
                num_rows = len(rows)
            else:
                num_rows = 0
            cold_ms = (time.perf_counter() - start_cold) * 1000

            print("warm run.")
            start_warm = time.perf_counter()
            cursor.execute(query)
            if cursor.description is not None:
                cursor.fetchall()  # We already know num_rows from cold run
            warm_ms = (time.perf_counter() - start_warm) * 1000

            # Save to worker's local list
            local_data.append([query, round(cold_ms, 4), round(warm_ms, 4), num_rows])
            
        except Exception as e:
            print(f"[-] Error executing: {query[:30]}... -> {e}")
        finally:
            query_queue.task_done()

    # At loop end, flush all to global list in a thread-safe way
    with lock:
        global_results.extend(local_data)
def run_benchmark_sequential(queries, results):
    """Sequential execution with query IDs"""
    try:
        conn = psycopg2.connect(args.db_url)
        conn.autocommit = True
        cursor = conn.cursor()
    except Exception as e:
        print(f"[-] Connection error: {e}")
        return

    for idx, query in enumerate(queries, start=1):
        query = query.strip()
        if not query:
            continue

        query_id = f"Q{idx}"
        try:
            print(f"cold run for {query_id}.")
            start_cold = time.perf_counter()
            cursor.execute(query)
            if cursor.description is not None:
                rows = cursor.fetchall()
                num_rows = len(rows)
            else:
                num_rows = 0
            cold_ms = (time.perf_counter() - start_cold) * 1000

            print(f"warm run for {query_id}.")
            start_warm = time.perf_counter()
            cursor.execute(query)
            if cursor.description is not None:
                cursor.fetchall()
            warm_ms = (time.perf_counter() - start_warm) * 1000

            results.append([query_id, query, round(cold_ms, 4), round(warm_ms, 4), num_rows])
            
        except Exception as e:
            print(f"[-] Error executing {query_id}: {query[:30]}... -> {e}")

    cursor.close()
    conn.close()

def main():
    # 0. Validate DB connection before running heavy benchmark
    if not check_db_connection(args.db_url):
        print("Please fix --db-url and ensure the database is reachable before running again.")
        return

    # 1. Load queries
    try:
        with open(args.query_file, 'r') as f:
            queries = [line for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File not found {args.query_file}")
        return

    if not queries:
        print("No queries to execute. Exiting.")
        return

    print(f"[*] Starting benchmark: {len(queries)} queries.")

    shared_results = []

    if args.ordered:
        print("[*] Running in ordered mode (sequential, single worker).")
        start_total = time.perf_counter()
        run_benchmark_sequential(queries, shared_results)
        end_total = time.perf_counter()
    else:
        print(f"[*] Running in parallel mode with {args.workers} workers.")
        # 2. Prepare infrastructure
        query_queue = Queue()
        for q in queries:
            query_queue.put(q)

        threads = []

        print("Launching workers.")
        start_total = time.perf_counter()
        for _ in range(args.workers):
            t = threading.Thread(target=run_benchmark, args=(query_queue, shared_results, results_lock))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
        
        end_total = time.perf_counter()

    # 4. Final single write
    # Normalize output path: if no directory specified, write into metrics/ by default
    output_path = args.output
    output_dir = os.path.dirname(output_path)
    if not output_dir:
        output_path = os.path.join('metrics', output_path)
        output_dir = 'metrics'

    print(f"[*] Writing results to {output_path}...")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if args.ordered:
            writer.writerow(["query_id", "query", "cold_latency_ms", "warm_latency_ms", "num_rows"])
        else:
            writer.writerow(["query", "cold_latency_ms", "warm_latency_ms", "num_rows"])
        writer.writerows(shared_results)

    # 5. Quick console summary
    total_time = end_total - start_total
    cold_idx = 2 if args.ordered else 1
    warm_idx = 3 if args.ordered else 2
    rows_idx = 4 if args.ordered else 3
    avg_cold = sum(r[cold_idx] for r in shared_results) / len(shared_results) if shared_results else 0
    avg_warm = sum(r[warm_idx] for r in shared_results) / len(shared_results) if shared_results else 0
    avg_rows = sum(r[rows_idx] for r in shared_results) / len(shared_results) if shared_results else 0

    print("-" * 30)
    print(f"Benchmark completed in {total_time:.2f} seconds.")
    print(f"Average COLD: {avg_cold:.2f} ms")
    print(f"Average WARM: {avg_warm:.2f} ms")
    print(f"Average ROWS: {avg_rows:.0f}")
    print("-" * 30)

if __name__ == "__main__":
    main()