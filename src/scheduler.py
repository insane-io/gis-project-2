import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

class ScheduleGenerator:
    """Generate detailed schedule from VRP solution"""
    
    def __init__(self, solution: Dict, clients_df: pd.DataFrame, 
                 config: Dict, distance_matrix: np.ndarray,
                 time_matrix: np.ndarray):
        self.solution = solution
        self.clients_df = clients_df
        self.config = config
        self.distance_matrix = distance_matrix
        self.time_matrix = time_matrix
        
    def generate_schedule(self) -> pd.DataFrame:
        """Generate detailed timeline schedule"""
        
        route = self.solution['route']
        schedule = []
        
        # Parse working hours
        start_time_str = self.config['sales_rep']['working_hours']['start']
        start_time = datetime.strptime(start_time_str, '%H:%M')
        
        for i, stop in enumerate(route):
            location_idx = stop['location_index']
            arrival_minutes = stop['arrival_time']
            
            # Calculate actual time - FIXED: Convert to int
            arrival_time = start_time + timedelta(minutes=int(arrival_minutes))
            
            if location_idx == 0:  # Depot
                if i == 0:  # Start of day
                    schedule.append({
                        'sequence': i + 1,
                        'location': self.config['sales_rep']['start_location']['name'],
                        'client_id': 'DEPOT',
                        'address': 'Office',
                        'arrival_time': arrival_time.strftime('%H:%M'),
                        'service_start': arrival_time.strftime('%H:%M'),
                        'service_duration': 0,
                        'service_end': arrival_time.strftime('%H:%M'),
                        'activity': 'Depart Office',
                        'cumulative_distance_km': 0.0,
                        'distance_from_previous_km': 0.0,
                        'travel_time_from_previous_min': 0
                    })
                else:  # End of day - return to depot
                    prev_location_idx = route[i-1]['location_index']
                    distance = float(self.distance_matrix[prev_location_idx][location_idx])
                    travel_time = float(self.time_matrix[prev_location_idx][location_idx])
                    
                    schedule.append({
                        'sequence': i + 1,
                        'location': self.config['sales_rep']['start_location']['name'],
                        'client_id': 'DEPOT',
                        'address': 'Office',
                        'arrival_time': arrival_time.strftime('%H:%M'),
                        'service_start': '-',
                        'service_duration': 0,
                        'service_end': '-',
                        'activity': 'Return to Office',
                        'cumulative_distance_km': float(stop['cumulative_distance']) / 1000,
                        'distance_from_previous_km': distance,
                        'travel_time_from_previous_min': int(travel_time)
                    })
            else:  # Client location
                # Get client info
                client = self.clients_df.iloc[location_idx - 1]  # -1 because depot is 0
                
                # Calculate distances - FIXED: Explicit type conversion
                if i > 0:
                    prev_location_idx = route[i-1]['location_index']
                    distance = float(self.distance_matrix[prev_location_idx][location_idx])
                    travel_time = float(self.time_matrix[prev_location_idx][location_idx])
                else:
                    distance = 0.0
                    travel_time = 0.0
                
                # Service times - FIXED: Convert to int
                service_duration = int(client['service_duration'])
                service_start = arrival_time
                service_end = arrival_time + timedelta(minutes=service_duration)
                
                schedule.append({
                    'sequence': i + 1,
                    'location': client['client_name'],
                    'client_id': client['client_id'],
                    'address': f"({client['latitude']:.4f}, {client['longitude']:.4f})",
                    'arrival_time': arrival_time.strftime('%H:%M'),
                    'service_start': service_start.strftime('%H:%M'),
                    'service_duration': service_duration,
                    'service_end': service_end.strftime('%H:%M'),
                    'activity': f'Meeting ({client["priority"]} Priority)',
                    'cumulative_distance_km': float(stop['cumulative_distance']) / 1000,
                    'distance_from_previous_km': distance,
                    'travel_time_from_previous_min': int(travel_time)
                })
        
        df_schedule = pd.DataFrame(schedule)
        return df_schedule
    
    def print_schedule(self, schedule_df: pd.DataFrame):
        """Print formatted schedule"""
        print("\n" + "="*80)
        print(f"DAILY SCHEDULE - {self.config['sales_rep']['name']}")
        print("="*80)
        
        for _, row in schedule_df.iterrows():
            if row['client_id'] == 'DEPOT':
                if row['sequence'] == 1:
                    print(f"\n{row['arrival_time']} | 🏢 {row['activity']}")
                else:
                    print(f"\n{row['arrival_time']} | 🏁 {row['activity']}")
                    print(f"           Distance: {row['distance_from_previous_km']:.1f} km | "
                          f"Travel Time: {row['travel_time_from_previous_min']} min")
            else:
                print(f"\n{row['arrival_time']} | 📍 Arrive at {row['location']}")
                print(f"           Distance from previous: {row['distance_from_previous_km']:.1f} km | "
                      f"Travel: {row['travel_time_from_previous_min']} min")
                print(f"{row['service_start']} | 🤝 Meeting Start ({row['service_duration']} min) - {row['activity']}")
                print(f"{row['service_end']} | ✓ Meeting End, Depart")
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Clients Visited: {len(schedule_df[schedule_df['client_id'] != 'DEPOT'])}")
        print(f"Total Distance: {schedule_df['cumulative_distance_km'].max():.2f} km")
        print(f"Total Travel Time: {schedule_df['travel_time_from_previous_min'].sum()} minutes")
        print(f"Total Service Time: {schedule_df['service_duration'].sum()} minutes")
        print(f"Day Duration: {schedule_df.iloc[0]['arrival_time']} - {schedule_df.iloc[-1]['arrival_time']}")
        print("="*80 + "\n")
    
    def export_to_csv(self, schedule_df: pd.DataFrame, filepath: str):
        """Export schedule to CSV"""
        schedule_df.to_csv(filepath, index=False)
        print(f"✓ Schedule exported to {filepath}")