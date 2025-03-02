1.Run the application: python app.py
 Open the browser at http://127.0.0.1:5000

2.Analyse node locations:
 A)Settings:
-Enter the number of nodes (1-10, default: 2).
-Specify a date range for Sentinel-2 data (e.g., 2024-01-01 to 2024-02-01).
-Click "Analyse" to process data and generate the map.

 B)Map Interaction:
-View population points (blue circles) and proposed nodes (red markers).
-Drag nodes to adjust positions; coverage updates automatically.

 C)Export:
-Download node locations as CSV or GeoJSON from the header.

3.Fetch Sentinel-2 Data:
-Replace the username and password(The app uses hardcoded credentials)

4.Acknowledgments:
-Built with Flask, Folium, and Sentinelsat.
-Uses open data from Copernicus Sentinel-2.