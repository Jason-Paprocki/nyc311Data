import React, { useState, useEffect } from "react";
import "./Header.css";

// Defines the bounding box for NYC to prioritize local search results.
const NYC_VIEWBOX = [-74.25909, 40.477398, -73.700181, 40.917577].join(",");

function Header({ onSearch }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(true);

  useEffect(() => {
    // Fetches address suggestions from OpenStreetMap's Nominatim API.
    const fetchSuggestions = async (searchQuery) => {
      // Avoid API calls for very short queries.
      if (searchQuery.length < 3) {
        setSuggestions([]);
        return;
      }
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
            searchQuery,
          )}&countrycodes=us&limit=5&viewbox=${NYC_VIEWBOX}&bounded=1&addressdetails=1`,
        );
        const data = await response.json();
        setSuggestions(data);
      } catch (error) {
        console.error("Failed to fetch suggestions:", error);
      }
    };

    // Debounce API calls to prevent firing on every keystroke.
    if (query && showSuggestions) {
      const timerId = setTimeout(() => {
        fetchSuggestions(query);
      }, 300); // Wait 300ms after user stops typing.

      return () => clearTimeout(timerId);
    } else {
      setSuggestions([]);
    }
  }, [query, showSuggestions]);

  // Formats the raw suggestion data into a readable address string.
  const formatSuggestion = (suggestion) => {
    const { address } = suggestion;
    return [
      address.house_number,
      address.road,
      address.city || address.town || address.village,
      "NY",
      address.postcode,
    ]
      .filter(Boolean)
      .join(", ");
  };

  // Handles when a user clicks on a suggestion.
  const handleSuggestionClick = (suggestion) => {
    const fullAddress = formatSuggestion(suggestion);
    setQuery(fullAddress);
    setShowSuggestions(false); // Hide suggestions after selection.
    onSearch(fullAddress); // Pass the search query up to the App component.
  };

  // Handles changes to the input field.
  const handleInputChange = (e) => {
    setQuery(e.target.value);
    if (!showSuggestions) {
      setShowSuggestions(true); // Show suggestions again if user starts typing.
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
          onChange={handleInputChange}
          // A short delay on blur prevents the list from disappearing before a click is registered.
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          autoComplete="off"
        />
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
