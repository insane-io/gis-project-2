import pandas as pd
import json
from datetime import datetime

# Load data
config = json.load(open('data/config.json'))
clients_df = pd.read_csv('data/clients.csv')

print("="*80)
print("CONSTRAINT ANALYSIS")
print("="*80)

# Working hours
work_start = datetime.strptime(config['sales_rep']['working_hours']['start'], '%H:%M')
work_end = datetime.strptime(config['sales_rep']['working_hours']['end'], '%H:%M')
work_duration = (work_end - work_start).total_seconds() / 60

print(f"\n1. WORKING HOURS: {work_start.strftime('%H:%M')} - {work_end.strftime('%H:%M')}")
print(f"   Total available time: {work_duration} minutes ({work_duration/60:.1f} hours)")

# Service time
total_service_time = clients_df['service_duration'].sum()
print(f"\n2. TOTAL SERVICE TIME: {total_service_time} minutes ({total_service_time/60:.1f} hours)")

# Travel time constraint
max_travel_minutes = config['sales_rep']['max_travel_hours'] * 60
print(f"\n3. MAX TRAVEL TIME: {max_travel_minutes} minutes ({max_travel_minutes/60:.1f} hours)")

# Time needed
total_time_needed = total_service_time + max_travel_minutes
print(f"\n4. MINIMUM TIME NEEDED: {total_time_needed} minutes ({total_time_needed/60:.1f} hours)")
print(f"   (Service: {total_service_time} min + Max Travel: {max_travel_minutes} min)")

# Check feasibility
print(f"\n5. FEASIBILITY CHECK:")
if total_time_needed > work_duration:
    print(f"   ❌ INFEASIBLE! Need {total_time_needed} min but only have {work_duration} min")
    print(f"   Shortage: {total_time_needed - work_duration} minutes ({(total_time_needed - work_duration)/60:.1f} hours)")
else:
    print(f"   ✓ FEASIBLE! Have enough time")

# Check time windows
print(f"\n6. TIME WINDOW CONFLICTS:")
for _, client in clients_df.iterrows():
    tw_start = datetime.strptime(client['time_window_start'], '%H:%M')
    tw_end = datetime.strptime(client['time_window_end'], '%H:%M')
    window_duration = (tw_end - tw_start).total_seconds() / 60
    
    if tw_start < work_start or tw_end > work_end:
        print(f"   ⚠️  {client['client_id']}: Window {client['time_window_start']}-{client['time_window_end']} "
              f"outside working hours!")
    elif window_duration < client['service_duration']:
        print(f"   ⚠️  {client['client_id']}: Window too short! "
              f"Need {client['service_duration']} min but window is {window_duration} min")

print("\n" + "="*80)