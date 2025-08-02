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
    static_path = os.path.join(settings.STATICFILES_DIRS[0], 'nysc', 'json', 'nigeria_states.geojson.gz')
    with gzip.open(static_path, 'rt', encoding='utf-8') as f:
        return geojson.load(f)['features']

def get_state_from_coords(lat, lon):
    point = Point(float(lon), float(lat))  # [lon, lat] order
    for feature in load_states_geojson():
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            return feature['properties']['statename']
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