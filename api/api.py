import os
import importlib.util
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # << ENSURE THIS IS IMPORTED

# --- FastAPI App Initialization ---
app = FastAPI(
    title="NYC 311 Data API",
    description="An API to query NYC 311 complaint data.",
    version="1.0.0",
)

# --- CORS Middleware Configuration ---
# This is the section that fixes the error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# --- Dynamic Router Loading ---
endpoints_dir = "endpoints"

if os.path.isdir(endpoints_dir):
    for filename in os.listdir(endpoints_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            file_path = os.path.join(endpoints_dir, filename)

            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "router"):
                    app.include_router(
                        module.router,
                        prefix=f"/api/v1/{module_name}",
                        tags=[module_name.capitalize()],
                    )
                else:
                    print(f"Warning: No 'router' found in {filename}")

            except Exception as e:
                raise RuntimeError(f"Failed to load endpoint from {filename}: {e}")
else:
    print(
        "Warning: 'endpoints' directory not found. No dynamic endpoints will be loaded."
    )


# --- Root Endpoint ---
@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the NYC 311 Data API"}
