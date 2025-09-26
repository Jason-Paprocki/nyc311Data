import React, { useState, useEffect } from "react";
import "./Header.css";

// We define the NYC bounding box here for the API call.
// Format: [lon_west, lat_south, lon_east, lat_north]
const NYC_VIEWBOX = [-74.25909, 40.477398, -73.700181, 40.917577].join(",");

function Header({ onSearch }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);

  const fetchSuggestions = async (searchQuery) => {
    if (searchQuery.length < 3) {
      setSuggestions([]);
      return;
    }
    // --- UPDATED API URL ---
    // We added 'viewbox' and 'bounded=1' to restrict the search to NYC.
    // We also added 'addressdetails=1' to get the structured address object.
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&countrycodes=us&limit=5&viewbox=${NYC_VIEWBOX}&bounded=1&addressdetails=1`,
    );
    const data = await response.json();
    setSuggestions(data);
  };

  useEffect(() => {
    const timerId = setTimeout(() => {
      fetchSuggestions(query);
    }, 300);

    return () => {
      clearTimeout(timerId);
    };
  }, [query]);

  // This helper function builds a clean address from the API response
  const formatSuggestion = (suggestion) => {
    const { address } = suggestion;
    let house = address.house_number || "";
    let road = address.road || "";
    let city = address.city || address.town || address.village || "";
    let postcode = address.postcode || "";

    // Filter out empty parts and join them
    return [house, road, city, "NY", postcode].filter(Boolean).join(", ");
  };

  const handleSuggestionClick = (suggestion) => {
    const fullAddress = formatSuggestion(suggestion);
    setQuery(fullAddress);
    setSuggestions([]);
    onSearch(fullAddress);
  };

  return (
    <header className="app-header">
      <div className="logo-container">
        <h1>NYC 311 Explorer</h1>
      </div>
      <div className="search-container">
        <input
          type="text"
          placeholder="Search an address in New York City..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoComplete="off"
        />
        {suggestions.length > 0 && (
          <ul className="suggestions-list">
            {suggestions.map((suggestion) => (
              <li
                key={suggestion.place_id}
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {/* Use our new formatting function instead of the long display_name */}
                {formatSuggestion(suggestion)}
              </li>
            ))}
          </ul>
        )}
      </div>
    </header>
  );
}

export default Header;
