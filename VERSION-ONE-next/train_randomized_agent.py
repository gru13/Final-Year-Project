import os
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import BaseCallback
from randomized_dssat_env import RandomizedDSSATEnv

# --- DEFINE THE CUSTOM CALLBACK CLASS ---
class SaveOnEpisodeEndCallback(BaseCallback):
    """
    A custom callback that saves the model at the end of each episode.
    """
    def __init__(self, save_path: str, verbose=1):
        super(SaveOnEpisodeEndCallback, self).__init__(verbose)
        self.save_path = save_path

    def _on_step(self) -> bool:
        """
        This method is called after each step in the environment.
        It must be implemented, but we don't need it to do anything.
        """
        return True

    def _on_rollout_end(self) -> bool:
        """
        This method is called at the end of each rollout (i.e., episode).
        """
        self.model.save(self.save_path)
        if self.verbose > 0:
            print(f"💾 Saving model checkpoint to {self.save_path}.zip after episode")
        return True

# --- Define Simulation Parameter Ranges ---
PARAMETER_RANGES = {
    'lat_range': (10.0, 15.0),
    'lon_range': (75.0, 80.0),
    'year_range': (2010, 2020),
    'planting_day_range': (150, 180)
}

# --- Define Workspace and API Key ---
WORKSPACE = "./randomized_env_workspace"
OWM_API_KEY = "eddbc7c0c9e63e225934add809624c6e"

# --- Create the Randomized DSSAT Environment ---
print("🚀 Initializing Randomized Training Environment...")
env = RandomizedDSSATEnv(
    parameter_ranges=PARAMETER_RANGES,
    workspace_dir=WORKSPACE,
    api_key=OWM_API_KEY
)

# --- Update Model Loading and Creation Logic ---
MODEL_SAVE_PATH = "sac_randomized_dssat_latest_model"
model_zip_path = f"{MODEL_SAVE_PATH}.zip"

if os.path.exists(model_zip_path):
    print(f"🧠 Found existing model. Loading from {model_zip_path} to continue training...")
    # Load the model and pass the environment. SB3 will handle the logger.
    model = SAC.load(model_zip_path, env=env)
    # ❌ THE LINE BELOW WAS REMOVED AS IT CAUSED THE ERROR ❌
    # model.set_logger(env.logger)
else:
    print("🧠 No existing model found. Creating a new SAC Agent...")
    model = SAC(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log="./sac_randomized_tensorboard/"
    )

TRAINING_TIMESTEPS = 20000

# --- Use the Callback in the Training Loop ---
callback = SaveOnEpisodeEndCallback(save_path=MODEL_SAVE_PATH)

print(f"\n💪 Starting/Continuing Training for {TRAINING_TIMESTEPS} timesteps...")
print("The agent will now train on a different, randomly generated environment for each episode.")
model.learn(
    total_timesteps=TRAINING_TIMESTEPS,
    log_interval=1,
    callback=callback,
    reset_num_timesteps=False
)

# --- Final Save ---
print(f"\n💾 Saving final model to {MODEL_SAVE_PATH}.zip")
model.save(MODEL_SAVE_PATH)

print("\n✅ Training complete.")
env.close()