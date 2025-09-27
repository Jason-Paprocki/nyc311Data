import React, { useState, useEffect, useRef, useCallback } from "react";
import Map, { Marker, Source, Layer } from "react-map-gl/maplibre";
import * as turf from "@turf/turf";
import { WebMercatorViewport } from "@math.gl/web-mercator";
import Header from "./components/Header";
import { highlightedDistrictStyle, heatmapLayerStyle } from "./mapStyles";
import "maplibre-gl/dist/maplibre-gl.css";
import "./App.css";

const NYC_BOUNDS = [
  [-74.25909, 40.477398],
  [-73.700181, 40.917577],
];

const CategorySelector = ({
  selectedCategory,
  setSelectedCategory,
  isLoading,
}) => {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch("/api/v1/categories");
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();
        setCategories(data);
        if (data.length > 0 && !selectedCategory) {
          setSelectedCategory(data[0].category);
        }
      } catch (err) {
        console.error("Failed to fetch categories:", err);
      }
    };
    fetchCategories();
  }, [setSelectedCategory, selectedCategory]);

  return (
    <div className="category-selector">
      {categories.map(({ category }) => (
        <button
          key={category}
          className={`category-btn ${selectedCategory === category ? "selected" : ""}`}
          onClick={() => setSelectedCategory(category)}
          disabled={isLoading} // Disable button when loading
        >
          {category}
        </button>
      ))}
    </div>
  );
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
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [isLoading, setIsLoading] = useState(false); // The missing state variable

  useEffect(() => {
    const fetchDistrictData = async () => {
      // This function fetches community district boundaries for the search feature
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

  const fetchHeatmapData = useCallback(async () => {
    if (!mapRef.current || !selectedCategory) return;

    setIsLoading(true); // Start loading
    console.log(
      `🔥 [TRIGGER] Fetching heatmap for category: ${selectedCategory}`,
    );

    const map = mapRef.current.getMap();
    const bounds = map.getBounds();
    const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;

    try {
      const response = await fetch(
        `/api/v1/heatmap?category=${encodeURIComponent(selectedCategory)}&bbox=${bbox}`,
      );
      if (!response.ok) {
        throw new Error(`API call failed with status: ${response.status}`);
      }
      const data = await response.json();
      console.log(
        `📦 [DATA] Received ${data.features.length} heatmap features.`,
      );
      setHeatmapData(data);
    } catch (error) {
      console.error("❌ [ERROR] Failed to fetch heatmap data:", error);
      setHeatmapData(null);
    } finally {
      setIsLoading(false); // Stop loading
    }
  }, [selectedCategory]);

  // Effect to re-fetch heatmap data when the selected category changes
  useEffect(() => {
    if (selectedCategory) {
      fetchHeatmapData();
    }
  }, [selectedCategory, fetchHeatmapData]);

  const handleSearch = async (address) => {
    // This function geocodes an address and highlights the corresponding district
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
      );
      const data = await response.json();
      if (data && data.length > 0 && allDistricts) {
        const { lat, lon } = data[0];
        const newPos = {
          latitude: parseFloat(lat),
          longitude: parseFloat(lon),
        };
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
        } else {
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
          onMoveEnd={fetchHeatmapData}
          onLoad={fetchHeatmapData}
          style={{ flexGrow: 1 }}
          mapStyle={mapStyleUrl}
          maxBounds={NYC_BOUNDS}
          className={`map-container ${isLoading ? "loading" : ""}`}
        >
          {heatmapData && (
            <Source id="heatmap-source" type="geojson" data={heatmapData}>
              <Layer {...heatmapLayerStyle} />
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
    </div>
  );
}

export default App;
