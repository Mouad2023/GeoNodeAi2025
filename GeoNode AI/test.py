import numpy as np
import folium
import pandas as pd
import json
from sklearn.cluster import KMeans
from folium.plugins import HeatMap
import os
import time
from sentinelsat import SentinelAPI, geojson_to_wkt
from datetime import date

# Dummy data: population coordinates (lat, lon) and terrain elevation
population_data = np.array([
    [36.1, 3.1, 100],  # [latitude, longitude, elevation]
    [36.2, 3.2, 120],
    [36.3, 3.0, 150],
    [36.4, 3.3, 110],
    [36.5, 3.1, 130],
])


# Function to find optimal node locations using KMeans
def find_optimal_nodes(data, n_nodes=2):
    coords = data[:, :2]
    kmeans = KMeans(n_clusters=n_nodes, random_state=42, n_init=10)
    kmeans.fit(coords)
    return kmeans.cluster_centers_


# Function to calculate coverage percentage
def calculate_coverage(data, nodes):
    coverage = [
        any(
            np.sqrt((point[0] - node[0]) ** 2 + (point[1] - node[1]) ** 2) < 0.2
            for node in nodes
        )
        for point in data[:, :2]
    ]
    return sum(coverage) / len(data) * 100


# User-defined number of nodes
n_nodes = int(input("Enter the number of optimal nodes: "))
optimal_nodes = find_optimal_nodes(population_data, n_nodes)
coverage_percentage = calculate_coverage(population_data, optimal_nodes)
print(f"Proposed node locations: {optimal_nodes}")
print(f"Coverage percentage: {coverage_percentage:.2f}%")

# Save results to CSV
node_df = pd.DataFrame(optimal_nodes, columns=['Latitude', 'Longitude'])
node_df.to_csv("optimal_nodes.csv", index=False)
print("Node locations saved to 'optimal_nodes.csv'")


# Save results to GeoJSON
def save_geojson(nodes, filename="optimal_nodes.geojson"):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)]
                },
                "properties": {
                    "node_id": i + 1
                }
            }
            for i, (lat, lon) in enumerate(nodes)
        ]
    }
    with open(filename, "w") as f:
        json.dump(geojson_data, f)
    print(f"GeoJSON saved to '{filename}'")


save_geojson(optimal_nodes)

# Visualization
m = folium.Map(location=[36.3, 3.2], zoom_start=12)

# Heatmap for population density
HeatMap(population_data[:, :2], radius=25).add_to(m)

# Add population points
for point in population_data:
    folium.CircleMarker(
        location=[point[0], point[1]],
        radius=5,
        color="blue",
        fill=True,
        popup=f"Elevation: {point[2]}m"
    ).add_to(m)

# Add node locations
for node in optimal_nodes:
    folium.Marker(
        location=[node[0], node[1]],
        popup="Proposed Node Location",
        icon=folium.Icon(color="red")
    ).add_to(m)

m.save("geonode_map.html")
print("The map has been saved as 'geonode_map.html'")

# Sentinel-2 API Fetching with Sentinelsat
def fetch_sentinel2_data():
    # Sentinel API Credentials (Replace with your Copernicus SciHub credentials)
    USERNAME = "mouadbouh2@gmail.com"
    PASSWORD = "@Project2025@"
    API_URL = "https://apihub.copernicus.eu/dhus"  # Nouvelle URL correcte

    # Connect to the API
    api = SentinelAPI(USERNAME, PASSWORD, API_URL)

    # Define Search Area (GeoJSON format)
    geojson_geometry = {
        "type": "Polygon",
        "coordinates": [[[3.1, 36.1], [3.3, 36.1], [3.3, 36.3], [3.1, 36.3], [3.1, 36.1]]]
    }

    # Convert GeoJSON to WKT format (required by Sentinelsat)
    footprint = geojson_to_wkt(geojson_geometry)

    # Define Search Parameters
    try:
        products = api.query(
            footprint,
            date=(date(2024, 1, 1), date(2024, 2, 1)),  # Date range
            platformname="Sentinel-2",
            cloudcoverpercentage=(0, 30),  # Cloud coverage limit
        )

        # Check if products were found
        if products:
            print(f"Found {len(products)} Sentinel-2 images.")

            # Get the first product available
            product_id, product_info = next(iter(products.items()))
            print(f"Downloading: {product_info['title']}")

            # Download the first available product
            api.download(product_id, directory_path="sentinel_data")

            print("Sentinel-2 image downloaded successfully.")
        else:
            print("No Sentinel-2 images found for the given criteria.")

    except Exception as e:
        print(f"Error fetching Sentinel-2 data: {e}")


# Fetch Sentinel-2 data
fetch_sentinel2_data()
