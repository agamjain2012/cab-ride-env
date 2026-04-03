import asyncio
import sys
import os

# Add the envs directory to sys.path to allow importing cab_ride_env
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from cab_ride_env import CabRideEnv, CabAction

async def main():
    # To run this, you need to start the server first:
    # cd OpenEnv/envs/cab_ride_env && uvicorn server.app:app --host 0.0.0.0 --port 8000
    
    print("Connecting to Cab Ride Environment...")
    try:
        # Use direct Space URL: https://<user>-<space>.hf.space
        async with CabRideEnv(base_url="https://agamjain90-cab-ride-env.hf.space") as client:
            print("Resetting environment...")
            result = await client.reset()
            obs = result.observation
            print(f"Pickup: {obs.pickup_location}, Dropoff: {obs.dropoff_location}")
            print(f"Simulation Time: {obs.simulation_time}")
            print(f"Available Drivers: {[f'ID:{d.driver_id} @ {d.current_zone} (ETA:{d.eta_to_pickup})' for d in obs.available_drivers]}")

            for i in range(5):
                if not obs.available_drivers:
                    print("No drivers available!")
                    break
                
                # Simple greedy policy: pick driver with lowest ETA
                selected_driver = min(obs.available_drivers, key=lambda d: d.eta_to_pickup)
                print(f"\nStep {i+1}: Selecting Driver {selected_driver.driver_id} (ETA: {selected_driver.eta_to_pickup})")
                
                result = await client.step(CabAction(driver_id=selected_driver.driver_id))
                obs = result.observation
                
                print(f"Reward: {result.reward}")
                print(f"New Pickup: {obs.pickup_location}, Dropoff: {obs.dropoff_location}")
                print(f"Simulation Time: {obs.simulation_time}")
                
                if result.done:
                    print("Episode finished.")
                    break
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure the server is running:")
        print("cd OpenEnv/envs/cab_ride_env && uvicorn server.app:app --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    asyncio.run(main())
