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

// --- NEW ---
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
