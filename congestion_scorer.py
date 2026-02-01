"""
Congestion Scoring Module
Calculates quiet scores for routes based on predicted tap-ins.
"""

import numpy as np
import pandas as pd
from scipy.stats import percentileofscore


class CongestionScorer:
    """Calculates congestion and quiet scores."""
    
    def __init__(self, predictions: dict):
        """
        Initialize scorer with GNN predictions.
        
        Args:
            predictions: Dict mapping station_complex_id → predicted_tap_ins
        """
        self.predictions = predictions
        self.all_tap_ins = list(predictions.values())
        
        # Load station name -> complex ID mapping from stop_to_complex.csv
        self.station_name_to_id = {}
        try:
            mapping_df = pd.read_csv("stop_to_complex.csv")
            for _, row in mapping_df.iterrows():
                name = str(row['Stop Name']).strip()
                complex_id = int(row['Complex ID'])
                self.station_name_to_id[name] = complex_id
        except Exception as e:
            print(f"Warning: Could not load station name mapping: {e}")
    
    def get_station_congestion_score(self, station_complex_id: int) -> float:
        """
        Calculate congestion score for a station (0.0 = empty, 1.0 = packed).
        Uses percentile ranking among all stations.
        
        Args:
            station_complex_id: Station complex ID
        
        Returns:
            Congestion score (0.0 to 1.0)
        """
        if station_complex_id not in self.predictions:
            return 0.5  # Default to moderate if no data
        
        tap_ins = self.predictions[station_complex_id]
        
        # Percentile among all stations
        percentile = percentileofscore(self.all_tap_ins, tap_ins) / 100.0
        
        return percentile
    
    def calculate_route_quiet_score(self, route: dict) -> int:
        """
        Calculate quiet score (0-10) for a route using station congestion.
        
        Args:
            route: Route dict with 'steps' list
        
        Returns:
            Quiet score (0 = very busy, 10 = very quiet)
        """
        congestion_scores = []
        
        for step in route.get('steps', []):
            if step['type'] != 'transit':
                continue
            
            # Extract station names from departure/arrival
            departure_name = step.get('departure', '').strip()
            arrival_name = step.get('arrival', '').strip()
            
            # Try to find matching station complex IDs
            dep_id = self._find_station_id(departure_name)
            arr_id = self._find_station_id(arrival_name)
            
            # Get congestion scores for both stations
            if dep_id is not None:
                dep_congestion = self.get_station_congestion_score(dep_id)
                congestion_scores.append(dep_congestion)
            
            if arr_id is not None:
                arr_congestion = self.get_station_congestion_score(arr_id)
                congestion_scores.append(arr_congestion)
        
        if not congestion_scores:
            # Fallback: use median congestion

            return 5
        
        # Average congestion across route
        route_congestion = np.mean(congestion_scores)
        
        # Convert to quiet score (invert: high congestion = low quiet score)
        quiet_score = int((1.0 - route_congestion) * 10)
        
        # Clamp to 0-10
        return max(0, min(10, quiet_score))
    
    def _find_station_id(self, station_name: str) -> int:
        """
        Find station_complex_id from station name using fuzzy matching.
        
        Args:
            station_name: Station name from Google Maps (e.g., "Times Sq-42 St")
        
        Returns:
            station_complex_id or None if not found
        """
        if not station_name:
            return None
        
        # Direct match
        if station_name in self.station_name_to_id:
            return self.station_name_to_id[station_name]
        
        # Normalize for fuzzy matching
        clean_query = station_name.lower().replace('-', ' ').replace('  ', ' ')
        
        # Try fuzzy matching
        for name, complex_id in self.station_name_to_id.items():
            clean_name = name.lower().replace('-', ' ').replace('  ', ' ')
            
            # Check if names are similar enough
            if clean_query in clean_name or clean_name in clean_query:
                return complex_id
            
            # Check if key parts match (first few words)
            query_parts = clean_query.split()[:2]
            name_parts = clean_name.split()[:2]
            if query_parts and name_parts and query_parts[0] == name_parts[0]:
                return complex_id
        
        return None
    
    def calculate_route_quiet_score_with_stations(self, station_complex_ids: list) -> int:
        """
        Calculate quiet score given explicit list of station complex IDs.
        Uses Method 5: Hybrid Percentile + Decay.
        
        Args:
            station_complex_ids: List of station complex IDs in order
        
        Returns:
            Quiet score (0-10)
        """
        if not station_complex_ids:
            return 5
        
        congestion_contributions = []
        
        for i, station_id in enumerate(station_complex_ids):
            # Station congestion
            station_congestion = self.get_station_congestion_score(station_id)
            
            # Distance decay (exponential)
            # More recent stations in route contribute more
            stops_from_start = i
            decay = np.exp(-stops_from_start / 6)  # Avg journey ~6 stops
            
            contribution = station_congestion * decay
            congestion_contributions.append(contribution)
        
        # Weighted average
        route_congestion = np.mean(congestion_contributions)
        
        # Convert to quiet score (invert)
        quiet_score = int((1.0 - route_congestion) * 10)
        
        return max(0, min(10, quiet_score))
