import React from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css"; // We'll create this next to style the map

function App() {
  // Coordinates for New York City
  const position = [40.7128, -74.006];

  return (
    <div id="app-container">
      {/* The MapContainer component is the root of the map */}
      <MapContainer center={position} zoom={11} scrollWheelZoom={true}>
        {/* The TileLayer is the base map image (e.g., OpenStreetMap) */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </MapContainer>
    </div>
  );
}

export default App;
