import os
import pandas as pd
import sys
import argparse

def analyze_benchmark(csv_file, output_name="query_stats"):
    output_file = f"docs/{output_name}.txt"
    os.makedirs("docs", exist_ok=True)

    try:
        df = pd.read_csv(csv_file)

        if df.empty:
            print("The CSV file is empty.")
            return

        with open(output_file, 'w') as f:
            f.write(f"{'='*20} BENCHMARK REPORT {'='*20}\n")
            f.write(f"Total Queries Processed: {len(df)}\n")

            # Additional stats
            total_cold_time = df['cold_latency_ms'].sum()
            total_warm_time = df['warm_latency_ms'].sum()
            f.write(f"Total Cold Latency Time: {total_cold_time:.2f} ms\n")
            f.write(f"Total Warm Latency Time: {total_warm_time:.2f} ms\n")

            if 'num_rows' in df.columns:
                total_rows = df['num_rows'].sum()
                avg_rows = df['num_rows'].mean()
                f.write(f"Total Rows Returned: {total_rows}\n")
                f.write(f"Average Rows per Query: {avg_rows:.1f}\n")

            # Statistics for Cold and Warm latencies
            stats = df[['cold_latency_ms', 'warm_latency_ms']].describe(percentiles=[.25, .5, .75, .95, .99])

            # We rename the index for clarity
            stats.index = ['Count', 'Mean', 'Std Dev', 'Min', '25% (Q1)', '50% (Median)', '75% (Q3)', '95% (P95)', '99% (P99)', 'Max']
            f.write("\nDetailed Latency Statistics (ms):\n")
            f.write(stats.round(2).to_string())
            f.write("\n")

            # Identify the "Heavy Hitters" (Slowest 5 queries)
            f.write(f"\n{'='*20} 5 SLOWEST QUERIES (WARM) {'='*20}\n")
            slowest = df.nlargest(5, 'warm_latency_ms')[['warm_latency_ms', 'query']]
            for i, row in slowest.iterrows():
                f.write(f"- {row['warm_latency_ms']:.2f} ms: {row['query']}\n")

            # Top 5 fastest queries (warm)
            f.write(f"\n{'='*20} 5 FASTEST QUERIES (WARM) {'='*20}\n")
            fastest = df.nsmallest(5, 'warm_latency_ms')[['warm_latency_ms', 'query']]
            for i, row in fastest.iterrows():
                f.write(f"- {row['warm_latency_ms']:.2f} ms: {row['query']}\n")

            # Top 5 slowest queries (cold)
            f.write(f"\n{'='*20} 5 SLOWEST QUERIES (COLD) {'='*20}\n")
            slowest_cold = df.nlargest(5, 'cold_latency_ms')[['cold_latency_ms', 'query']]
            for i, row in slowest_cold.iterrows():
                f.write(f"- {row['cold_latency_ms']:.2f} ms: {row['query']}\n")

            # Top 5 fastest queries (cold)
            f.write(f"\n{'='*20} 5 FASTEST QUERIES (COLD) {'='*20}\n")
            fastest_cold = df.nsmallest(5, 'cold_latency_ms')[['cold_latency_ms', 'query']]
            for i, row in fastest_cold.iterrows():
                f.write(f"- {row['cold_latency_ms']:.2f} ms: {row['query']}\n")

        print(f"Report saved to {output_file}")

    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze benchmark CSV and generate stats report")
    parser.add_argument("csv_file", help="Path to the benchmark CSV file")
    parser.add_argument("--output", default="query_stats", help="Output file name (without extension, saved in docs/)")
    args = parser.parse_args()

    analyze_benchmark(args.csv_file, args.output)