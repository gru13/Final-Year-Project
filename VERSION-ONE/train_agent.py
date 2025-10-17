import os
from stable_baselines3 import SAC
from dynamic_dssat_env import DynamicDSSATEnv

# --- 1. Define Simulation Parameters ---
# These must be consistent between training and evaluation
LAT = 12.3811
LON = 78.9366
START_DATE = "2014-01-01"
END_DATE = "2014-12-31"
PLANTING_DATE = "2014-06-02"
WORKSPACE = "./dynamic_env_workspace_train"
OWM_API_KEY = "eddbc7c0c9e63e225934add809624c6e" # Use your key if needed

# --- 2. Create the DSSAT Environment ---
print("🚀 Initializing Training Environment...")
env = DynamicDSSATEnv(
    lat=LAT,
    lon=LON,
    start_date=START_DATE,
    end_date=END_DATE,
    planting_date=PLANTING_DATE,
    workspace_dir=WORKSPACE,
    api_key=OWM_API_KEY
)

# --- 3. Create and Train the SAC Agent ---
# SAC is well-suited for continuous action spaces like irrigation amount
print("🧠 Creating SAC Agent...")
model = SAC(
    "MlpPolicy",          # Use a standard Multi-Layer Perceptron policy
    env,
    verbose=1,            # Print training progress
    tensorboard_log="./sac_dssat_tensorboard/"
)

# Train the agent for a specified number of timesteps
# Start with a smaller number (e.g., 10,000) to test the pipeline.
# For real results, you'll need significantly more (e.g., 100,000+).
TRAINING_TIMESTEPS = 10000
MODEL_SAVE_PATH = "sac_dssat_model"

print(f"\n💪 Starting Training for {TRAINING_TIMESTEPS} timesteps...")
model.learn(total_timesteps=TRAINING_TIMESTEPS)

# --- 4. Save the Trained Model ---
print(f"\n💾 Saving trained model to {MODEL_SAVE_PATH}.zip")
model.save(MODEL_SAVE_PATH)

print("\n✅ Training complete.")
env.close()