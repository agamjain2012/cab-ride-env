"""
Cab Ride Environment Server.
"""

try:
    from .cab_ride_environment import CabRideEnvironment
except (ImportError, ValueError):
    from cab_ride_environment import CabRideEnvironment

__all__ = ["CabRideEnvironment"]
