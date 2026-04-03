---
title: Cab Ride RL Environment
emoji: 🚕
colorFrom: yellow
colorTo: black
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Cab Ride Environment (Bengaluru)

Idea inspired from [link](https://www.uber.com/in/en/blog/reinforcement-learning-for-modeling-marketplace-balance/).
This is an attempt to build a real-world task simulation for cab ride dispatching in Bengaluru.

## Motivation
In a large city like Bengaluru, efficient cab dispatching is critical. A dispatcher must balance immediate rider satisfaction (Wait Time) with future driver efficiency (Driver Positioning). This environment provides a realistic simulation of these trade-offs, requiring agents to manage a fleet of drivers across discrete city zones with varying demand levels.

## Environment Overview
The agent acts as a centralized dispatcher. At each step, a new ride request appears at a specific `pickup_location` with a `dropoff_location`. The agent must select one of the `available_drivers` to fulfill the request.

### Bengaluru Zones
The city is modeled using 10 major hubs:
- **Central/Business:** MG Road, Indiranagar
- **Residential/Tech Hubs:** Koramangala, HSR Layout, Jayanagar, JP Nagar
- **Major Tech Parks:** Whitefield, Marathahalli, Electronic City, Bellandur

Travel times are pre-defined in a matrix (ranging from 15 to 45 minutes) to simulate city traffic.

## Action Space
The action is a single integer representing the `driver_id` of the driver assigned to the current request.
- `driver_id` (int): Must be one of the IDs in the `available_drivers` list.

## Observation Space
| Field | Type | Description |
|-------|------|-------------|
| `pickup_location` | `str` | Zone where the rider is waiting. |
| `dropoff_location` | `str` | Zone where the rider wants to go. |
| `available_drivers` | `List[DriverInfo]` | Idle drivers with their current zone and ETA to the pickup. |
| `demand_forecast` | `Dict[str, float]` | 0.0 to 1.0 probability of future requests in each zone. |
| `simulation_time` | `float` | Current simulation clock in minutes. |

## Tasks & Expected Difficulty

| Task ID | Name | Steps | Drivers | Difficulty | Description |
|---------|------|-------|---------|------------|-------------|
| `easy` | Single Dispatch | 1 | 3 | Easy | One driver is exactly at the pickup location. Tests basic "closest driver" logic. |
| `medium` | Random Sequence | 20 | 5 | Medium | A series of random requests across the city. |
| `hard` | Residential Rush | 30 | 10 | Hard | Requests originate in low-demand residential zones and move to high-demand business hubs. Requires strategic positioning. |

## Programmatic Grader
Performance is scored from **0.0 to 1.0** based on the average rider wait time across the episode.
- **Score 1.0:** Average wait time ≤ 15 minutes.
- **Score 0.0:** Average wait time ≥ 45 minutes.
- **Linear interpolation** between 15 and 45 minutes.

## Setup and Usage

### Local Development (using uv)
1. Install dependencies: `uv sync`
2. Start server: `PYTHONPATH=src:envs/cab_ride_env uv run python envs/cab_ride_env/server/app.py`
3. Run example: `PYTHONPATH=src:envs/cab_ride_env uv run python examples/cab_ride_simple.py`

### Docker
```bash
docker build -t cab-ride-env envs/cab_ride_env/
docker run -p 8000:8000 cab-ride-env
```

## Baseline Scores
Reproducible results using `examples/cab_ride_inference.py` with GPT-4o:

| Task | Total Reward | Grader Score |
|------|--------------|--------------|
| Easy | -3.00 | 1.00 |
| Medium | -420.50 | 0.82 |
| Hard | -850.20 | 0.74 |
| **Final Baseline** | - | **0.85** |
