import React, { useState, useEffect } from "react";
import Map, { Marker, Source, Layer } from "react-map-gl/maplibre";
import * as turf from "@turf/turf";
import { WebMercatorViewport } from "@math.gl/web-mercator";
import Header from "./components/Header";
import { highlightedDistrictStyle } from "./mapStyles";
import "maplibre-gl/dist/maplibre-gl.css";
import "./App.css";

const NYC_BOUNDS = [
  [-74.25909, 40.477398],
  [-73.700181, 40.917577],
];

function App() {
  const [markerPosition, setMarkerPosition] = useState(null);
  const [viewState, setViewState] = useState({
    longitude: -74.006,
    latitude: 40.7128,
    zoom: 11,
  });
  const [allDistricts, setAllDistricts] = useState(null);
  const [highlightedDistrict, setHighlightedDistrict] = useState(null);

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

        // --- THIS IS THE FIX ---
        // We must provide the current viewport dimensions (width, height) for the calculation.
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
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        style={{ flexGrow: 1 }}
        mapStyle={mapStyleUrl}
        maxBounds={NYC_BOUNDS}
      >
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
