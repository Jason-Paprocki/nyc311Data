import React, { useState, useEffect, useRef, useCallback } from "react";
import Map, { Marker, Source, Layer } from "react-map-gl/maplibre";
import * as turf from "@turf/turf";
import { WebMercatorViewport } from "@math.gl/web-mercator";

import Header from "./components/Header";
import CategorySelector from "./components/CategorySelector";
import {
  highlightedDistrictStyle,
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
  const [allDistricts, setAllDistricts] = useState(null);
  const [highlightedDistrict, setHighlightedDistrict] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [pointsData, setPointsData] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch community district boundary data for the search feature on initial load.
  useEffect(() => {
    const fetchDistrictData = async () => {
      try {
        const response = await fetch(
          "https://data.cityofnewyork.us/resource/5crt-au7u.json",
        );
        const data = await response.json();
        const features = data.map((district) => ({
          type: "Feature",
          geometry: district.the_geom,
          properties: { boro_cd: district.boro_cd },
        }));
        setAllDistricts({ type: "FeatureCollection", features });
      } catch (error) {
        console.error("Failed to fetch district data:", error);
      }
    };
    fetchDistrictData();
  }, []);

  // Main data fetching logic, called when map moves or category changes.
  const fetchData = useCallback(async () => {
    if (!mapRef.current || !selectedCategory) return;

    setIsLoading(true);
    const map = mapRef.current.getMap();
    const bounds = map.getBounds();
    const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;
    const currentZoom = map.getZoom();

    try {
      // Determine which API endpoint to call based on the current zoom level.
      // The trailing slash is added to match the backend's expected URL format.
      const endpoint =
        currentZoom < ZOOM_THRESHOLD.CLUSTER
          ? `/api/v1/heatmap/?category=${encodeURIComponent(
              selectedCategory,
            )}&bbox=${bbox}`
          : `/api/v1/points/?category=${encodeURIComponent(
              selectedCategory,
            )}&bbox=${bbox}`;

      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`API call failed with status: ${response.status}`);
      }
      const data = await response.json();

      // Update the appropriate data state based on the zoom level.
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

      if (data && data.length > 0 && allDistricts) {
        const { lat, lon } = data[0];
        const newPos = {
          latitude: parseFloat(lat),
          longitude: parseFloat(lon),
        };
        const point = turf.point([newPos.longitude, newPos.latitude]);

        // Find which community district the searched point falls into.
        let foundDistrict = null;
        for (const district of allDistricts.features) {
          if (turf.booleanPointInPolygon(point, district.geometry)) {
            foundDistrict = district;
            break;
          }
        }

        // If a district is found, zoom the map to fit its boundaries.
        if (foundDistrict) {
          const [minLng, minLat, maxLng, maxLat] = turf.bbox(foundDistrict);
          const viewport = new WebMercatorViewport({
            ...viewState,
            width: window.innerWidth,
            height: window.innerHeight,
          });
          const { longitude, latitude, zoom } = viewport.fitBounds(
            [
              [minLng, minLat],
              [maxLng, maxLat],
            ],
            { padding: 40 },
          );
          setViewState({ longitude, latitude, zoom });
          setHighlightedDistrict(foundDistrict);
        } else {
          // If no district is found, just center the map on the point.
          setViewState({ ...newPos, zoom: 14 });
          setHighlightedDistrict(null);
        }
        setMarkerPosition(newPos);
      } else {
        console.warn("Address not found or district data not loaded yet.");
        setHighlightedDistrict(null);
      }
    } catch (error) {
      console.error("Search failed:", error);
    }
  };

  // IMPORTANT: Replace "GET_YOUR_OWN_KEY" with an actual API key from a provider like Maptiler or Stadia.
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

          {/* Highlighted District Layer */}
          {highlightedDistrict && (
            <Source type="geojson" data={highlightedDistrict}>
              <Layer {...highlightedDistrictStyle} />
            </Source>
          )}
        </Map>
      </div>
    </div>
  );
}

export default App;
