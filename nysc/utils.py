import json
from pathlib import Path
import os
import logging
import gzip
import geojson
from shapely.geometry import shape, Point
from django.conf import settings

logger = logging.getLogger(__name__)

# Define BASE_DIR to match settings.py
BASE_DIR = Path(__file__).resolve().parent.parent

def load_states_geojson():
    static_path = os.path.join(BASE_DIR, 'static', 'nysc', 'json', 'nigeria_states.geojson.gz')
    if not os.path.exists(static_path):
        static_path = os.path.join(settings.STATIC_ROOT, 'nysc', 'json', 'nigeria_states.geojson.gz')
        if not os.path.exists(static_path):
            logger.error(f"GeoJSON file not found at {static_path}")
            return []
    try:
        with gzip.open(static_path, 'rt', encoding='utf-8') as f:
            data = geojson.load(f)
            logger.debug(f"Loaded GeoJSON with {len(data['features'])} features")
            return data['features']
    except Exception as e:
        logger.error(f"Error loading GeoJSON: {str(e)}", exc_info=True)
        return []

def get_state_from_coords(lat, lon):
    point = Point(float(lon), float(lat))  # [lon, lat] order for Shapely
    logger.debug(f"Checking point: {point} with coords {lat}, {lon}")
    features = load_states_geojson()
    if not features:
        logger.error("No GeoJSON features loaded")
        return None

    for feature in features:
        if 'geometry' in feature and feature['geometry']:
            try:
                polygon = shape(feature['geometry'])
                # Round coordinates to 4 decimal places for consistency
                point_rounded = Point(round(float(lon), 4), round(float(lat), 4))
                if polygon.contains(point_rounded):
                    state = feature['properties'].get('statename')
                    logger.info(f"Found state: {state} for coordinates {lat}, {lon}")
                    return state
            except Exception as e:
                logger.error(f"Error processing polygon for feature {feature.get('properties', {})}: {str(e)}", exc_info=True)
                continue
    logger.warning(f"No state found for coordinates: {lat}, {lon}")
    return None

# Load LGA data from JSON file
lga_json_path = os.path.join(BASE_DIR, 'static', 'nysc', 'json', 'nigeria_lgas.json')
lgasData = {}
try:
    with open(lga_json_path, 'r', encoding='utf-8') as f:
        lgasData = json.load(f)
    logger.info(f"LGA data loaded successfully from {lga_json_path}")
except FileNotFoundError:
    logger.error(f"LGA JSON file not found at {lga_json_path}")
except json.JSONDecodeError:
    logger.error(f"Invalid JSON in {lga_json_path}")