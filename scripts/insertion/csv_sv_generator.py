import argparse
import csv
import math
import sys
from datetime import datetime, timedelta

def generate_data_per_satellite(file_name, num_satellites, days, interval_seconds, start_time):
    total_steps = int((days * 24 * 3600) / interval_seconds)
    total_rows = num_satellites * total_steps

    print(f"--- Current config ---")
    print(f"File: {file_name}")
    print(f"Num_Satellites: {num_satellites}")
    print(f"Days: {days}")
    print(f"Interval: {interval_seconds} seconds")
    print(f"Start_Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"----------------------------")
    print(f"Generating approximately {total_rows} rows...\n")

    try:
        with open(file_name, mode='w', newline='') as f:
            writer = csv.writer(f)
            # Header: ephemeris_id, time, x, y, z, vx, vy, vz
            # If your DB expects CSV header, uncomment:
            # writer.writerow(["ephemeris_id", "time", "x", "y", "z", "vx", "vy", "vz"])
            
            count = 0
            for sat_id in range(1, num_satellites + 1):
                # Base orbital parameters
                radius = 6700 + (sat_id * 2) 
                velocity = math.sqrt(398600 / radius) 
                
                for step in range(total_steps):
                    current_time = start_time + timedelta(seconds=step * interval_seconds)
                    
                    # Motion simulation
                    angle = (step * interval_seconds * 0.001) + sat_id
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    z = (radius / 10) * math.sin(angle / 2) 
                    
                    vx = -velocity * math.sin(angle)
                    vy = velocity * math.cos(angle)
                    vz = 0.1 
                    
                    writer.writerow([
                        sat_id, 
                        current_time.strftime('%Y-%m-%d %H:%M:%S'), 
                        round(x, 4), round(y, 4), round(z, 4), 
                        round(vx, 4), round(vy, 4), round(vz, 4)
                    ])
                    count += 1
                
                if sat_id % 10 == 0 or sat_id == num_satellites:
                    print(f"Progress: {sat_id}/{num_satellites} satellites completed...")

        print(f"\nReady! File '{file_name}' was generated with {count} rows.")
    
    except Exception as e:
        print(f"Error generating the file: {e}")


def generate_data_linear_time(file_name, num_satellites, days, interval_seconds, start_time):
    total_steps = int((days * 24 * 3600) / interval_seconds)
    total_rows = num_satellites * total_steps

    print(f"--- Current config (linear time mode) ---")
    print(f"File: {file_name}")
    print(f"Num_Satellites: {num_satellites}")
    print(f"Days: {days}")
    print(f"Interval: {interval_seconds} seconds")
    print(f"Start_Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"----------------------------")
    print(f"Generating approximately {total_rows} rows in time order...\n")

    try:
        with open(file_name, mode='w', newline='') as f:
            writer = csv.writer(f)
            # Header: ephemeris_id, time, x, y, z, vx, vy, vz
            # If your DB expects CSV header, uncomment:
            # writer.writerow(["ephemeris_id", "time", "x", "y", "z", "vx", "vy", "vz"])

            count = 0
            for step in range(total_steps):
                current_time = start_time + timedelta(seconds=step * interval_seconds)
                for sat_id in range(1, num_satellites + 1):
                    radius = 6700 + (sat_id * 2)
                    velocity = math.sqrt(398600 / radius)
                    angle = (step * interval_seconds * 0.001) + sat_id
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)
                    z = (radius / 10) * math.sin(angle / 2)
                    vx = -velocity * math.sin(angle)
                    vy = velocity * math.cos(angle)
                    vz = 0.1

                    writer.writerow([
                        sat_id,
                        current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        round(x, 4), round(y, 4), round(z, 4),
                        round(vx, 4), round(vy, 4), round(vz, 4)
                    ])
                    count += 1

                if (step + 1) % max(1, total_steps // 10) == 0 or step == total_steps - 1:
                    print(f"Progress: {(step+1)}/{total_steps} time steps completed...")

        print(f"\nReady! File '{file_name}' was generated with {count} rows in time-linear order.")

    except Exception as e:
        print(f"Error generating the file: {e}")

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Satellite ephemeris generator for database testing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter 
    )

    
    parser.add_argument("-f", "--file", type=str, default="efemerides_datos.csv", 
                        help="Output CSV file name")
    parser.add_argument("-s", "--satellites", type=int, default=100, 
                        help="Number of satellites to simulate")
    parser.add_argument("-d", "--days", type=int, default=7, 
                        help="Days of data to generate")
    parser.add_argument("-i", "--interval", type=int, default=10, 
                        help="Time interval in seconds between records")
    parser.add_argument("-date", "--start-date", type=str, default="2026-01-01", 
                        help="Start date in YYYY-MM-DD format")
    parser.add_argument("-m", "--mode", choices=["distributed", "linear"], default="distributed",
                        help="Generation mode: distributed (per-satellite) or linear (time-ordered)")
     
    
    
    args = parser.parse_args()


    try:
        start_time_obj = datetime.strptime(args.start_date, "%Y-%m-%d")
    except ValueError:
        print("\n[!] Error: The date format is incorrect.")
        print("Please use YYYY-MM-DD (e.g., 2026-05-15).")
        sys.exit(1)

    if args.mode == "distributed":
        generate_data_per_satellite(args.file, args.satellites, args.days, args.interval, start_time_obj)
    else:
        generate_data_linear_time(args.file, args.satellites, args.days, args.interval, start_time_obj)
