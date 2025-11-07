from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
from typing import Dict, List, Tuple

class VRPSolver:
    """Vehicle Routing Problem solver using Google OR-Tools"""
    
    def __init__(self, data: Dict):
        self.data = data
        self.manager = None
        self.routing = None
        self.solution = None
        
    def create_data_model(self, distance_matrix: np.ndarray, 
                         time_matrix: np.ndarray,
                         time_windows: List[Tuple[int, int]],
                         service_times: List[int],
                         max_distance: float,
                         max_time: int) -> Dict:
        """Create data model for VRP"""
        
        data = {}
        data['distance_matrix'] = distance_matrix.astype(int).tolist()
        data['time_matrix'] = time_matrix.astype(int).tolist()
        data['time_windows'] = time_windows
        data['service_times'] = service_times
        data['num_vehicles'] = 1
        data['depot'] = 0
        data['vehicle_capacity'] = int(max_distance * 1000)  # Convert to meters
        data['vehicle_time_capacity'] = max_time
        
        return data
    
    def solve(self, time_limit: int = 30) -> Dict:
        """
        Solve the VRP problem
        
        Args:
            time_limit: Maximum time in seconds for optimization
            
        Returns:
            Solution dictionary with route and statistics
        """
        data = self.data
        
        # Create routing index manager
        self.manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        
        # Create routing model
        self.routing = pywrapcp.RoutingModel(self.manager)
        
        # Create distance callback
        def distance_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]
        
        distance_callback_index = self.routing.RegisterTransitCallback(distance_callback)
        self.routing.SetArcCostEvaluatorOfAllVehicles(distance_callback_index)
        
        # Add distance dimension
        self.routing.AddDimension(
            distance_callback_index,
            0,  # no slack
            data['vehicle_capacity'],  # vehicle maximum travel distance
            True,  # start cumul to zero
            'Distance'
        )
        
        # Create time callback
        def time_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            travel_time = data['time_matrix'][from_node][to_node]
            service_time = data['service_times'][from_node]
            return int(travel_time + service_time)
        
        time_callback_index = self.routing.RegisterTransitCallback(time_callback)
        
        # Add time dimension with time windows
        self.routing.AddDimension(
            time_callback_index,
            60,  # allow waiting time (60 minutes max)
            data['vehicle_time_capacity'],  # maximum time per vehicle
            False,  # don't force start cumul to zero
            'Time'
        )
        
        time_dimension = self.routing.GetDimensionOrDie('Time')
        
        # Add time window constraints
        for location_idx, time_window in enumerate(data['time_windows']):
            if location_idx == data['depot']:
                continue
            index = self.manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        
        # Add time windows for depot (start and end of day)
        depot_idx = data['depot']
        index = self.manager.NodeToIndex(depot_idx)
        time_dimension.CumulVar(index).SetRange(data['time_windows'][depot_idx][0], 
                                                data['time_windows'][depot_idx][1])
        
        # Instantiate route start and end times to produce feasible times
        for i in range(data['num_vehicles']):
            self.routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(self.routing.Start(i)))
            self.routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(self.routing.End(i)))
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = time_limit
        search_parameters.log_search = True
        
        # Solve the problem
        print("\n" + "="*60)
        print("Starting VRP Optimization...")
        print("="*60)
        
        self.solution = self.routing.SolveWithParameters(search_parameters)
        
        if self.solution:
            return self._extract_solution()
        else:
            print("\n✗ No solution found!")
            return None
    
    def _extract_solution(self) -> Dict:
        """Extract solution details"""
        data = self.data
        time_dimension = self.routing.GetDimensionOrDie('Time')
        distance_dimension = self.routing.GetDimensionOrDie('Distance')
        
        route = []
        total_distance = 0
        total_time = 0
        
        index = self.routing.Start(0)
        
        while not self.routing.IsEnd(index):
            node_index = self.manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            distance_var = distance_dimension.CumulVar(index)
            
            route.append({
                'location_index': node_index,
                'arrival_time': self.solution.Min(time_var),
                'cumulative_distance': self.solution.Min(distance_var)
            })
            
            index = self.solution.Value(self.routing.NextVar(index))
        
        # Add final depot return
        node_index = self.manager.IndexToNode(index)
        time_var = time_dimension.CumulVar(index)
        distance_var = distance_dimension.CumulVar(index)
        
        route.append({
            'location_index': node_index,
            'arrival_time': self.solution.Min(time_var),
            'cumulative_distance': self.solution.Min(distance_var)
        })
        
        total_distance = self.solution.Min(distance_var) / 1000  # Convert to km
        total_time = self.solution.Min(time_var)
        
        print("\n" + "="*60)
        print("✓ OPTIMIZATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Total Distance: {total_distance:.2f} km")
        print(f"Total Time: {total_time} minutes ({total_time/60:.2f} hours)")
        print(f"Locations Visited: {len(route) - 1}")  # Exclude depot return
        print("="*60 + "\n")
        
        return {
            'route': route,
            'total_distance_km': total_distance,
            'total_time_minutes': total_time,
            'num_locations': len(route) - 1
        }