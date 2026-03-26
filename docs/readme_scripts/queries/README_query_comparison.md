# Query Comparison

## Description

This Python script compares benchmark results from two different systems (e.g., PostgreSQL vs. TimescaleDB) by analyzing their query performance data. It generates side-by-side bar charts for cold and warm query latencies, with queries sorted in natural order based on their identifiers.

## Prerequisites

- Python 3.6 or higher
- Required Python packages: `pandas`, `matplotlib`, `seaborn`

## Installation

1. Ensure Python 3.6+ is installed on your system.
2. Install the required dependencies using pip:

   ```bash
   pip install pandas matplotlib seaborn
   ```

## Usage

Execute the script from the command line with the following syntax:

```bash
python query_comparison.py FILE1.csv FILE2.csv [LABEL1] [LABEL2]
```

### Arguments

- `FILE1.csv` (required): Path to the first CSV file containing benchmark results.
- `FILE2.csv` (required): Path to the second CSV file containing benchmark results.
- `LABEL1` (optional): Label for the first system (default: "System A").
- `LABEL2` (optional): Label for the second system (default: "System B").

### CSV Format

Both input CSV files must contain the following columns:
- `query_id`: Unique identifier for each query (e.g., "Q1", "Q2", "Q10")
- `cold_latency_ms`: Latency values for cold queries in milliseconds
- `warm_latency_ms`: Latency values for warm queries in milliseconds

The script merges the datasets on `query_id`, so this column must be present and consistent across both files.

## Output

The script generates a PNG image file containing two subplots:
1. **Cold Latency Comparison**: Bar chart comparing cold query latencies between the two systems
2. **Warm Latency Comparison**: Bar chart comparing warm query latencies between the two systems

Queries are sorted in natural order (e.g., Q1, Q2, Q10 instead of Q1, Q10, Q2).

The output image is saved to `docs/comparison_charts.png` by default. The script will create the output directory if it does not exist.

## Examples

### Basic Usage with Default Labels
```bash
python query_comparison.py postgresql_results.csv timescale_results.csv
```
Generates comparison charts with labels "System A" and "System B".

### Custom Labels
```bash
python query_comparison.py pg_bench.csv ts_bench.csv "PostgreSQL" "TimescaleDB"
```
Generates comparison charts with custom labels.

## Error Handling

The script includes error handling for:
- Missing or invalid CSV files
- Missing required columns
- File I/O errors during chart generation

If an error occurs, an appropriate message will be printed to the console.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.