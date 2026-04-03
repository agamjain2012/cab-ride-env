"""
Cab Ride Environment Client.
"""

from __future__ import annotations

from typing import Any, Dict

from openenv.core.client_types import StepResult
from openenv.core.env_client import EnvClient

from .models import CabAction, CabObservation, CabState, DriverInfo

class CabRideEnv(EnvClient[CabAction, CabObservation, CabState]):
    """
    Client for Cab Ride Environment.
    """

    def _step_payload(self, action: CabAction) -> Dict[str, Any]:
        return {
            "driver_id": action.driver_id,
        }

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[CabObservation]:
        obs_data = payload.get("observation", {})

        available_drivers = [
            DriverInfo(**d) for d in obs_data.get("available_drivers", [])
        ]

        observation = CabObservation(
            pickup_location=obs_data.get("pickup_location", ""),
            dropoff_location=obs_data.get("dropoff_location", ""),
            available_drivers=available_drivers,
            simulation_time=obs_data.get("simulation_time", 0.0),
            demand_forecast=obs_data.get("demand_forecast", {}),
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> CabState:
        return CabState(**payload)
