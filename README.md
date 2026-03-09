# Hush - MTA Sensory-Safe Router

A routing app for the NYC subway that finds the **quietest** route, not just the fastest. Uses a Graph Neural Network trained on MTA ridership data to predict station congestion and score routes on a 0-10 quiet scale.

## How It Works

1. **GNN Prediction** - A `DirSAGEEmbRes` GNN takes current ridership data and time-of-day features (including peak-hour flags), then predicts next-hour tap-ins for every station complex.
2. **Congestion Scoring** - Predicted tap-ins are percentile-ranked across all stations. Each station gets a congestion score (0.0–1.0), and route scores are computed as a weighted average with distance decay.
3. **Route Selection** - The Google Routes API returns up to 3 subway/rail routes between two stations. Each route is assigned a quiet score (0 = busy, 10 = quiet) so users can choose the calmest option.

## Architecture

```
frontend/   React + TypeScript (Vite)  ->  deployed on Render (Static Site)
backend/    Flask + Gunicorn           ->  deployed on Render (Docker Web Service)
```

The frontend calls the backend REST API (`/api/stations`, `/api/routes`, `/api/station-coords`). The backend loads the GNN model at startup and serves predictions on demand.

## Quick Start

### Prerequisites
- Docker + Docker Compose
- A Google Cloud API key with the Routes API enabled

### Local Development

```bash
# 1. Create backend/.env with your API key
echo "ROUTES_API_KEY=your_key_here" > backend/.env

# 2. Start the backend
docker compose up

# 3. Start the frontend (separate terminal)
cd frontend
npm install
npm run dev
```

- Backend: **http://localhost:8000**
- Frontend: **http://localhost:5173**

## Training

The GNN is trained on MTA hourly ridership data (2020-2024). To retrain:

```bash
cd training

# 1. Preprocess raw CSVs into train/val/test parquet splits
python preprocess.py

# 2. Open train.ipynb and run all cells (sweep over 8 hyperparameter configs)
# 3. Open evaluate.ipynb to pick and export the best model to models/best_model.pt
```

**Split strategy:**
- 2020–2022: train
- 2023: val  
- 2024: test

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, Vite, deck.gl, MapLibre GL |
| Backend | Flask, Gunicorn, Flask-CORS |
| ML Model | PyTorch, PyTorch Geometric (`DirSAGEEmbRes` GNN) |
| Routing | Google Routes API |
| Data | Pandas, NumPy, SciPy |
| Deployment | Render (Docker + Static Site) |

## Data

- **MTA Hourly Ridership (2020–2024)** - tap-in counts per station per hour
- **GTFS Static** - stop coordinates, trips, stop times
- **Processed** - station complex graph edges, node mappings, normalization stats, pre-aggregated ridership by hour
