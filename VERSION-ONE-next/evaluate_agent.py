import numpy as np
import pandas as pd
from stable_baselines3 import SAC
from stable_baselines3.common.evaluation import evaluate_policy
from dynamic_dssat_env import DynamicDSSATEnv

# --- 1. Define Simulation Parameters ---
# Use the same parameters as in training
LAT = 12.3812
LON = 78.9362
START_DATE = "2012-01-01"
END_DATE = "2012-12-31"
PLANTING_DATE = "2012-02-02"
WORKSPACE = "./dynamic_env_workspace_eval" # Use a separate workspace
OWM_API_KEY = "eddbc7c0c9e63e225934add809624c6e"

# --- 2. Setup Environment and Load Model ---
print("🚀 Initializing Evaluation Environment...")
eval_env = DynamicDSSATEnv(
    lat=LAT,
    lon=LON,
    start_date=START_DATE,
    end_date=END_DATE,
    planting_date=PLANTING_DATE,
    workspace_dir=WORKSPACE,
    api_key=OWM_API_KEY
)

MODEL_PATH = "./sac_dssat_model1.zip"
print(f"🧠 Loading trained model from {MODEL_PATH}...")
model = SAC.load(MODEL_PATH)

# ====================================================================
# Method 1: Standard Evaluation using Stable Baselines3 Helper
# ====================================================================
print("\n--- Method 1: Running Standard SB3 Evaluation ---")
N_EVAL_EPISODES = 10
mean_reward, std_reward = evaluate_policy(
    model,
    eval_env,
    n_eval_episodes=N_EVAL_EPISODES,
    deterministic=True  # Use deterministic actions for evaluation
)
print(f"📈 Mean reward over {N_EVAL_EPISODES} episodes: {mean_reward:.2f} +/- {std_reward:.2f}")

# ====================================================================
# Method 2: Manual Evaluation for Detailed Insights
# ====================================================================
print("\n--- Method 2: Running Manual Rollout for Detailed Analysis ---")

episode_results = []

for i in range(N_EVAL_EPISODES):
    obs, info = eval_env.reset()
    done = False
    truncated = False
    
    total_reward = 0
    total_irrigation = 0
    final_yield = 0
    
    while not done and not truncated:
        # Use deterministic=True for the agent to pick the "best" action
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, done, truncated, info = eval_env.step(action)
        
        # Accumulate results
        total_reward += reward
        total_irrigation += float(action[0])

    # After the episode ends, get the final state from the environment
    # The 'harverst_grain_weight' is stored in the environment's state dict
    if eval_env.previous_state:
        final_yield = eval_env.previous_state.get('harverst_grain_weight', 0)

    episode_results.append({
        'episode': i + 1,
        'total_reward': total_reward,
        'total_irrigation_mm': total_irrigation,
        'final_yield_kg_ha': final_yield
    })
    
    print(f"  Episode {i+1:02d}: "
          f"Reward={total_reward:8.2f}, "
          f"Water={total_irrigation:7.1f} mm, "
          f"Yield={final_yield:8.1f} kg/ha")

# --- 3. Analyze and Display Results ---
print("\n--- Summary of Manual Evaluation ---")
results_df = pd.DataFrame(episode_results)
print(results_df.describe())

eval_env.close()