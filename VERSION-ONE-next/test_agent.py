import gymnasium as gym
from stable_baselines3 import SAC
from randomized_dssat_env import RandomizedDSSATEnv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
MODEL_PATH = "sac_randomized_dssat_latest_model.zip"
WORKSPACE_PATH = "./randomized_env_workspace"
EPISODES_TO_TEST = 5

# Define the same ranges as training
param_ranges = {
    'lat_range': (10.0, 15.0),  # South India
    'lon_range': (75.0, 80.0),
    'year_range': (2010, 2018),
    'planting_day_range': (152, 182) # June 1 - July 1
}

def run_test():
    # 1. Setup Environment
    env = RandomizedDSSATEnv(param_ranges, WORKSPACE_PATH)
    
    # 2. Load the Trained Agent
    print(f"🧠 Loading model from {MODEL_PATH}...")
    try:
        model = SAC.load(MODEL_PATH)
    except FileNotFoundError:
        print("❌ Model file not found! Make sure training finished successfully.")
        return

    results = []

    # 3. Run Testing Loop
    for ep in range(EPISODES_TO_TEST):
        print(f"\n--- Testing Episode {ep+1}/{EPISODES_TO_TEST} ---")
        obs, _ = env.reset()
        done = False
        truncated = False
        
        total_reward = 0
        logs = []
        
        while not (done or truncated):
            # Deterministic=True means "Use your best strategy, don't experiment"
            action, _ = model.predict(obs, deterministic=True)
            
            obs, reward, done, truncated, info = env.step(action)
            total_reward += reward
            
            # Capture data from the environment's last log entry
            if env.current_episode_data:
                logs.append(env.current_episode_data[-1])

        # Episode Summary
        if logs:
            df = pd.DataFrame(logs)
            rain_sum = df['rainfall_7day'].mean() # approx
            irr_sum = df['action_irrigation_mm'].sum()
            yield_val = df['total_biomass'].max()
            
            print(f"✅ Result: Rain={rain_sum:.1f}mm | Irr={irr_sum:.1f}mm | Yield={yield_val:.0f} kg/ha")
            
            results.append({
                'Episode': ep+1,
                'Rain': rain_sum,
                'Irrigation': irr_sum,
                'Yield': yield_val
            })

    # 4. Simple Report
    res_df = pd.DataFrame(results)
    print("\n--- 📊 FINAL TEST REPORT ---")
    print(res_df)
    res_df.to_csv("final_test_results.csv", index=False)
    print("Saved results to final_test_results.csv")

if __name__ == "__main__":
    run_test()