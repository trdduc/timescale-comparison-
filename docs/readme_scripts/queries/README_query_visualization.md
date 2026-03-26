# Query Visualization

## Description

This Python script generates performance visualization charts from CSV benchmark data, focusing on cold and warm query latencies. It creates histograms and boxplots to analyze latency distributions and outliers.

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
python query_visualization.py [CSV_FILE]
```

### Arguments

- `CSV_FILE` (optional): Path to the input CSV file containing benchmark results. If not specified, the script defaults to `benchmark_results.csv`.

### CSV Format

The input CSV file must contain at least the following columns:
- `cold_latency_ms`: Latency values for cold queries in milliseconds
- `warm_latency_ms`: Latency values for warm queries in milliseconds

## Output

The script generates a single PNG image file containing three subplots:
1. **Cold Query Latency Distribution**: Histogram with kernel density estimate
2. **Warm Query Latency Distribution**: Histogram with kernel density estimate
3. **Latency Variance & Outliers**: Boxplot comparing cold and warm latencies

The output image is saved to `docs/performance_charts.png` by default. The script will create the output directory if it does not exist.

## Examples

### Basic Usage (using default CSV file)
```bash
python query_visualization.py
```

### Specifying a Custom CSV File
```bash
python query_visualization.py path/to/my_benchmark_results.csv
```

## Error Handling

The script includes error handling for:
- Missing or empty CSV files
- Invalid CSV format
- File I/O errors

If an error occurs, an appropriate message will be printed to the console.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.