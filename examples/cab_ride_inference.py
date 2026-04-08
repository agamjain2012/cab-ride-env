import asyncio
import os
import sys
from openai import OpenAI

# Add the envs directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from cab_ride_env import CabRideEnv, CabAction

# Initialize OpenAI client
client_ai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def clamp_score(score: float) -> float:
    return min(max(float(score), 0.01), 0.99)

async def run_task(task_id: str):
    print(f"\n--- Starting Task: {task_id} ---")
    async with CabRideEnv(base_url="http://localhost:8000") as client:
        result = await client.reset(task_id=task_id)
        obs = result.observation
        done = False
        total_reward = 0.0

        while not done:
            # Format observation for LLM
            drivers_str = "\n".join([
                f"- Driver {d.driver_id} at {d.current_zone} (ETA to pickup: {d.eta_to_pickup} mins)"
                for d in obs.available_drivers
            ])
            
            prompt = f"""
You are a cab dispatcher in Bengaluru.
Current Request:
- Pickup: {obs.pickup_location}
- Dropoff: {obs.dropoff_location}

Available Drivers:
{drivers_str}

Zone Demand Forecast (Higher is better for driver positioning):
{obs.demand_forecast}

Choose the best driver ID to minimize wait time and maximize future efficiency. 
Respond with ONLY the driver ID number.
"""
            
            response = client_ai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0
            )
            
            try:
                driver_id = int(response.choices[0].message.content.strip())
            except ValueError:
                print(f"LLM gave invalid response: {response.choices[0].message.content}")
                driver_id = obs.available_drivers[0].driver_id

            result = await client.step(CabAction(driver_id=driver_id))
            obs = result.observation
            done = result.done
            total_reward += result.reward
            
        score = clamp_score(obs.metadata.get("score", 0.01))
        print(f"Task {task_id} Finished. Total Reward: {total_reward:.2f}, Grader Score: {score:.2f}")
        return score

async def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    tasks = ["easy", "medium", "hard"]
    scores = []
    for t in tasks:
        try:
            score = await run_task(t)
            scores.append(score)
        except Exception as e:
            print(f"Error running task {t}: {e}")
    
    avg_score = sum(scores) / len(scores) if scores else 0.01
    print(f"\nFinal Baseline Score: {avg_score:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
