import logging
import os
from flask import Flask
from flask_cors import CORS
from routers.routes import routes_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEPLOYED_FRONTEND_URL = os.getenv("DEPLOYED_FRONTEND_URL", "https://hush-d5dr.onrender.com")

#---------------------------------------
# Create Flask app
#---------------------------------------
def create_app():
    app = Flask(__name__)

    CORS(app, origins=[
        "http://localhost:5173",  # Local frontend dev
        DEPLOYED_FRONTEND_URL,    # Deployed frontend URL on Render
    ], methods=["GET"])

    app.register_blueprint(routes_bp, url_prefix="/api")

    # Warm up caches at startup
    with app.app_context():
        logger.info("Loading GNN model and station data...")
        from services.gnn_loader import get_tap_in_predictions
        from services.station_data import load_station_coordinates, get_station_list
        from services.intermediate_lookup import load_gtfs_lookup

        load_station_coordinates()
        get_station_list()
        load_gtfs_lookup()
        get_tap_in_predictions()
        logger.info("Startup complete.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
