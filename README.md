### \#\# Updated Project Plan v2.1

I've revised the logic for the Historical Trend and the Smart Radius as we discussed. The core goal remains the same.

**Goal:** To create an advanced, interactive heatmap that visualizes NYC 311 complaint data, providing context-aware insights by balancing per-capita rates with complaint volume.

-----

### \#\#\#\# Core Visualization Logic

This section covers the backend data processing that powers the map's core metric.

#### The "Weighted Impact Score" Engine

  * **Concept:** To provide a more nuanced view than simple per-capita or raw counts, the map will be colored based on a **Weighted Impact Score**. This score identifies areas that have both a high rate of complaints relative to their population *and* a significant volume of complaints, filtering out misleading noise from low-population or low-complaint zones.
  * **Implementation (Backend Scheduled Job):**
    1.  A daily job fetches the 30-day complaint count (`complaints`) and the stored estimated population (`population`) for every H3 hexagon.
    2.  It calculates the new metric using the formula: `Impact Score = (complaints / population) * log(complaints + 1)`.
    3.  It then calculates percentile boundaries (e.g., Low, Medium, High) based on the city-wide distribution of these new scores and saves them for the API.

#### The Historical Trend Logic **(REVISED)**

  * **Concept:** To provide seasonal context, the system will compare the current period to the same period from the previous year. This data will be shown on-demand to keep the main map view clean.
  * **Implementation (API on User Interaction):**
    1.  When a user clicks on a hexagon, the API fetches complaint data for two rolling 30-day periods: the most recent 30 days and the same 30-day window from the previous year.
    2.  It calculates the year-over-year percentage change to determine a trend status. **To prevent misleading alerts from low-volume areas, both a relative and an absolute threshold must be met.**
          * **Improving:** `< -10%` change AND `> 5` fewer complaints.
          * **Worsening:** `> 10%` change AND `> 5` more complaints.
          * **Stable:** All other cases.
    3.  This trend status, along with a detailed graph, is displayed in a popup or sidebar.

-----

### \#\#\#\# User Interaction & Features

This section covers the interactive map features for the end-user.

#### Address Search & Smart Radius **(REVISED)**

  * **Concept:** To provide an intelligent, user-centric starting point for exploration, the system will generate an initial search radius based on the proximity of key Points of Interest (POIs), **keeping the user's search as the center point.**
  * **Implementation:**
    1.  The user searches for an address, which becomes the `search_center`.
    2.  The system queries a predefined list of POI categories (e.g., subway stations, grocery stores) within a capped search distance (e.g., 1 mile).
    3.  **Fallback:** If no POIs are found within the cap, the system defaults to a standard, fixed-radius circle (e.g., 500m).
    4.  If POIs are found, the system identifies the POI that is **farthest** from the `search_center`.
    5.  The circle's radius is set to the distance between the `search_center` and this farthest POI. The circle is drawn on the map, centered on the `search_center`.
    6.  The user can then use a slider or drag handles to manually resize and move the circle.

#### Zoom Behavior: Hexagons to Points

  * **Concept:** Switch from an aggregated hexagon view to a detailed, individual complaint view when the user is zoomed in far enough. This logic remains unchanged.
  * **Implementation:**
    1.  When the map's zoom level passes a set threshold, the hexagon layer is hidden.
    2.  The frontend fetches the raw latitude/longitude of individual complaints for the visible map area.
    3.  These points are rendered using a clustering library to manage density and maintain performance.


#maptiler link:
https://cloud.maptiler.com/maps/019986e1-bffa-78b0-a4af-bca020aa39ae/

#servicemap link:
https://portal.311.nyc.gov/article/?kanumber=KA-01361


https://portal.311.nyc.gov/check-status/


https://experience.arcgis.com/experience/c625a78991d34ae59deb7a33806ac0d1/page/Population-%7C-Density?views=Count




NYC 311 Explorer API v1

This document outlines the API endpoints required for the NYC 311 Explorer frontend application.
Base URL

/api/v1
Endpoints
1. Get Categories

Retrieves a list of all available 311 complaint categories for filtering.

    URL: /categories

    Method: GET

    Query Parameters: None

    Success Response (200 OK):

    [
      {
        "category": "Noise",
        "sort_order": 1
      },
      {
        "category": "Sanitation",
        "sort_order": 2
      },
      {
        "category": "Housing & Buildings",
        "sort_order": 3
      }
    ]

    Error Response (500 Internal Server Error):

    {
      "error": "Failed to retrieve categories."
    }

2. Get Heatmap Data

Retrieves aggregated 311 complaint data as H3 hexagons for a given category and geographic bounding box. This endpoint should be used for lower zoom levels.

    URL: /heatmap

    Method: GET

    Query Parameters:

        category (string, required): The complaint category to filter by (e.g., "Noise").

        bbox (string, required): A comma-separated string of the map's bounding box coordinates in the format west,south,east,north (e.g., -74.1,40.7,-73.9,40.8).

    Success Response (200 OK):
    A GeoJSON FeatureCollection where each feature is a Polygon representing an H3 hexagon. The properties of each feature must include the final_impact_score.

    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [-73.984, 40.759],
                [-73.985, 40.758],
                [-73.984, 40.757],
                [-73.983, 40.758],
                [-73.984, 40.759]
              ]
            ]
          },
          "properties": {
            "h3_index": "892a100d6bfffff",
            "final_impact_score": 85.5
          }
        }
      ]
    }

    Client-Side Visualization Note: The frontend client buckets the final_impact_score into three discrete color categories:

        Good (Green): Scores from 0 to 33.

        Average (Orange): Scores from 34 to 66.

        Poor (Red): Scores 67 and higher.

    Error Response (500 Internal Server Error):

    {
      "error": "Failed to retrieve heatmap data."
    }

3. Get Points Data

Retrieves individual 311 complaint locations for a given category and geographic bounding box. This endpoint should be used for higher zoom levels to show clusters and individual points.

    URL: /points

    Method: GET

    Query Parameters:

        category (string, required): The complaint category to filter by.

        bbox (string, required): A comma-separated string of the map's bounding box in the format west,south,east,north.

    Success Response (200 OK):
    A GeoJSON FeatureCollection where each feature is a Point representing a single 311 complaint.

    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [-73.987, 40.752]
          },
          "properties": {
            "unique_key": "58392019",
            "complaint_type": "Noise - Residential"
          }
        }
      ]
    }

    Error Response (500 Internal Server Error):

    {
      "error": "Failed to retrieve points data."
    }
