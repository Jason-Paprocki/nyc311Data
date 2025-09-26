import React, { useState, useEffect } from "react";
import "./Header.css";

const NYC_VIEWBOX = [-74.25909, 40.477398, -73.700181, 40.917577].join(",");

function Header({ onSearch }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  // --- NEW STATE TO FIX THE BUG ---
  // This state explicitly controls the visibility of the suggestions dropdown.
  const [showSuggestions, setShowSuggestions] = useState(true);

  const fetchSuggestions = async (searchQuery) => {
    if (searchQuery.length < 3) {
      setSuggestions([]);
      return;
    }
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&countrycodes=us&limit=5&viewbox=${NYC_VIEWBOX}&bounded=1&addressdetails=1`,
    );
    const data = await response.json();
    setSuggestions(data);
  };

  useEffect(() => {
    // Only fetch if the query is not empty and we want to show suggestions
    if (query && showSuggestions) {
      const timerId = setTimeout(() => {
        fetchSuggestions(query);
      }, 300);

      return () => {
        clearTimeout(timerId);
      };
    } else {
      setSuggestions([]); // Clear suggestions if input is empty or hidden
    }
  }, [query, showSuggestions]);

  const formatSuggestion = (suggestion) => {
    const { address } = suggestion;
    let house = address.house_number || "";
    let road = address.road || "";
    let city = address.city || address.town || address.village || "";
    let postcode = address.postcode || "";
    return [house, road, city, "NY", postcode].filter(Boolean).join(", ");
  };

  const handleSuggestionClick = (suggestion) => {
    const fullAddress = formatSuggestion(suggestion);
    setQuery(fullAddress);
    // --- FIX ---
    // Explicitly hide the suggestions dropdown upon selection.
    setShowSuggestions(false);
    onSearch(fullAddress);
  };

  // --- NEW HANDLER ---
  // When the user types, show the suggestions again.
  const handleInputChange = (e) => {
    setQuery(e.target.value);
    if (!showSuggestions) {
      setShowSuggestions(true);
    }
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
          onChange={handleInputChange} // Use the new handler
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)} // Hide on blur with a small delay
          autoComplete="off"
        />
        {/* --- UPDATED RENDER LOGIC --- */}
        {/* Only show the list if there are suggestions AND we want to show them */}
        {suggestions.length > 0 && showSuggestions && (
          <ul className="suggestions-list">
            {suggestions.map((suggestion) => (
              <li
                key={suggestion.place_id}
                onClick={() => handleSuggestionClick(suggestion)}
              >
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
