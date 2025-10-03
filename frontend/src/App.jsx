import React, { useState, useEffect, useRef, useCallback } from "react";
import Map, { Marker, Source, Layer } from "react-map-gl/maplibre";
import * as turf from "@turf/turf";
import { WebMercatorViewport } from "@math.gl/web-mercator";

// Component Imports
import Header from "./components/Header";
import CategorySelector from "./components/CategorySelector";

// Style Imports
import {
  heatmapLayerStyle,
  clusterLayerStyle,
  clusterCountLayerStyle,
  unclusteredPointLayerStyle,
} from "./mapStyles";
import "maplibre-gl/dist/maplibre-gl.css";
import "./App.css";

const NYC_BOUNDS = [
  [-74.25909, 40.477398],
  [-73.700181, 40.917577],
];

// Zoom levels to switch between heatmap, clusters, and individual points.
const ZOOM_THRESHOLD = {
  CLUSTER: 12,
  POINT: 15,
};

function App() {
  const mapRef = useRef();
  const [markerPosition, setMarkerPosition] = useState(null);
  const [viewState, setViewState] = useState({
    longitude: -74.006,
    latitude: 40.7128,
    zoom: 11,
  });
  const [heatmapData, setHeatmapData] = useState(null);
  const [pointsData, setPointsData] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Main data fetching logic, called when map moves or category changes.
  const fetchData = useCallback(async () => {
    if (!mapRef.current || !selectedCategory) return;

    setIsLoading(true);
    const map = mapRef.current.getMap();
    const bounds = map.getBounds();
    const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;
    const currentZoom = map.getZoom();

    try {
      const endpoint =
        currentZoom < ZOOM_THRESHOLD.CLUSTER
          ? `/api/v1/heatmap/?category=${encodeURIComponent(
              selectedCategory,
            )}&bbox=${bbox}`
          : `/api/v1/points/?category=${encodeURIComponent(
              selectedCategory,
            )}&bbox=${bbox}`;

      console.log("Attempting to fetch data from endpoint:", endpoint);

      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`API call failed with status: ${response.status}`);
      }
      const data = await response.json();

      if (currentZoom < ZOOM_THRESHOLD.CLUSTER) {
        setHeatmapData(data);
        setPointsData(null);
      } else {
        setPointsData(data);
        setHeatmapData(null);
      }
    } catch (error) {
      console.error("Failed to fetch map data:", error);
      setHeatmapData(null);
      setPointsData(null);
    } finally {
      setIsLoading(false);
    }
  }, [selectedCategory]);

  // Re-fetch data whenever the selected category changes.
  useEffect(() => {
    if (selectedCategory) {
      fetchData();
    }
  }, [selectedCategory, fetchData]);

  // Handles the address search event from the Header component.
  const handleSearch = async (address) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
          address,
        )}&limit=1`,
      );
      const data = await response.json();

      if (data && data.length > 0) {
        const { lat, lon } = data[0];
        const newPos = {
          latitude: parseFloat(lat),
          longitude: parseFloat(lon),
        };

        // Center the map on the searched point with a closer zoom.
        setViewState({ ...newPos, zoom: 16 });
        setMarkerPosition(newPos);
      } else {
        console.warn("Address not found.");
      }
    } catch (error) {
      console.error("Search failed:", error);
    }
  };

  const mapStyleUrl = `https://api.maptiler.com/maps/019986e1-bffa-78b0-a4af-bca020aa39ae/style.json?key=${import.meta.env.VITE_MAPTILER_API}`;

  return (
    <div id="app-container">
      <Header onSearch={handleSearch} />
      <CategorySelector
        selectedCategory={selectedCategory}
        setSelectedCategory={setSelectedCategory}
        isLoading={isLoading}
      />
      <div id="map-wrapper">
        <Map
          ref={mapRef}
          {...viewState}
          onMove={(evt) => setViewState(evt.viewState)}
          onMoveEnd={fetchData}
          onLoad={fetchData}
          style={{ flexGrow: 1 }}
          mapStyle={mapStyleUrl}
          maxBounds={NYC_BOUNDS}
          className={`map-container ${isLoading ? "loading" : ""}`}
        >
          {/* Heatmap Layer */}
          {heatmapData && viewState.zoom < ZOOM_THRESHOLD.CLUSTER && (
            <Source id="heatmap-source" type="geojson" data={heatmapData}>
              <Layer {...heatmapLayerStyle} />
            </Source>
          )}

          {/* Clustered and Unclustered Points Layer */}
          {pointsData && viewState.zoom >= ZOOM_THRESHOLD.CLUSTER && (
            <Source
              id="points-source"
              type="geojson"
              data={pointsData}
              cluster={true}
              clusterMaxZoom={ZOOM_THRESHOLD.POINT - 1}
              clusterRadius={50}
            >
              <Layer {...clusterLayerStyle} />
              <Layer {...clusterCountLayerStyle} />
              <Layer
                {...unclusteredPointLayerStyle}
                filter={["!", ["has", "point_count"]]}
              />
            </Source>
          )}

          {/* Searched Location Marker */}
          {markerPosition && (
            <Marker
              longitude={markerPosition.longitude}
              latitude={markerPosition.latitude}
              anchor="bottom"
            />
          )}
        </Map>
      </div>
    </div>
  );
}

export default App;
