"""FastAPI application for the Cab Ride Environment."""

from fastapi.responses import RedirectResponse
from openenv.core.env_server import create_app

# Support both in-repo and standalone imports
try:
    from ..models import CabAction, CabObservation
    from .cab_ride_environment import CabRideEnvironment
except (ImportError, ValueError):
    try:
        from models import CabAction, CabObservation
        from server.cab_ride_environment import CabRideEnvironment
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from models import CabAction, CabObservation
        from server.cab_ride_environment import CabRideEnvironment

# Create a single persistent environment instance
env_instance = CabRideEnvironment()

def env_factory():
    return env_instance

# Create the FastAPI app
app = create_app(
    env_factory, CabAction, CabObservation, env_name="cab_ride_env"
)

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health():
    return {"status": "ok"}

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
