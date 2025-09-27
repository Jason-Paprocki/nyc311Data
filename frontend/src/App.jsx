import React, { useState, useEffect, useRef, useCallback } from "react";
import Map, { Marker, Source, Layer } from "react-map-gl/maplibre";
import * as turf from "@turf/turf";
import { WebMercatorViewport } from "@math.gl/web-mercator";
import Header from "./components/Header";
import { highlightedDistrictStyle, heatmapLayerStyle } from "./mapStyles"; // Note: You'll need to create/update this file
import "maplibre-gl/dist/maplibre-gl.css";
import "./App.css";

const NYC_BOUNDS = [
  [-74.25909, 40.477398],
  [-73.700181, 40.917577],
];

// --- HEATMAP LAYER STYLE ---
// Define the style for the heatmap layer.
// The color will change from green to yellow to red based on the complaint count.
const heatmapLayer = {
  id: "heatmap",
  type: "fill",
  paint: {
    "fill-color": [
      "interpolate",
      ["linear"],
      ["get", "count"],
      0,
      "rgba(0,0,0,0)", // Transparent for 0 count
      1,
      "#00ff00", // Green
      5,
      "#ffff00", // Yellow
      10,
      "#ff0000", // Red
    ],
    "fill-opacity": 0.6,
    "fill-outline-color": "rgba(255, 255, 255, 0.1)",
  },
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
  const [heatmapData, setHeatmapData] = useState(null); // State for heatmap GeoJSON

  useEffect(() => {
    const fetchDistrictData = async () => {
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
    };
    fetchDistrictData();
  }, []);

  // --- NEW: Fetch Heatmap Data ---
  // This function is wrapped in useCallback to prevent it from being recreated on every render.
  const fetchHeatmapData = useCallback(async () => {
    if (!mapRef.current) return;

    const map = mapRef.current.getMap();
    const bounds = map.getBounds();
    const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;

    // For now, we'll hardcode the complaint type. This could be a dropdown menu later.
    const complaintType = "Noise - Residential";

    try {
      const response = await fetch(
        `/api/v1/heatmap?complaint_type=${encodeURIComponent(complaintType)}&bbox=${bbox}`,
      );
      if (!response.ok) {
        throw new Error(`API call failed with status: ${response.status}`);
      }
      const data = await response.json();
      setHeatmapData(data);
    } catch (error) {
      console.error("Failed to fetch heatmap data:", error);
    }
  }, []); // The dependency array is empty because it only relies on the mapRef.

  const handleSearch = async (address) => {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
    );
    const data = await response.json();

    if (data && data.length > 0 && allDistricts) {
      const { lat, lon } = data[0];
      const newPos = { latitude: parseFloat(lat), longitude: parseFloat(lon) };
      const point = turf.point([newPos.longitude, newPos.latitude]);

      let foundDistrict = null;
      for (const district of allDistricts.features) {
        if (turf.booleanPointInPolygon(point, district.geometry)) {
          foundDistrict = district;
          break;
        }
      }

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
        setMarkerPosition(newPos);
      } else {
        setViewState({ ...newPos, zoom: 14 });
        setHighlightedDistrict(null);
        setMarkerPosition(newPos);
      }
    } else {
      alert("Address not found or district data not loaded yet.");
      setHighlightedDistrict(null);
    }
  };

  const mapStyleUrl = `https://api.maptiler.com/maps/019986e1-bffa-78b0-a4af-bca020aa39ae/style.json?key=${import.meta.env.VITE_MAPTILER_API}`;

  return (
    <div id="app-container">
      <Header onSearch={handleSearch} />
      <Map
        ref={mapRef}
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        onLoad={fetchHeatmapData} // Fetch data when map loads
        onMoveEnd={fetchHeatmapData} // Fetch new data when user stops moving map
        style={{ flexGrow: 1 }}
        mapStyle={mapStyleUrl}
        maxBounds={NYC_BOUNDS}
      >
        {/* --- NEW: Render Heatmap Layer --- */}
        {heatmapData && (
          <Source id="heatmap-source" type="geojson" data={heatmapData}>
            <Layer {...heatmapLayer} />
          </Source>
        )}

        {markerPosition && (
          <Marker
            longitude={markerPosition.longitude}
            latitude={markerPosition.latitude}
            anchor="bottom"
          />
        )}
        {highlightedDistrict && (
          <Source type="geojson" data={highlightedDistrict}>
            <Layer {...highlightedDistrictStyle} />
          </Source>
        )}
      </Map>
    </div>
  );
}

export default App;
