import React, { useState } from "react";
// --- THIS IS THE FIX ---
// We import from 'react-map-gl/maplibre' to explicitly use the MapLibre library.
import Map, { Marker } from "react-map-gl/maplibre";
import Header from "./components/Header";
import "maplibre-gl/dist/maplibre-gl.css";
import "./App.css";

const NYC_BOUNDS = [
  [-74.25909, 40.477398], // Southwest coordinates
  [-73.700181, 40.917577], // Northeast coordinates
];

function App() {
  const [markerPosition, setMarkerPosition] = useState(null);
  const [viewState, setViewState] = useState({
    longitude: -74.006,
    latitude: 40.7128,
    zoom: 11,
  });

  const handleSearch = async (address) => {
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`,
    );
    const data = await response.json();

    if (data && data.length > 0) {
      const { lat, lon } = data[0];
      const newPos = { latitude: parseFloat(lat), longitude: parseFloat(lon) };

      setViewState({ ...newPos, zoom: 15 });
      setMarkerPosition(newPos);
    } else {
      alert("Address not found. Please try again.");
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
      </Map>
    </div>
  );
}

export default App;
