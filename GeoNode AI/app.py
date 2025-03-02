from flask import Flask, render_template, request, jsonify
import numpy as np
import folium
import pandas as pd
import json
from sklearn.cluster import KMeans
from folium.plugins import HeatMap
import os
from sentinelsat import SentinelAPI, geojson_to_wkt
from datetime import date

app = Flask(__name__)

population_data = np.array([
    [36.1, 3.1, 100],
    [36.2, 3.2, 120],
    [36.3, 3.0, 150],
    [36.4, 3.3, 110],
    [36.5, 3.1, 130],
])


def find_optimal_nodes(data, n_nodes=2):
    coords = data[:, :2]
    kmeans = KMeans(n_clusters=n_nodes, random_state=42, n_init=10)
    kmeans.fit(coords)
    return kmeans.cluster_centers_


def calculate_coverage(data, nodes):
    coverage = [
        any(np.sqrt((point[0] - node[0]) ** 2 + (point[1] - node[1]) ** 2) < 0.2 for node in nodes)
        for point in data[:, :2]
    ]
    return sum(coverage) / len(data) * 100


def save_geojson(nodes, filename="static/optimal_nodes.geojson"):
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
             "properties": {"node_id": i + 1}}
            for i, (lat, lon) in enumerate(nodes)
        ]
    }
    with open(filename, "w") as f:
        json.dump(geojson_data, f)
    return filename


def fetch_sentinel2_data(start_date, end_date):
    USERNAME = "mouadbouh2@gmail.com"
    PASSWORD = "@Project2025@"
    API_URL = "https://apihub.copernicus.eu/dhus"
    api = SentinelAPI(USERNAME, PASSWORD, API_URL)
    geojson_geometry = {"type": "Polygon",
                        "coordinates": [[[3.1, 36.1], [3.3, 36.1], [3.3, 36.3], [3.1, 36.3], [3.1, 36.1]]]}
    footprint = geojson_to_wkt(geojson_geometry)

    try:
        products = api.query(footprint, date=(start_date, end_date), platformname="Sentinel-2",
                             cloudcoverpercentage=(0, 30))
        if products:
            product_id, product_info = next(iter(products.items()))
            api.download(product_id, directory_path="sentinel_data")
            return True, product_info['title']
        return False, "No images found."
    except Exception as e:
        return False, str(e)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        n_nodes = int(request.form.get("n_nodes", 2))
        start_date = request.form.get("start_date", "2024-01-01")
        end_date = request.form.get("end_date", "2024-02-01")

        sentinel_status, sentinel_message = fetch_sentinel2_data(start_date, end_date)

        optimal_nodes = find_optimal_nodes(population_data, n_nodes)
        coverage = calculate_coverage(population_data, optimal_nodes)

        # Create map
        m = folium.Map(location=[36.3, 3.2], zoom_start=12)
        HeatMap(population_data[:, :2], radius=25).add_to(m)
        for point in population_data:
            folium.CircleMarker([point[0], point[1]], radius=5, color="#3B82F6", fill=True,
                                popup=f"Elevation: {point[2]}m").add_to(m)
        for i, node in enumerate(optimal_nodes):
            folium.Marker(
                [node[0], node[1]],
                popup=f"Node #{i + 1}",
                icon=folium.Icon(color="red", icon="tower-cell", prefix="fa"),
                draggable=True
            ).add_to(m)

        # Get map HTML and inject drag-and-drop script
        map_html = m._repr_html_()
        drag_script = """
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            document.addEventListener("DOMContentLoaded", function() {
                let markers = document.querySelectorAll(".leaflet-marker-draggable");
                markers.forEach((marker, i) => {
                    marker.addEventListener("dragend", function(e) {
                        let latlng = marker._latlng;
                        window.parent.nodes[i] = [latlng.lat, latlng.lng];
                        window.parent.recalculate();
                    });
                });
            });
        </script>
        """
        full_html = map_html.replace("</body>", drag_script + "</body>")
        with open("static/geonode_map.html", "w") as f:
            f.write(full_html)

        geojson_file = save_geojson(optimal_nodes)
        node_df = pd.DataFrame(optimal_nodes, columns=['Latitude', 'Longitude'])
        node_df.to_csv("static/optimal_nodes.csv", index=False)

        return render_template(
            "index.html",
            map_url="/static/geonode_map.html",
            coverage=coverage,
            nodes=optimal_nodes.tolist(),
            sentinel_status=sentinel_status,
            sentinel_message=sentinel_message
        )

    return render_template("index.html", map_url=None, coverage=None, nodes=None)


@app.route("/update_coverage", methods=["POST"])
def update_coverage():
    data = request.get_json()
    nodes = np.array(data["nodes"])
    coverage = calculate_coverage(population_data, nodes)
    return jsonify({"coverage": coverage})


if __name__ == "__main__":
    app.run(debug=True)