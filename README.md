NYC 311 Data Visualization Project

This project is a full-stack web application designed to ingest, process, and visualize 311 complaint data for New York City using a sophisticated geospatial approach. It demonstrates skills in data engineering, backend and frontend development, and modern DevSecOps practices.

Project Vision

The final application will provide users with an interactive, high-performance map interface to explore NYC 311 complaint data. Key features include:

    Hexagonal Heatmap: A dynamic, color-coded hexagonal grid visualizing complaint density across the city.

    Address Search: An autocomplete-enabled search bar to instantly navigate to any address in NYC.

    Contextual "Scorecard": A side panel that provides at-a-glance statistics for a searched area, comparing local complaint levels to the Community District average.

    Custom Map Styling: A clean, minimalist vector map designed for data visualization, with all unnecessary clutter removed.

Technology Stack

    Data Pipeline: Python, Docker

    Database: PostgreSQL with PostGIS for geospatial analysis

    Backend: FastAPI

    Frontend: React, Vite, MapLibre GL JS for vector map rendering

    Geospatial: H3 for hexagonal grid system, Maptiler for custom map styles, Nominatim for geocoding

Project Plan & Status

Phase 1: Data Pipeline & Storage (The Foundation)

STATUS: 95% Complete
The goal is to reliably fetch, store, and structure NYC data for high-performance geospatial querying.

    [x] 1A: Build Ingestion Script: A robust Python script performs efficient, incremental data loads from the NYC OpenData API.

    [x] 1B: Set up PostGIS Database: A fully containerized PostGIS service is self-initializing and optimized for spatial queries with a GEOGRAPHY type and spatial index.

    [x] 1C: Full Orchestration: All services are orchestrated via docker-compose and configured securely with a .env file.

    [ ] 1D: Load Contextual Boundaries: A one-time script to download and load NYC Community District GeoJSON boundaries into the database. (Next Step)

Phase 2: Backend API & Analytics (The Engine)

STATUS: 25% Complete
This phase focuses on pre-calculating statistics and building the API endpoints to serve processed data to the frontend.

    [x] 2A: Build "Skeleton" API: A containerized FastAPI service is running, networked with the database, and serving test data.

    [ ] 2B: Pre-calculate Baselines: An offline analytics script to calculate the average complaint density for each complaint type within each Community District, stored in a new community_district_stats table.

    [ ] 2C: Augment Data with H3: Update the ingestion script and database to map every 311 complaint to a fixed H3 hexagon ID for instant aggregation.

    [ ] 2D: Build Core API Endpoints:

        Create the GET /api/v1/heatmap endpoint to return scored, color-coded hexagon data for the current map view.

        Create the GET /api/v1/scorecard endpoint to return detailed statistics for a specific Community District.

Phase 3: Frontend Interface (The Visualization)

STATUS: 60% Complete
This phase focuses on building the complete user experience for visualizing and interacting with the data.

    [x] 3A: Set up Frontend & Map: A containerized React + Vite application is running with a fully interactive, custom-styled vector map powered by MapLibre GL and Maptiler.

    [x] 3B: Implement Address Search: A fully functional search bar with debounced autocomplete suggestions is implemented. The search is constrained to NYC and uses a clean, user-friendly address format.

    [x] 3C: Implement Bounded Pan: The map view is locked to the NYC area to improve usability and manage tile usage.

    [ ] 3D: Render Hexagon Layer: Use MapLibre's Source and Layer components to fetch and render the GeoJSON data from the /heatmap endpoint, with colors determined by the data's "score."

    [ ] 3E: Build the "Scorecard" UI: Create a SidePanel component that appears after a search, fetches data from the /scorecard endpoint, and displays the "above/below average" statistics.

Phase 4: CI/CD & Security (DevSecOps)

STATUS: 10% Complete
This ongoing phase involves ensuring the entire application is robust, secure, and easy to manage.

    [ ] 4A: Security Hardening: Scan container images for vulnerabilities and implement proper secrets management.

    [ ] 4B: CI/CD Pipeline (Optional): Set up a basic CI/CD pipeline (e.g., using GitHub Actions) to automatically build, test, and deploy the application.
