import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.ticker as ticker

# --- Configuration ---
sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'legend.fontsize': 10,
    'figure.figsize': (12, 7)
})

METRICS_DIR = 'metrics'
DOCS_DIR = 'docs'
DB_LABELS = {
    'timescale_bench.csv': 'TimescaleDB',
    'postgres_bench.csv': 'PostgreSQL'
}

def load_benchmark_data(filename, label):
    """Loads and cleans benchmark CSV data."""
    path = os.path.join(METRICS_DIR, filename)
    if not os.path.exists(path):
        print(f"[!] Warning: {path} not found. Skipping {label}.")
        return None

    # Load data
    df = pd.read_csv(path)
    
    # Ensure numeric types and handle potential corruption or nulls
    cols_to_fix = ['total_rows', 'period_rate_rows_sec', 'period_throughput_mb_sec', 'elapsed_sec']
    for col in cols_to_fix:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows where critical metrics are missing
    df = df.dropna(subset=['total_rows', 'period_rate_rows_sec'])
    
    # Add database identifier for plotting
    df['database'] = label
    return df

def create_plots():
    """Generates academic-grade visualizations for the benchmark."""
    # Ensure output directory exists
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)

    # 1. Load and combine data
    dataframes = []
    for file, label in DB_LABELS.items():
        df = load_benchmark_data(file, label)
        if df is not None:
            dataframes.append(df)

    if not dataframes:
        print("[!] Error: No valid data found in /metrics to plot.")
        return

    full_df = pd.concat(dataframes, ignore_index=True)

    # --- Plot 1: Insertion Speed vs Table Volume ---
    # Purpose: Observe performance degradation as the B-Tree/Index grows
    plt.figure()
    ax1 = sns.lineplot(
        data=full_df,
        x='total_rows',
        y='period_rate_rows_sec',
        hue='database',
        palette='Set1',
        linewidth=2.5,
        marker='o',
        markevery=0.1 # Show markers at 10% intervals to avoid clutter
    )

    plt.title('Insertion Rate Stability vs. Data Volume (2 CPUs, 2GB RAM)', pad=20)
    plt.xlabel('Total Rows Inserted (Cumulative)')
    plt.ylabel('Instantaneous Rate (Rows/Second)')
    
    # Format X axis to show millions (M) for better readability
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.1f}M'))
    plt.legend(title='Database System')
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, 'insertion_stability.png'), dpi=300)
    print(f"[+] Saved: {DOCS_DIR}/insertion_stability.png")

    # --- Plot 2: Throughput (MB/s) vs Time ---
    # Purpose: Compare IO performance over the duration of the test
    plt.figure()
    ax2 = sns.lineplot(
        data=full_df,
        x='elapsed_sec',
        y='period_throughput_mb_sec',
        hue='database',
        palette='Set1',
        linewidth=2.5
    )

    plt.title('Data Throughput Over Time', pad=20)
    plt.xlabel('Elapsed Time (Seconds)')
    plt.ylabel('Throughput (MB/s)')
    
    plt.legend(title='Database System')
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, 'throughput_over_time.png'), dpi=300)
    print(f"[+] Saved: {DOCS_DIR}/throughput_over_time.png")
    # --- Plot 3: Latency vs Table Volume  ---

    plt.figure()
    ax3 = sns.lineplot(
        data=full_df,
        x='total_rows',
        y='avg_batch_latency_s', # Using the new latency column
        hue='database',
        palette='Set1',
        linewidth=2.5
    )

    plt.title('Average Batch Latency vs. Data Volume', pad=20)
    plt.xlabel('Total Rows Inserted (Millions)')
    plt.ylabel('Latency per Batch (Seconds)')
    
    # Format X axis in Millions
    ax3.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.1f}M'))
    
    plt.legend(title='Database System')
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, 'latency_comparison.png'), dpi=300)
    print(f"[+] Saved: {DOCS_DIR}/latency_comparison.png")


if __name__ == "__main__":
    print("--- Starting Visualization Process ---")
    create_plots()
    print("--- Visualization Completed ---")
