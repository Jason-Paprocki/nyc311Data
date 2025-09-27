// This file exports different map tile layer and overlay configurations.

export const tileLayers = {
  light: {
    url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
  dark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  },
};

// Style for the highlighted community district boundary
export const highlightedDistrictStyle = {
  id: "highlight-district-outline",
  type: "line",
  paint: {
    "line-color": "#007cbf",
    "line-width": 3,
    "line-opacity": 0.9,
  },
};

// --- THIS IS THE FIX ---
// Style for the H3 hexagon heatmap layer
export const heatmapLayerStyle = {
  id: "heatmap",
  type: "fill",
  paint: {
    "fill-color": [
      "interpolate",
      ["linear"],
      ["get", "count"],
      0,
      "rgba(0, 0, 0, 0)", // Transparent for 0 count
      1,
      "#feebe2",
      5,
      "#fbb4b9",
      10,
      "#f768a1",
      20,
      "#c51b8a",
      50,
      "#7a0177",
    ],
    "fill-opacity": 0.7,
    "fill-outline-color": "rgba(255, 255, 255, 0.1)",
  },
};
