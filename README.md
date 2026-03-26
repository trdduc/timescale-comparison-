# Timescale Comparison

This repository provides tools to investigate and compare the insertion, query, and deletion performance of TimescaleDB against other databases.(It can also be used for an individual performance test)

## Repository Structure


- **data**: Contains data for insertion and queries for database operations
- **docs/**: Documentation and results from script execution
    **docs/readme_scripts**    
    - Includes a README with the same structure as scripts folder
    - Individual README files for each script explaining functionality
- **metrics/**: Performance metrics in CSV format
    - Insertion details
    - Query performance data
    - Raw, untreated results
- **scripts/**: Automation scripts organized by operation type
    - `insertion/`: Scripts for insert operations
    - `queries/`: Scripts for query operations
    - `deletion/`: Scripts for delete operations
- **requirements.txt**:  requirements file used during the Docker build process to install all necessary dependencies into the Python

Although the scripts are designed to save files in folders corresponding to their characteristics, this structure is merely an example used in this study and can be customized as desired. The key components are the scripts in the 'scripts' directory and their associated README files for understanding; the rest can be adapted to suit individual needs.

## Deployment

This project utilizes Docker Compose to configure the required services, eliminating the need for local Python installations or library dependencies. If Docker is not being used, the necessary dependencies are specified in the requirements.txt file. 

### Steps

1. Clone this repository:
   ```
   git clone <repo-url>
   cd timescale-comparison
   ```

2. Start the services:
   ```
   docker-compose up -d
   ```

This will start the following services:

- **TimescaleDB**: A PostgreSQL database with TimescaleDB extension, accessible on port 5433.
- **PostgreSQL**: A standard PostgreSQL database, accessible on port 5434.
- **PgAdmin**: A web-based administration interface for PostgreSQL databases, accessible at         http://localhost:8080 
- **Python Lab**: A container with Python and required libraries for running the scripts ().

### Running Scripts

1. Access the Python lab container:
   ```
   docker exec -it python_lab bash
   ```

2. Navigate to the scripts directory and run the desired scripts.

The scripts are organized into subdirectories:

- **insertion/**: Scripts for data insertion operations.
- **queries/**: Scripts for query performance testing.
- **deletion/**: Scripts for data deletion operations.

Refer to the individual README files in `docs/readme_scripts/` for detailed instructions on each script.
