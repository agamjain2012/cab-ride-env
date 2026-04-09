import asyncio
import os
import sys
import textwrap
import re
from typing import List, Optional

from openai import OpenAI

# Import Cab Ride Environment Client and Models
try:
    from client import CabRideEnv
    from models import CabAction
except ImportError:
    # Handle cases where it might be run from different contexts
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    from client import CabRideEnv
    from models import CabAction

# Mandatory Environment Variables
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"

# Benchmark Settings
BENCHMARK = "cab_ride_env"
BASE_URL = os.getenv("BASE_URL") or "http://localhost:7860"
SUCCESS_THRESHOLD = 0.5

def clamp_score(score: float) -> float:
    """Ensure score is strictly within [0.0, 1.0]."""
    return min(max(float(score), 0.0), 1.0)

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

async def run_inference_for_task(client_ai: OpenAI, env: CabRideEnv, task_id: str):
    """Runs the inference loop for a single task."""
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task_id=task_id)
        obs = result.observation
        done = False
        step = 1

        while not done:
            # Format observation for LLM
            drivers_str = "\n".join([
                f"- Driver {d.driver_id} at {d.current_zone} (ETA to pickup: {d.eta_to_pickup} mins)"
                for d in obs.available_drivers
            ])
            
            prompt = f"""
You are a cab dispatcher in Bengaluru managing task: {task_id}.
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
            
            try:
                response = client_ai.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=5,
                    temperature=0
                )
                action_str = (response.choices[0].message.content or "").strip()
            except Exception as e:
                print(f"[DEBUG] LLM API call failed: {e}", flush=True)
                action_str = "0"

            # Robust parsing
            match = re.search(r"\d+", action_str)
            driver_id = int(match.group()) if match else 0

            try:
                result = await env.step(CabAction(driver_id=driver_id))
                obs = result.observation
                reward = result.reward
                done = result.done
            except Exception as e:
                print(f"[DEBUG] Environment step failed: {e}", flush=True)
                done = True
                break

            rewards.append(reward)
            steps_taken = step
            log_step(step=step, action=action_str, reward=reward, done=done, error=None)
            
            if done:
                break
            step += 1

        # Retrieve score from final metadata
        score = clamp_score(obs.metadata.get("score", 0.0))
        success = score >= SUCCESS_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Inference error on task {task_id}: {e}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

async def main() -> None:
    if not API_KEY:
        print("[DEBUG] HF_TOKEN or API_KEY environment variable not set.", flush=True)
        return

    client_ai = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    # Run all 3 tasks
    tasks = ["easy", "medium", "hard"]
    
    try:
        async with CabRideEnv(base_url=BASE_URL) as env:
            for task_id in tasks:
                await run_inference_for_task(client_ai, env, task_id)
    except Exception as e:
        print(f"[DEBUG] Connection error: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
