import React from "react";
import "./Header.css"; // We'll create this file next

function Header() {
  return (
    <header className="app-header">
      <div className="logo-container">
        <h1>NYC 311 Explorer</h1>
      </div>
      <div className="search-container">
        <input
          type="text"
          placeholder="Search an address in New York City..."
        />
      </div>
    </header>
  );
}

export default Header;
