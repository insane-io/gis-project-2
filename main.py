#!/usr/bin/env python3
"""
Sales Route Optimizer - Main Execution Script
Optimizes daily routes for sales representatives using VRP
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append('src')

from distance_matrix import DistanceMatrixCalculator
from vrp_solver import VRPSolver
from scheduler import ScheduleGenerator
from visualizer import RouteVisualizer

def load_config(config_path='data/config.json'):
    """Load configuration file"""
    with open(config_path, 'r') as f:
        return json.load(f)

def load_clients(clients_path='data/clients.csv'):
    """Load client data"""
    df = pd.read_csv(clients_path)
    print(f"✓ Loaded {len(df)} clients from {clients_path}")
    return df

def convert_time_to_minutes(time_str, base_time_str='09:00'):
    """Convert HH:MM to minutes from base time"""
    base = datetime.strptime(base_time_str, '%H:%M')
    target = datetime.strptime(time_str, '%H:%M')
    diff = (target - base).total_seconds() / 60
    return int(diff)

def main():
    """Main execution function"""
    
    print("\n" + "="*80)
    print("🚗 SALES ROUTE OPTIMIZER - VRP SOLVER")
    print("="*80 + "\n")
    
    # Step 1: Load data
    print("Step 1: Loading configuration and client data...")
    config = load_config()
    clients_df = load_clients()
    
    # Step 2: Prepare locations
    print("\nStep 2: Preparing location data...")
    depot_location = (
        config['sales_rep']['start_location']['latitude'],
        config['sales_rep']['start_location']['longitude']
    )
    
    client_locations = list(zip(clients_df['latitude'], clients_df['longitude']))
    all_locations = [depot_location] + client_locations
    
    print(f"✓ Total locations: {len(all_locations)} (1 depot + {len(client_locations)} clients)")
    
    # Step 3: Calculate distance matrix
    print("\nStep 3: Calculating distance and time matrix...")
    dm_calculator = DistanceMatrixCalculator(config['osrm_server'])
    matrix_data = dm_calculator.get_matrix(all_locations)
    
    distance_matrix = matrix_data['distances']
    time_matrix = matrix_data['durations']
    
    print(f"✓ Matrix size: {distance_matrix.shape}")
    
    # Optional: Save matrix for future use
    dm_calculator.save_matrix(matrix_data, 'output/distance_matrix.npz')
    
    # Step 4: Prepare VRP data
    print("\nStep 4: Preparing VRP model data...")
    
    # Convert time windows to minutes from start of day
    base_time = config['sales_rep']['working_hours']['start']
    
    time_windows = [(0, 0)]  # Depot time window (placeholder)
    service_times = [0]  # Depot service time
    
    for _, client in clients_df.iterrows():
        tw_start = convert_time_to_minutes(client['time_window_start'], base_time)
        tw_end = convert_time_to_minutes(client['time_window_end'], base_time)
        time_windows.append((tw_start, tw_end))
        service_times.append(client['service_duration'])
    
    # Set depot time window (full working day)
    work_start = 0
    work_end = convert_time_to_minutes(
        config['sales_rep']['working_hours']['end'], 
        base_time
    )
    time_windows[0] = (work_start, work_end)
    
    # Max capacities
    max_distance = config['sales_rep']['max_distance_km']
    max_time = config['sales_rep']['max_travel_hours'] * 60  # Convert to minutes
    
    print(f"✓ Time windows defined for {len(time_windows)} locations")
    print(f"✓ Working hours: {config['sales_rep']['working_hours']['start']} - "
          f"{config['sales_rep']['working_hours']['end']}")
    print(f"✓ Max distance: {max_distance} km")
    print(f"✓ Max travel time: {max_time} minutes")
    
    # Step 5: Solve VRP
    print("\nStep 5: Solving Vehicle Routing Problem...")
    
    solver = VRPSolver(None)
    data = solver.create_data_model(
        distance_matrix=distance_matrix * 1000,  # Convert to meters for OR-Tools
        time_matrix=time_matrix,
        time_windows=time_windows,
        service_times=service_times,
        max_distance=max_distance,
        max_time=work_end  # Use full working day as max time
    )
    
    solver.data = data
    solution = solver.solve(
        time_limit=config['optimization_settings']['time_limit_seconds']
    )
    
    if not solution:
        print("\n✗ Failed to find a solution!")
        print("Possible reasons:")
        print("  - Time windows too restrictive")
        print("  - Too many clients for one day")
        print("  - Distance/time limits too tight")
        return
    
    # Step 6: Generate schedule
    print("\nStep 6: Generating detailed schedule...")
    schedule_gen = ScheduleGenerator(
        solution=solution,
        clients_df=clients_df,
        config=config,
        distance_matrix=distance_matrix,
        time_matrix=time_matrix
    )
    
    schedule_df = schedule_gen.generate_schedule()
    schedule_gen.print_schedule(schedule_df)
    
    # Export schedule
    schedule_gen.export_to_csv(schedule_df, 'output/daily_schedule.csv')
    
    # Step 7: Visualize
    print("\nStep 7: Creating visualizations...")
    visualizer = RouteVisualizer(
        solution=solution,
        clients_df=clients_df,
        config=config,
        schedule_df=schedule_df
    )
    
    visualizer.create_map('output/route_map.html')
    visualizer.create_gantt_chart()
    
    # Final summary
    print("\n" + "="*80)
    print("✅ OPTIMIZATION COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nGenerated files:")
    print("  📄 output/daily_schedule.csv - Detailed schedule")
    print("  🗺️  output/route_map.html - Interactive map")
    print("  💾 output/distance_matrix.npz - Distance matrix")
    print("\nTo view the map, open: output/route_map.html in your browser")
    print("="*80 + "\n")

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Execution interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()