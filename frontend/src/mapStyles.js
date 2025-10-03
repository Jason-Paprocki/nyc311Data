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

// Style for the H3 hexagon heatmap layer with a Green-Orange-Red scale.
// Lower "final_impact_score" is better (green), higher is worse (red).
export const heatmapLayerStyle = {
  id: "heatmap",
  type: "fill",
  paint: {
    "fill-color": [
      "step",
      ["get", "final_impact_score"],
      "#2dc937", // Green for scores 0-33
      34,
      "#fca600", // Orange for scores 34-66
      67,
      "#e51919", // Red for scores 67+
    ],
    "fill-opacity": 0.7,
    "fill-outline-color": "rgba(255, 255, 255, 0.1)",
  },
};

// Style for the clustered points layer
export const clusterLayerStyle = {
  id: "clusters",
  type: "circle",
  paint: {
    "circle-color": [
      "step",
      ["get", "point_count"],
      "#51bbd6", // Blue for less than 100 points
      100,
      "#f1f075", // Yellow for 100-750 points
      750,
      "#f28cb1", // Pink for more than 750 points
    ],
    "circle-radius": ["step", ["get", "point_count"], 20, 100, 30, 750, 40],
  },
};

// Style for the cluster count text
export const clusterCountLayerStyle = {
  id: "cluster-count",
  type: "symbol",
  layout: {
    "text-field": "{point_count_abbreviated}",
    "text-font": ["DIN Offc Pro Medium", "Arial Unicode MS Bold"],
    "text-size": 12,
  },
};

// Style for the unclustered, individual points
export const unclusteredPointLayerStyle = {
  id: "unclustered-point",
  type: "circle",
  paint: {
    "circle-color": "#11b4da",
    "circle-radius": 4,
    "circle-stroke-width": 1,
    "circle-stroke-color": "#fff",
  },
};
