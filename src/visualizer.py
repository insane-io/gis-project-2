import folium
from folium import plugins
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime

class RouteVisualizer:
    """Create interactive map visualization of optimized route"""
    
    def __init__(self, solution: Dict, clients_df: pd.DataFrame, 
                 config: Dict, schedule_df: pd.DataFrame):
        self.solution = solution
        self.clients_df = clients_df
        self.config = config
        self.schedule_df = schedule_df
        
    def create_map(self, filepath: str = 'output/route_map.html'):
        """Create interactive Folium map"""
        
        # Get depot location
        depot_lat = self.config['sales_rep']['start_location']['latitude']
        depot_lon = self.config['sales_rep']['start_location']['longitude']
        
        # Create map centered on depot
        m = folium.Map(
            location=[depot_lat, depot_lon],
            zoom_start=11,
            tiles='OpenStreetMap'
        )
        
        # Add depot marker
        folium.Marker(
            location=[depot_lat, depot_lon],
            popup=folium.Popup(
                f"<b>🏢 OFFICE - START/END</b><br>"
                f"{self.config['sales_rep']['start_location']['name']}<br>"
                f"Rep: {self.config['sales_rep']['name']}",
                max_width=250
            ),
            icon=folium.Icon(color='red', icon='home', prefix='fa'),
            tooltip='Office (Depot)'
        ).add_to(m)
        
        # Add client markers with route sequence
        route = self.solution['route']
        route_coords = []
        
        for i, stop in enumerate(route):
            location_idx = stop['location_index']
            
            if location_idx == 0:  # Depot
                route_coords.append([depot_lat, depot_lon])
            else:
                client = self.clients_df.iloc[location_idx - 1]
                lat, lon = client['latitude'], client['longitude']
                route_coords.append([lat, lon])
                
                # Get schedule info for this stop
                schedule_info = self.schedule_df[
                    self.schedule_df['client_id'] == client['client_id']
                ].iloc[0]
                
                # Color based on priority
                color_map = {
                    'High': 'red',
                    'Medium': 'orange',
                    'Low': 'blue'
                }
                color = color_map.get(client['priority'], 'gray')
                
                # Create detailed popup
                popup_html = f"""
                <div style="font-family: Arial; width: 280px;">
                    <h4 style="margin: 0; color: #333;">
                        #{schedule_info['sequence']-1} - {client['client_name']}
                    </h4>
                    <hr style="margin: 5px 0;">
                    <table style="width: 100%; font-size: 12px;">
                        <tr><td><b>Client ID:</b></td><td>{client['client_id']}</td></tr>
                        <tr><td><b>Priority:</b></td><td><span style="color: {color};">⬤ {client['priority']}</span></td></tr>
                        <tr><td><b>Arrival:</b></td><td>{schedule_info['arrival_time']}</td></tr>
                        <tr><td><b>Meeting:</b></td><td>{schedule_info['service_start']} - {schedule_info['service_end']}</td></tr>
                        <tr><td><b>Duration:</b></td><td>{schedule_info['service_duration']} min</td></tr>
                        <tr><td><b>Time Window:</b></td><td>{client['time_window_start']} - {client['time_window_end']}</td></tr>
                        <tr><td><b>Distance:</b></td><td>{schedule_info['distance_from_previous_km']:.1f} km from previous</td></tr>
                        <tr><td><b>Travel Time:</b></td><td>{schedule_info['travel_time_from_previous_min']} min</td></tr>
                    </table>
                </div>
                """
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(
                        color=color, 
                        icon='briefcase', 
                        prefix='fa'
                    ),
                    tooltip=f"#{schedule_info['sequence']-1}: {client['client_name']}"
                ).add_to(m)
                
                # Add sequence number label
                folium.Marker(
                    location=[lat, lon],
                    icon=folium.DivIcon(html=f"""
                        <div style="
                            font-size: 14px; 
                            font-weight: bold; 
                            color: white; 
                            background-color: {color}; 
                            border-radius: 50%; 
                            width: 25px; 
                            height: 25px; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center;
                            border: 2px solid white;
                            box-shadow: 0 0 5px rgba(0,0,0,0.5);
                        ">
                            {schedule_info['sequence']-1}
                        </div>
                    """)
                ).add_to(m)
        
        # Draw route line
        folium.PolyLine(
            route_coords,
            color='blue',
            weight=3,
            opacity=0.7,
            popup=f"Total Distance: {self.solution['total_distance_km']:.2f} km"
        ).add_to(m)
        
        # Add arrows to show direction
        plugins.AntPath(
            route_coords,
            color='blue',
            weight=3,
            opacity=0.6,
            delay=1000
        ).add_to(m)
        
        # Add legend
        legend_html = f"""
        <div style="
            position: fixed; 
            bottom: 50px; 
            left: 50px; 
            width: 280px; 
            background-color: white; 
            border: 2px solid grey; 
            z-index: 9999; 
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
        ">
            <h4 style="margin: 0 0 10px 0;">📊 Route Summary</h4>
            <hr style="margin: 5px 0;">
            <b>Rep:</b> {self.config['sales_rep']['name']}<br>
            <b>Clients Visited:</b> {self.solution['num_locations']}<br>
            <b>Total Distance:</b> {self.solution['total_distance_km']:.2f} km<br>
            <b>Total Time:</b> {self.solution['total_time_minutes']/60:.2f} hours<br>
            <b>Max Distance:</b> {self.config['sales_rep']['max_distance_km']} km<br>
            <b>Max Travel:</b> {self.config['sales_rep']['max_travel_hours']} hours<br>
            <hr style="margin: 5px 0;">
            <b>Legend:</b><br>
            🏢 <span style="color: red;">Red</span> - Office/Depot<br>
            ⬤ <span style="color: red;">Red</span> - High Priority<br>
            ⬤ <span style="color: orange;">Orange</span> - Medium Priority<br>
            ⬤ <span style="color: blue;">Blue</span> - Low Priority<br>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        m.save(filepath)
        print(f"✓ Interactive map saved to {filepath}")
        
        return m
    
    def create_gantt_chart(self):
        """Create simple text-based Gantt chart"""
        print("\n" + "="*80)
        print("GANTT CHART - TIME ALLOCATION")
        print("="*80)
        
        working_start = datetime.strptime(
            self.config['sales_rep']['working_hours']['start'], '%H:%M'
        )
        
        for _, row in self.schedule_df.iterrows():
            if row['client_id'] != 'DEPOT' or row['sequence'] == 1:
                arrival = datetime.strptime(row['arrival_time'], '%H:%M')
                
                # Calculate minutes from start
                minutes_from_start = int((arrival - working_start).total_seconds() / 60)
                bar_length = minutes_from_start // 10  # Scale: 1 char = 10 min
                
                bar = '─' * bar_length + '●'
                
                if row['client_id'] == 'DEPOT':
                    print(f"{row['arrival_time']} {bar} 🏢 START")
                else:
                    duration_bar = '█' * (row['service_duration'] // 10)
                    print(f"{row['arrival_time']} {bar}{duration_bar} {row['location'][:30]}")
        
        print("="*80 + "\n")