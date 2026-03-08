import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routers.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEPLOYED_FRONTEND_URL = os.getenv("DEPLOYED_FRONTEND_URL")

#---------------------------------------
# FastAPI Startup Events
#---------------------------------------
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

    # Run an initial prediction to load model
    get_tap_in_predictions()

    logger.info("Startup complete.")
    yield

#---------------------------------------
# Create FastAPI app
#---------------------------------------
app = FastAPI(title="Hush API", lifespan=lifespan)

# CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local frontend dev
        DEPLOYED_FRONTEND_URL,    # Deployed frontend URL on Render
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")
