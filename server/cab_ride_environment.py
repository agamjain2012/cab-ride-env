import random
import uuid
from typing import Dict, List, Any, Optional

from openenv.core.env_server import Environment

# Support both in-repo and standalone imports
try:
    from ..models import CabAction, CabObservation, CabReward, CabState, DriverInfo, DriverState
except (ImportError, ValueError):
    try:
        from models import CabAction, CabObservation, CabReward, CabState, DriverInfo, DriverState
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from models import CabAction, CabObservation, CabReward, CabState, DriverInfo, DriverState

# Bengaluru Zones and a simplified travel time matrix (minutes)
ZONES = [
    "Indiranagar", "Koramangala", "HSR Layout", "Whitefield", "Marathahalli",
    "MG Road", "Jayanagar", "JP Nagar", "Electronic City", "Bellandur"
]

TRAVEL_TIMES = {
    "Indiranagar": {"Koramangala": 20, "HSR Layout": 25, "Whitefield": 40, "MG Road": 15, "Bellandur": 30},
    "Koramangala": {"Indiranagar": 20, "HSR Layout": 15, "MG Road": 20, "Bellandur": 20, "Electronic City": 35},
    "HSR Layout": {"Koramangala": 15, "Bellandur": 15, "Electronic City": 25, "JP Nagar": 20},
    "Whitefield": {"Marathahalli": 15, "Indiranagar": 40, "Bellandur": 25},
    "Marathahalli": {"Whitefield": 15, "Bellandur": 15, "Indiranagar": 30},
    "MG Road": {"Indiranagar": 15, "Koramangala": 20, "Jayanagar": 25},
    "Jayanagar": {"MG Road": 25, "JP Nagar": 15, "Koramangala": 20},
    "JP Nagar": {"Jayanagar": 15, "HSR Layout": 20, "Electronic City": 30},
    "Electronic City": {"HSR Layout": 25, "JP Nagar": 30, "Koramangala": 35},
    "Bellandur": {"Marathahalli": 15, "HSR Layout": 15, "Koramangala": 20, "Whitefield": 25}
}

# Fill in missing symmetric entries and self-travel
for z1 in ZONES:
    if z1 not in TRAVEL_TIMES: TRAVEL_TIMES[z1] = {}
    TRAVEL_TIMES[z1][z1] = 0
    for z2 in ZONES:
        if z2 not in TRAVEL_TIMES[z1]:
            TRAVEL_TIMES[z1][z2] = TRAVEL_TIMES.get(z2, {}).get(z1, 45)

DEMAND_FORECAST = {
    "Indiranagar": 0.9, "Koramangala": 0.9, "HSR Layout": 0.8,
    "Whitefield": 0.7, "Marathahalli": 0.7, "MG Road": 0.8,
    "Jayanagar": 0.6, "JP Nagar": 0.6, "Electronic City": 0.5, "Bellandur": 0.8
}

class CabRideEnvironment(Environment):
    def __init__(self):
        super().__init__()
        self.max_steps = 20
        self.reset()

    def reset(self, task_id: str = "medium", **kwargs):
        self.task_id = task_id
        self.simulation_time = 0.0
        self.total_wait_time = 0.0
        self.steps_taken = 0
        
        # Configure based on task
        if task_id == "easy":
            self.max_steps = 1
            num_drivers = 3
            # Fixed setup for easy task
            self.drivers = [
                DriverState(driver_id=0, current_zone="Electronic City", status="IDLE"),
                DriverState(driver_id=1, current_zone="Indiranagar", status="IDLE"),
                DriverState(driver_id=2, current_zone="Whitefield", status="IDLE")
            ]
            self.pending_request = {"pickup": "Indiranagar", "dropoff": "Koramangala", "request_time": 0.0}
        elif task_id == "hard":
            self.max_steps = 30
            num_drivers = 10
            self.drivers = [DriverState(driver_id=i, current_zone=random.choice(ZONES), status="IDLE") for i in range(num_drivers)]
            self.pending_request = self._generate_request()
        else: # medium
            self.max_steps = 20
            num_drivers = 5
            self.drivers = [DriverState(driver_id=i, current_zone=random.choice(ZONES), status="IDLE") for i in range(num_drivers)]
            self.pending_request = self._generate_request()

        self._state = CabState(
            drivers=self.drivers,
            pending_requests=[self.pending_request],
            simulation_time=self.simulation_time,
            step_count=0,
            episode_id=str(uuid.uuid4())
        )
        return self._make_observation()

    def _generate_request(self) -> Dict[str, Any]:
        # Logic for demand-based request generation
        if self.task_id == "hard":
            # In hard mode, requests mostly come from low-demand residential zones 
            # and want to go to high-demand business zones.
            pickup = random.choices(ZONES, weights=[1.0 - DEMAND_FORECAST[z] for z in ZONES])[0]
            dropoff = random.choices(ZONES, weights=[DEMAND_FORECAST[z] for z in ZONES])[0]
            if pickup == dropoff: dropoff = random.choice([z for z in ZONES if z != pickup])
        else:
            pickup = random.choice(ZONES)
            dropoff = random.choice([z for z in ZONES if z != pickup])
        
        return {"pickup": pickup, "dropoff": dropoff, "request_time": self.simulation_time}

    def _make_observation(self, reward: Optional[CabReward] = None, done: bool = False) -> CabObservation:
        available_drivers = []
        pickup = self.pending_request["pickup"]
        for d in self.drivers:
            if d.status == "IDLE":
                eta = TRAVEL_TIMES[d.current_zone][pickup]
                available_drivers.append(DriverInfo(
                    driver_id=d.driver_id,
                    current_zone=d.current_zone,
                    eta_to_pickup=float(eta)
                ))
        
        # Use default zero reward if none provided
        current_reward = reward or CabReward(wait_time_penalty=0.0, positioning_penalty=0.0)
        
        obs = CabObservation(
            pickup_location=pickup,
            dropoff_location=self.pending_request["dropoff"],
            available_drivers=available_drivers,
            simulation_time=self.simulation_time,
            demand_forecast=DEMAND_FORECAST,
            reward=float(current_reward.value),
            done=done
        )
        
        if done:
            obs.metadata["score"] = self._calculate_score()
            
        return obs

    def _calculate_score(self) -> float:
        """Programmatic grader: returns 0.0 to 1.0."""
        if self.task_id == "easy":
            # Optimal wait time is 0 (Driver 1 is in Indiranagar)
            # score = 1.0 if wait_time < 5, else 0.0
            return 1.0 if self.total_wait_time <= 5.0 else 0.0
        
        # For medium/hard, score based on average wait time
        avg_wait = self.total_wait_time / max(1, self.steps_taken)
        if avg_wait <= 15.0: return 1.0
        if avg_wait >= 45.0: return 0.0
        return 1.0 - (avg_wait - 15.0) / 30.0

    def step(self, action: CabAction):
        selected_driver_id = action.driver_id
        driver = next((d for d in self.drivers if d.driver_id == selected_driver_id), None)
        
        if not driver or driver.status != "IDLE":
            reward = CabReward(wait_time_penalty=0.0, positioning_penalty=0.0, invalid_action_penalty=100.0)
            return self._make_observation(reward=reward, done=True)

        pickup = self.pending_request["pickup"]
        dropoff = self.pending_request["dropoff"]
        
        wait_time_rider = TRAVEL_TIMES[driver.current_zone][pickup]
        travel_time_trip = TRAVEL_TIMES[pickup][dropoff]
        
        self.total_wait_time += wait_time_rider
        self.steps_taken += 1
        
        # Reward logic: penalize wait time and low demand at destination
        expected_idle_at_dest = (1.0 - DEMAND_FORECAST[dropoff]) * 30.0
        reward = CabReward(
            wait_time_penalty=float(wait_time_rider),
            positioning_penalty=float(expected_idle_at_dest)
        )
        
        # Update driver state
        driver.current_zone = dropoff
        self.simulation_time += wait_time_rider + travel_time_trip

        # Generate next request
        self.pending_request = self._generate_request()
        self._state.step_count += 1
        self._state.simulation_time = self.simulation_time
        
        done = self._state.step_count >= self.max_steps
        return self._make_observation(reward=reward, done=done)

    @property
    def state(self):
        return self._state
