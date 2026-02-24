"""
GNN Inference Module
Loads the trained GNN model and predicts tap-ins for MTA stations.
"""

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from datetime import datetime
from torch_geometric.nn import SAGEConv
class DirSAGEEmbRes(nn.Module):
    """
    Directed SAGE with:
      - learnable node embedding
      - 2-layer message passing
      - residual connection to reduce over-smoothing
    """
    def __init__(self, num_nodes: int, in_dim: int, hidden_dim: int, emb_dim: int = 16):
        super().__init__()
        self.node_emb = nn.Embedding(num_nodes, emb_dim)

        d0 = in_dim + emb_dim

        # incoming edges
        self.in1 = SAGEConv(d0, hidden_dim)
        self.in2 = SAGEConv(hidden_dim, hidden_dim)

        # outgoing edges (reversed)
        self.out1 = SAGEConv(d0, hidden_dim)
        self.out2 = SAGEConv(hidden_dim, hidden_dim)

        self.lin = nn.Linear(2 * hidden_dim, 1)

    def forward(self, x, edge_in, edge_out):
        node_ids = torch.arange(x.size(0), device=x.device)
        x = torch.cat([x, self.node_emb(node_ids)], dim=1)

        h_in1 = torch.relu(self.in1(x, edge_in))
        h_in2 = torch.relu(self.in2(h_in1, edge_in))
        h_in  = h_in2 + h_in1  # residual

        h_out1 = torch.relu(self.out1(x, edge_out))
        h_out2 = torch.relu(self.out2(h_out1, edge_out))
        h_out  = h_out2 + h_out1  # residual

        h = torch.cat([h_in, h_out], dim=-1)
        return self.lin(h).squeeze(-1)

class GNNPredictor:
    """Wrapper for GNN inference."""
    
    def __init__(self, model_path="models/model.pt", stats_path="data/processed/stats.csv", 
                 ComplexNodes_path="data/processed/ComplexNodes.csv",
                 edges_path="data/processed/ComplexEdges.csv"):
        """Initialize predictor with model and mappings."""
        
        # Load station mappings
        self.ComplexNodes = pd.read_csv(ComplexNodes_path)
        self.node_to_cmplx = dict(zip(
            self.ComplexNodes['node_id'], 
            self.ComplexNodes['complex_id']
        ))
        self.ComplexNodes_dict = dict(zip(
            self.ComplexNodes['complex_id'],
            self.ComplexNodes['node_id']
        ))
        
        # Load normalization stats
        self.stats = pd.read_csv(stats_path)
        self.stats_dict = dict(zip(
            self.stats['station_complex_id'],
            zip(self.stats['mean'], self.stats['std'])
        ))
        
        # Load edges
                # Use mapping size as num_nodes (safer than max+1)
        self.num_nodes = len(self.ComplexNodes_dict)

        # Load edges (DIRECTED) and build both directions for dual-pass
        edges_df = pd.read_csv(edges_path)

        edge_in = []   # from -> to
        edge_out = []  # to -> from (reverse of edge_in)

        for _, row in edges_df.iterrows():
            start = row['from_complex_id']
            end = row['to_complex_id']
            if start in self.ComplexNodes_dict and end in self.ComplexNodes_dict:
                u = self.ComplexNodes_dict[start]
                v = self.ComplexNodes_dict[end]
                edge_in.append([u, v])
                edge_out.append([v, u])

        # Add self-loops to both edge sets (helps stability)
        for i in range(self.num_nodes):
            edge_in.append([i, i])
            edge_out.append([i, i])

        self.edge_in = torch.tensor(edge_in, dtype=torch.long).T
        self.edge_out = torch.tensor(edge_out, dtype=torch.long).T

        # Load model (must match training architecture + feature dim)
        self.model = DirSAGEEmbRes(num_nodes=self.num_nodes, in_dim=5, hidden_dim=64, emb_dim=16)
        self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
        self.model.eval()
    
    def predict(self, current_ridership_df: pd.DataFrame, current_time: datetime = None):
        """
        Run inference to predict next hour's tap-ins.
        
        Args:
            current_ridership_df: DataFrame with columns ['station_complex_id', 'ridership']
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Dict mapping station_complex_id -> predicted_tap_ins
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Prepare input features (ridership_norm, sin/cos hour, sin/cos dow)
        X = torch.zeros(self.num_nodes, 5)

        hour = current_time.hour
        sin_hour = np.sin(2 * np.pi * hour / 24)
        cos_hour = np.cos(2 * np.pi * hour / 24)

        dow = current_time.weekday()  # 0=Mon ... 6=Sun
        sin_dow = np.sin(2 * np.pi * dow / 7)
        cos_dow = np.cos(2 * np.pi * dow / 7)
        
        # Fill in features for stations with data
        for _, row in current_ridership_df.iterrows():
            cmplx_id = row['station_complex_id']
            ridership = row['ridership']
            
            if cmplx_id not in self.ComplexNodes_dict:
                continue
            
            node_id = self.ComplexNodes_dict[cmplx_id]
            
            # Normalize ridership
            if cmplx_id in self.stats_dict:
                mean, std = self.stats_dict[cmplx_id]
                ridership_norm = (ridership - mean) / (std + 1e-6)
            else:
                ridership_norm = 0.0
            
            X[node_id, 0] = ridership_norm
            X[node_id, 1] = sin_hour
            X[node_id, 2] = cos_hour
            X[node_id, 3] = sin_dow
            X[node_id, 4] = cos_dow
        
        # Run inference
        with torch.no_grad():
            y_pred = self.model(X, self.edge_in, self.edge_out)
        
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
