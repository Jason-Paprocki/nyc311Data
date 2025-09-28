Project Outline: NYC 311 Explorer

The goal is to create an advanced, interactive heatmap that visualizes NYC 311 complaint data. The system is designed to be performant, intuitive, and provide meaningful, context-aware insights by moving beyond simple data representation.

Core Data Visualization & Logic
This section covers the backend processing and the "engine" that drives the main visualization.

Color Scale Engine (The "Smart Scale")

    Concept: To solve the "population density" problem, the color of a hexagon is not based on a fixed, primitive scale. Instead, its color represents its rank compared to all other hexagons in the city. This scale is calculated dynamically.

    Implementation Logic (Backend / Scheduled Job):

        Scheduled Job: Once a day, a background process runs.

        Calculate Distribution: The job fetches the complaint count for every single hexagon across the city for the last 30 days.

        Define Brackets: It calculates the percentile boundaries from this data. For example:

            Low (Green): The bottom 50% of hexagons (e.g., those with 0-8 complaints).

            Medium (Yellow): Hexagons between the 50th and 85th percentile (e.g., 9-45 complaints).

            High (Red): The top 15% of all hexagons (e.g., 46+ complaints).

        Store Boundaries: These calculated boundaries (8 and 45 in this example) are saved. The API will use these numbers to categorize hexagons without having to recalculate anything on the fly.

The Historical Trend Layer

    Concept: To show not just the current state but also the direction of change, we'll encode a historical trend into the color of each hexagon.

    Implementation Logic (Backend):

        When the API receives a request for heatmap data, it performs two counts for each hexagon:

            Current Period: Complaints in the last 30 days.

            Previous Period: Complaints in the same 30-day period last year (to account for seasonality).

        The API compares the two counts to determine a trend status: Increasing, Stable, or Decreasing.

        The final API response for each hexagon will include its level (Low, Medium, or High) and its trend.

Frontend Color Rendering (The 9-Color System)

    Concept: Combine the level and trend into a single, intuitive color using three shades for each primary color.

    Implementation Logic (Frontend):

        The frontend will have a 9-color palette defined.

        When it receives data for a hexagon, it will use a simple lookup to select the final color:

            level: High, trend: Increasing → Deep Red (Worst case)

            level: High, trend: Decreasing → Pale Red (Still bad, but improving)

            level: Low, trend: Increasing → Deep Green (Good, but getting a little worse)

            level: Low, trend: Decreasing → Pale Green (Best case)

User Interaction & Features

This section covers the interactive features that make the tool powerful for users.

Address Search & "Smart Radius"

    Concept: The default search radius should intelligently adapt to the local density of the searched address.

    Implementation Logic:

        User searches an address, which is converted to a latitude/longitude coordinate.

        The frontend makes a call to a new API endpoint (e.g., /local-density).

        The backend calculates a "density score" by counting complaints in the immediate vicinity of the coordinate.

        Based on the score, the backend returns a suggested physical radius (e.g., 0.25 miles for high density, 0.5 miles for low density).

        The frontend draws a circle with this smart radius and fetches the data for that area.

Radius Slider & Comparison Mode Toggle

    Concept: Give "hardcore users" full control over their analysis.

    Implementation Logic (Frontend):

        Slider: A UI slider will be available after a search. Changing it adjusts the size of the search circle and triggers a new data fetch.

        Toggle: A UI toggle will switch between two color modes:

            "Borough View" (Default): Uses the standard, percentile-based color system. This is for fair, city-wide comparisons.

            "Local View": The frontend takes only the data currently visible, finds the local min/max, and temporarily re-colors the hexagons to highlight hotspots relative to the current view.

Zoom Behavior: Hexagons to Points

    Concept: Switch from an aggregated view (hexagons) to a detailed view (individual points) when the user is zoomed in far enough.

    Implementation Logic (Frontend & Backend):

        The frontend listens for map zoom events.

        Once the zoom level passes a threshold (e.g., zoom level 16), the hexagon layer is hidden.

        The frontend calls a new API endpoint (e.g., /points) to fetch the raw latitude/longitude of individual complaints for the visible area.

        These points are rendered on the map using a clustering library to group dense points into single, numbered circles, preventing the "blob" effect.
