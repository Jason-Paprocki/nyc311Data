import React, { useState, useEffect } from 'react';

function App() {
  const [latestComplaints, setLatestComplaints] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // This function is called when the component first loads.
    const fetchLatestComplaints = async () => {
      try {
        // We use '/api' here, which Vite will proxy to our backend.
        const response = await fetch('/api/v1/complaints/latest');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setLatestComplaints(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLatestComplaints();
  }, []); // The empty array ensures this effect runs only once.

  return (
    <div>
      <h1>NYC 311 Data Explorer</h1>
      <h2>Latest Complaints</h2>
      {isLoading && <p>Loading data...</p>}
      {error && <p style={{ color: 'red' }}>Error fetching data: {error}</p>}
      {latestComplaints && (
        <pre style={{ background: '#f4f4f4', padding: '1rem', borderRadius: '5px' }}>
          {JSON.stringify(latestComplaints, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default App;
