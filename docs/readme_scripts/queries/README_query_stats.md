# Query Stats

## Description

This Python script analyzes benchmark data from a CSV file and generates a comprehensive statistical report on query performance. It provides detailed latency statistics, identifies performance outliers (slowest and fastest queries), and summarizes key metrics for cold and warm query executions.

## Prerequisites

- Python 3.6 or higher
- Required Python package: `pandas`

## Installation

1. Ensure Python 3.6+ is installed on your system.
2. Install the required dependency using pip:

   ```bash
   pip install pandas
   ```

## Usage

Execute the script from the command line with the following syntax:

```bash
python query_stats.py CSV_FILE [--output OUTPUT_NAME]
```

### Arguments

- `CSV_FILE` (required): Path to the input CSV file containing benchmark results.
- `--output OUTPUT_NAME` (optional): Base name for the output file (without extension). The report will be saved as `docs/OUTPUT_NAME.txt`. If not specified, defaults to `query_stats`.

### CSV Format

The input CSV file must contain at least the following columns:
- `cold_latency_ms`: Latency values for cold queries in milliseconds
- `warm_latency_ms`: Latency values for warm queries in milliseconds
- `query`: The query string or identifier

Optional columns:
- `num_rows`: Number of rows returned by each query

## Output

The script generates a text-based report saved to `docs/{output_name}.txt` containing:

- **Summary Statistics**: Total queries processed, total latency times, and row counts (if available)
- **Detailed Latency Statistics**: Descriptive statistics (count, mean, std dev, min, percentiles, max) for cold and warm latencies
- **Performance Outliers**:
  - Top 5 slowest queries (warm latency)
  - Top 5 fastest queries (warm latency)
  - Top 5 slowest queries (cold latency)
  - Top 5 fastest queries (cold latency)

The report is formatted for easy reading with clear section headers.

## Examples

### Basic Usage
```bash
python query_stats.py benchmark_results.csv
```
Generates `docs/query_stats.txt`

### Custom Output Name
```bash
python query_stats.py my_benchmark.csv --output custom_report
```
Generates `docs/custom_report.txt`

## Error Handling

The script includes error handling for:
- Missing or invalid CSV files
- Empty CSV files
- File I/O errors during report generation

If an error occurs, an appropriate message will be printed to the console.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.