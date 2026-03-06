import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load GNN model and station data into memory at startup."""
    logger.info("Loading GNN model and station data...")
    from services.gnn_loader import get_tap_in_predictions
    from services.station_data import load_station_coordinates, get_station_list
    from services.intermediate_lookup import load_gtfs_lookup

    # Warm up caches
    load_station_coordinates()
    get_station_list()
    load_gtfs_lookup()

    # Run initial prediction to load model
    get_tap_in_predictions()

    logger.info("Startup complete.")
    yield


app = FastAPI(title="Hush API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
