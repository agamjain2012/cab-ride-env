"""FastAPI application for the Cab Ride Environment."""

from openenv.core.env_server import create_app

# Support both in-repo and standalone imports
try:
    from ..models import CabAction, CabObservation
    from .cab_ride_environment import CabRideEnvironment
except ImportError:
    from models import CabAction, CabObservation
    from server.cab_ride_environment import CabRideEnvironment

# Create the FastAPI app
app = create_app(
    CabRideEnvironment, CabAction, CabObservation, env_name="cab_ride_env"
)

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
