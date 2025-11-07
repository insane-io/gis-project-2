import requests
import numpy as np
import json
from typing import List, Tuple, Dict

class DistanceMatrixCalculator:
    """Calculate distance and time matrix using OSRM"""
    
    def __init__(self, osrm_server: str = "http://router.project-osrm.org"):
        self.osrm_server = osrm_server
        
    def get_matrix(self, locations: List[Tuple[float, float]]) -> Dict:
        """
        Get distance and time matrix for all locations
        
        Args:
            locations: List of (lat, lon) tuples
            
        Returns:
            Dict with 'distances' (km) and 'durations' (minutes)
        """
        # Convert to lon,lat format for OSRM
        coordinates = ";".join([f"{lon},{lat}" for lat, lon in locations])
        
        # OSRM API endpoint
        url = f"{self.osrm_server}/table/v1/driving/{coordinates}"
        params = {
            "annotations": "distance,duration"
        }
        
        try:
            print(f"Fetching distance matrix for {len(locations)} locations...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data['code'] != 'Ok':
                raise Exception(f"OSRM Error: {data.get('message', 'Unknown error')}")
            
            # Extract matrices
            distances_m = np.array(data['distances'])  # meters
            durations_s = np.array(data['durations'])  # seconds
            
            # Convert to km and minutes
            distances_km = distances_m / 1000
            durations_min = durations_s / 60
            
            print(f"✓ Distance matrix calculated successfully")
            
            return {
                'distances': distances_km,
                'durations': durations_min,
                'locations': locations
            }
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching distance matrix: {e}")
            print("Falling back to Euclidean distance...")
            return self._euclidean_fallback(locations)
    
    def _euclidean_fallback(self, locations: List[Tuple[float, float]]) -> Dict:
        """Fallback to Euclidean distance if OSRM fails"""
        n = len(locations)
        distances = np.zeros((n, n))
        durations = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Approximate distance using Haversine
                    lat1, lon1 = locations[i]
                    lat2, lon2 = locations[j]
                    
                    # Simple Euclidean (rough approximation)
                    dlat = (lat2 - lat1) * 111  # 1 degree ≈ 111 km
                    dlon = (lon2 - lon1) * 111 * np.cos(np.radians(lat1))
                    dist = np.sqrt(dlat**2 + dlon**2)
                    
                    distances[i][j] = dist
                    durations[i][j] = dist / 40 * 60  # Assume 40 km/h, convert to minutes
        
        return {
            'distances': distances,
            'durations': durations,
            'locations': locations
        }
    
    def save_matrix(self, matrix_data: Dict, filepath: str):
        """Save matrix data to file"""
        np.savez(filepath, 
                 distances=matrix_data['distances'],
                 durations=matrix_data['durations'])
        print(f"✓ Matrix saved to {filepath}")
    
    def load_matrix(self, filepath: str) -> Dict:
        """Load matrix data from file"""
        data = np.load(filepath)
        return {
            'distances': data['distances'],
            'durations': data['durations']
        }