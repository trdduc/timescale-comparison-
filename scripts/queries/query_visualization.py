import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

def generate_plots(csv_file, output_image="docs/performance_charts.png"):
    os.makedirs(os.path.dirname(output_image), exist_ok=True)
    try:
        # 1. Load data
        df = pd.read_csv(csv_file)
        if df.empty:
            print("CSV is empty.")
            return

        # 2. Setup the visualization style
        sns.set_theme(style="whitegrid")
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # --- Plot 1: Histogram (Cold latency) ---
        sns.histplot(data=df, x='cold_latency_ms', kde=True, color='tab:blue', ax=axes[0], stat='density', alpha=0.7)
        mean_cold = df['cold_latency_ms'].mean()
        axes[0].axvline(mean_cold, color='black', linestyle='--', linewidth=1.5)
        axes[0].text(mean_cold, axes[0].get_ylim()[1] * 0.9, f'{mean_cold:.1f}ms', rotation=90, va='center', ha='right')
        axes[0].set_title('Cold Query Latency Distribution', fontsize=14)
        axes[0].set_xlabel('Cold Latency (ms)')

        # --- Plot 2: Histogram (Warm latency) ---
        sns.histplot(data=df, x='warm_latency_ms', kde=True, color='tab:orange', ax=axes[1], stat='density', alpha=0.7)
        mean_warm = df['warm_latency_ms'].mean()
        axes[1].axvline(mean_warm, color='black', linestyle='--', linewidth=1.5)
        axes[1].text(mean_warm, axes[1].get_ylim()[1] * 0.9, f'{mean_warm:.1f}ms', rotation=90, va='center', ha='right')
        axes[1].set_title('Warm Query Latency Distribution', fontsize=14)
        axes[1].set_xlabel('Warm Latency (ms)')

        # --- Plot 3: Boxplot (Outliers and Quartiles) ---
        df_melted = df.melt(value_vars=['cold_latency_ms', 'warm_latency_ms'],
                            var_name='Type', value_name='Latency (ms)')
        sns.boxplot(
            data=df_melted,
            x='Type',
            y='Latency (ms)',
            ax=axes[2],
            palette=['tab:blue', 'tab:orange'],
            showmeans=True,
            meanline=True,
            meanprops={'linestyle': '--', 'color': 'black', 'linewidth': 1.2},
            medianprops={'color': 'firebrick'}
        )

        mean_cold = df['cold_latency_ms'].mean()
        mean_warm = df['warm_latency_ms'].mean()
        axes[2].text(0, mean_cold + (mean_cold * 0.02), f'{mean_cold:.1f} ms',
                     color='black', ha='center', va='bottom', fontsize=9)
        axes[2].text(1, mean_warm + (mean_warm * 0.02), f'{mean_warm:.1f} ms',
                     color='black', ha='center', va='bottom', fontsize=9)

        axes[2].set_title('Latency Variance & Outliers', fontsize=14)
        axes[2].set_ylabel('Milliseconds (ms)')
        sns.despine(ax=axes[2], trim=True)

        # 3. Final Touches
        plt.tight_layout()
        plt.savefig(output_image, dpi=300)
        print(f"Charts saved as: {output_image}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "benchmark_results.csv"
    generate_plots(file_path)