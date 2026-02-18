#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 30 14:20:41 2025

@author: rabea
"""

import json
import googlemaps
import pandas as pd
import os
from pathlib import Path
from json_repair import repair_json


## Set directory and ensure API Key is stored in session 
print("GMAPS_API_KEY:", os.getenv("GMAPS_API_KEY"))
os.chdir("/Users/yourname/Documents/GitHub/CSI_Database/Example")

# Get the key from environment variable
gmaps_api_key = os.getenv("GMAPS_API_KEY")

# Initialize the client
gmaps = googlemaps.Client(key=gmaps_api_key)

# Directories

# Directories (relative to current working directory)
complete_dir = Path("merged_outputs/complete")
coords_dir = Path("merged_outputs/coords") # new directory where dataset with coordinates gets stored


## Function 1: takes a location string and asks the Google Maps API to convert it into latitude and longitude coordinates

def geocode_location(location):
    try:
        result = gmaps.geocode(location)
        if result:
            lat = result[0]['geometry']['location']['lat']
            lng = result[0]['geometry']['location']['lng']
            return lat, lng
    except Exception as e:
        print(f"Error geocoding '{location}': {e}")
    return None, None

## Function 2: adds location data to existing dataset (contains geo_code locatioin from above)

def get_location(data):
    for entry in data:
        for project in entry.get('projects', []):
            raw_locations = project.get('location', '')
            locations = [loc.strip() for loc in raw_locations.split(';') if loc.strip()]
            
            for i, loc in enumerate(locations, start=1):
                lat, lng = geocode_location(loc)
                project[f'lat{i}'] = lat
                project[f'long{i}'] = lng
    return data


# Apply the functions to the datasets 

for input_file in complete_dir.glob("*.json"):
    rel_path = input_file.relative_to(complete_dir)
    coords_file = coords_dir / rel_path.with_suffix(".json")

    if coords_file.exists():
        print(f" Skipping existing file: {coords_file}")
        continue

    print(f" Processing: {input_file}")

    # Load the dataset
    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Process the dataset
    updated_dataset = get_location(dataset)  

    # Save the updated dataset
    output_filename = input_file.stem + "_coords.json"
    output_path = coords_dir / output_filename  
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_dataset, f, indent=2, ensure_ascii=False)

    print(f"✅ Processed: {input_file.name} → {output_filename}")