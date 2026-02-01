"""
GNN Inference Module
Loads the trained GNN model and predicts tap-ins for MTA stations.
"""

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from datetime import datetime
from torch_geometric.nn import GCNConv


class GNN(nn.Module):
    """GNN model architecture (must match training)."""
    def __init__(self, in_dim, hidden_dim):
        super().__init__()
        self.conv1 = GCNConv(in_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.mlp = nn.Linear(hidden_dim, 1)

    def forward(self, x, edge_index):
        h = torch.relu(self.conv1(x, edge_index))
        h = torch.relu(self.conv2(h, edge_index))
        return self.mlp(h).squeeze()


class GNNPredictor:
    """Wrapper for GNN inference."""
    
    def __init__(self, model_path="model.pt", stats_path="stats.csv", 
                 cmplx_to_node_path="cmplx_to_node.csv",
                 edges_path="complex_edges.csv"):
        """Initialize predictor with model and mappings."""
        
        # Load model
        self.model = GNN(in_dim=3, hidden_dim=64)
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        self.model.eval()
        
        # Load station mappings
        self.cmplx_to_node = pd.read_csv(cmplx_to_node_path)
        self.node_to_cmplx = dict(zip(
            self.cmplx_to_node['node_id'], 
            self.cmplx_to_node['complex_id']
        ))
        self.cmplx_to_node_dict = dict(zip(
            self.cmplx_to_node['complex_id'],
            self.cmplx_to_node['node_id']
        ))
        
        # Load normalization stats
        self.stats = pd.read_csv(stats_path)
        self.stats_dict = dict(zip(
            self.stats['station_complex_id'],
            zip(self.stats['mean'], self.stats['std'])
        ))
        
        # Load edges
        edges_df = pd.read_csv(edges_path)
        edge_list = []
        for _, row in edges_df.iterrows():
            start = row['from_complex_id']
            end = row['to_complex_id']
            if start in self.cmplx_to_node_dict and end in self.cmplx_to_node_dict:
                start_node = self.cmplx_to_node_dict[start]
                end_node = self.cmplx_to_node_dict[end]
                edge_list.append([start_node, end_node])
                edge_list.append([end_node, start_node])  # Undirected
        
        self.edge_tensor = torch.tensor(edge_list, dtype=torch.long).T
        self.num_nodes = int(self.cmplx_to_node['node_id'].max() + 1)
    
    def predict(self, current_ridership_df: pd.DataFrame, current_time: datetime = None):
        """
        Run inference to predict next hour's tap-ins.
        
        Args:
            current_ridership_df: DataFrame with columns ['station_complex_id', 'ridership']
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Dict mapping station_complex_id → predicted_tap_ins
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Prepare input features
        X = torch.zeros(self.num_nodes, 3)
        
        hour = current_time.hour
        sin_hour = np.sin(2 * np.pi * hour / 24)
        cos_hour = np.cos(2 * np.pi * hour / 24)
        
        # Fill in features for stations with data
        for _, row in current_ridership_df.iterrows():
            cmplx_id = row['station_complex_id']
            ridership = row['ridership']
            
            if cmplx_id not in self.cmplx_to_node_dict:
                continue
            
            node_id = self.cmplx_to_node_dict[cmplx_id]
            
            # Normalize ridership
            if cmplx_id in self.stats_dict:
                mean, std = self.stats_dict[cmplx_id]
                ridership_norm = (ridership - mean) / (std + 1e-6)
            else:
                ridership_norm = 0.0
            
            X[node_id, 0] = ridership_norm
            X[node_id, 1] = sin_hour
            X[node_id, 2] = cos_hour
        
        # Run inference
        with torch.no_grad():
            y_pred = self.model(X, self.edge_tensor)
        
        # Denormalize predictions and convert to dict
        predictions = {}
        for node_id in range(self.num_nodes):
            if node_id in self.node_to_cmplx:
                cmplx_id = self.node_to_cmplx[node_id]
                pred_norm = y_pred[node_id].item()
                
                # Denormalize
                if cmplx_id in self.stats_dict:
                    mean, std = self.stats_dict[cmplx_id]
                    pred_tap_ins = pred_norm * std + mean
                else:
                    pred_tap_ins = pred_norm
                
                # Ensure non-negative
                predictions[cmplx_id] = max(0, pred_tap_ins)
        
        return predictions


# Singleton instance (cached)
_predictor_instance = None

def get_predictor():
    """Get or create GNN predictor singleton."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = GNNPredictor()
    return _predictor_instance
