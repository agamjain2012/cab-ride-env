"""
Data models for Cab Ride Environment.
"""

from __future__ import annotations

from typing import List, Dict, Any
from pydantic import BaseModel, Field
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


class CabReward(BaseModel):
    """
    Reward for Cab Ride environment.
    """
    wait_time_penalty: float
    positioning_penalty: float
    invalid_action_penalty: float = 0.0

    @property
    def value(self) -> float:
        return -(self.wait_time_penalty + self.positioning_penalty + self.invalid_action_penalty)


class CabObservation(Observation):
    """
    Observation for Cab Ride environment.
    """
    pickup_location: str
    dropoff_location: str
    available_drivers: List[DriverInfo]
    simulation_time: float
    demand_forecast: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: float | None = None
    task_id: str | None = None


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
    task_id: str
    drivers: List[DriverState]
    pending_requests: List[Dict]
    simulation_time: float
    step_count: int
    total_wait_time: float = 0.0
    steps_taken: int = 0


CabObservation.model_rebuild()
