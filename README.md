# Hush — MTA Sensory-Safe Router

A routing app for the NYC subway that finds the **quietest** route, not just the fastest. Uses a Graph Neural Network trained on MTA ridership data to predict station congestion and score routes on a 0–10 quiet scale.

## How It Works

1. **GNN Prediction** — A two-layer GCN model (`models/model.pt`) takes current ridership data and time-of-day features, then predicts next-hour tap-ins for every station complex.
2. **Congestion Scoring** — Predicted tap-ins are percentile-ranked across all stations. Each station gets a congestion score (0.0–1.0), and route scores are computed as a weighted average with distance decay.
3. **Route Selection** — The Google Routes API returns up to 3 subway/rail routes between two stations. Each route is assigned a quiet score (0 = busy, 10 = quiet) so users can choose the calmest option.

## Quick Start

### Prerequisites
- Python 3.12+
- A Google Cloud API key with the Routes API enabled

### Setup

```bash
# 1. Create a .env file with your API key
echo "ROUTES_API_KEY=your_key_here" > .env

# 2. Run the start script (creates venv, installs deps, launches app)
bash start_app.sh
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

Open **http://localhost:8501** in your browser.

## Project Structure

```
hush/
├── src/
│   ├── app.py                 # Streamlit frontend & routing logic
│   ├── gnn_inference.py       # GNN model loading & prediction
│   └── congestion_scorer.py   # Quiet score calculation
├── models/
│   └── model.pt               # Trained GCN model weights
├── data/
│   ├── raw/                   # MTA ridership CSVs, GTFS files
│   └── processed/             # Station mappings, edges, stats
├── training/
│   ├── test_train.ipynb       # Model training notebook
│   ├── test_eval.ipynb        # Model evaluation notebook
│   └── preprocessing/         # Data preprocessing scripts
├── start_app.sh               # One-command setup & launch
├── requirements.txt
└── README.md
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Streamlit, Pydeck |
| ML Model | PyTorch, PyTorch Geometric (GCN) |
| Routing | Google Routes API |
| Data | Pandas, NumPy, SciPy |

## Data

- **MTA Hourly Ridership (2020–2025)** — tap-in counts per station per hour
- **GTFS Static** — stop coordinates, trips, stop times
- **Processed** — station complex graph edges, node mappings, normalization stats