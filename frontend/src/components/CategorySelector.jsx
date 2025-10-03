import React, { useState, useEffect } from "react";

function CategorySelector({
  selectedCategory,
  setSelectedCategory,
  isLoading,
}) {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    // Fetches the list of complaint categories from the API.
    const fetchCategories = async () => {
      try {
        const response = await fetch("/api/v1/categories");
        if (!response.ok) {
          throw new Error(`API call failed with status: ${response.status}`);
        }
        const data = await response.json();
        setCategories(data);
        // If no category is selected yet, default to the first one.
        if (data.length > 0 && !selectedCategory) {
          setSelectedCategory(data[0].category);
        }
      } catch (err) {
        console.error("Failed to fetch categories:", err);
      }
    };
    fetchCategories();
  }, [setSelectedCategory, selectedCategory]);

  return (
    <div className="category-selector">
      {categories.map(({ category }) => (
        <button
          key={category}
          className={`category-btn ${
            selectedCategory === category ? "selected" : ""
          }`}
          onClick={() => setSelectedCategory(category)}
          disabled={isLoading} // Disable buttons while map data is loading.
        >
          {category}
        </button>
      ))}
    </div>
  );
}

export default CategorySelector;
