import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import re  # Importamos expresiones regulares para extraer los números

def extract_number(query_id):
    """Extrae el número de un string como 'Q1', 'Q10' -> devuelve 1, 10"""
    match = re.search(r'\d+', str(query_id))
    return int(match.group()) if match else 0

def compare_results(file1, file2, label1="PostgreSQL", label2="TimescaleDB", output_image="docs/comparison_charts.png"):
    os.makedirs(os.path.dirname(output_image), exist_ok=True)
    try:
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        
        # 1. Unir ambos datasets
        combined = pd.merge(df1, df2, on='query_id', suffixes=(f'_{label1}', f'_{label2}'))
        
        # 2. ORDENACIÓN NATURAL:
        # Creamos una columna temporal con el valor numérico de la query
        combined['sort_val'] = combined['query_id'].apply(extract_number)
        # Ordenamos por ese número y luego borramos la columna temporal
        combined = combined.sort_values('sort_val').drop('sort_val', axis=1)

        # 3. Configuración del lienzo
        sns.set_theme(style="white")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))

        def draw_grouped_bars(metric_name, title, ax):
            cols = [f'{metric_name}_{label1}', f'{metric_name}_{label2}']
            plot_data = combined.melt(id_vars=['query_id'], value_vars=cols, 
                                      var_name='Sistema', value_name='ms')
            
            plot_data['Sistema'] = plot_data['Sistema'].replace({cols[0]: label1, cols[1]: label2})
            
            sns.barplot(data=plot_data, x='query_id', y='ms', hue='Sistema', 
                        ax=ax, palette=['tab:blue', 'tab:orange'], edgecolor='black')
            
            ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
            ax.set_ylabel('Execution Time (ms)', fontsize=12)
            ax.set_xlabel('Query ID', fontsize=12)
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            ax.legend(frameon=True, loc='upper right', edgecolor='black')
            
            # Ajustar etiquetas del eje X
            plt.setp(ax.get_xticklabels(), rotation=0) # Si son pocas, mejor sin rotar. Si son muchas, pon 45.

        # Panel Superior: Cold Latency
        draw_grouped_bars('cold_latency_ms', 'Cold Latency Comparison', ax1)

        # Panel Inferior: Warm Latency
        draw_grouped_bars('warm_latency_ms', 'Warm Latency Comparison', ax2)

        plt.tight_layout()
        plt.savefig(output_image, dpi=300)
        print(f"✅ Gráfico ordenado guardado en: {output_image}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python script.py file1.csv file2.csv [Nombre1] [Nombre2]")
    else:
        f1, f2 = sys.argv[1], sys.argv[2]
        n1 = sys.argv[3] if len(sys.argv) > 3 else "System A"
        n2 = sys.argv[4] if len(sys.argv) > 4 else "System B"
        compare_results(f1, f2, n1, n2)