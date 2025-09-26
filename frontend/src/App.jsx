import React from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import Header from "./components/Header"; // Import the new Header component
import "leaflet/dist/leaflet.css";
import "./App.css";

function App() {
  const position = [40.7128, -74.006];

  return (
    <div id="app-container">
      <Header /> {/* Render the Header at the top */}
      <MapContainer center={position} zoom={11} scrollWheelZoom={true}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </MapContainer>
    </div>
  );
}

export default App;
