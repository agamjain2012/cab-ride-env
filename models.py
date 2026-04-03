"""
Data models for Cab Ride Environment.
"""

from __future__ import annotations

from typing import List, Dict
from pydantic import Field
from openenv.core.env_server import Action, Observation, State


class DriverInfo(Action):
    """
    Information about an available driver.
    """
    driver_id: int
    current_zone: str
    eta_to_pickup: float


class CabAction(Action):
    """
    Action for Cab Ride environment.
    """
    driver_id: int


class CabObservation(Observation):
    """
    Observation for Cab Ride environment.
    """
    pickup_location: str
    dropoff_location: str
    available_drivers: List[DriverInfo]
    simulation_time: float
    demand_forecast: Dict[str, float] = Field(default_factory=dict)


class DriverState(State):
    """
    Internal state of a driver.
    """
    driver_id: int
    current_zone: str
    status: str  # "IDLE", "TO_PICKUP", "BUSY"
    target_zone: str | None = None
    time_remaining: float = 0.0


class CabState(State):
    """
    State for Cab Ride environment.
    """
    drivers: List[DriverState]
    pending_requests: List[Dict]
    simulation_time: float
    step_count: int
