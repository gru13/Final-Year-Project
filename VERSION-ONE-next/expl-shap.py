import pandas as pd
import shap
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
import os

# --- 1. CONFIGURATION ---
# UPDATE THIS to your "Best Case" file (e.g., episode_0052.csv)
LOG_FILE = r"D:\Final-Year-Project\VERSION-ONE-next\randomized_env_workspace\episode_logs\episode_0089_log.csv"

FEATURE_COLUMNS = [
    'DAP', 'days_since_last_rain', 'rainfall_7day', 'phenological_stage',
    'leaf_area_index', 'total_biomass', 'soil_water_content_0_30cm',
    'soil_water_content_30_60cm', 'soil_water_content_60_100cm',
    'available_water_fraction', 'water_stress_factor', 'temperature_avg',
    'solar_radiation', 'days_since_last_irrigation', 'forecast'
]
TARGET_COLUMN = 'action_irrigation_mm'

def generate_simple_plots():
    print(f"📂 Loading log: {LOG_FILE}...")
    if not os.path.exists(LOG_FILE):
        print("❌ File not found.")
        return

    df = pd.read_csv(LOG_FILE)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # 1. Train the Surrogate (The Translator)
    print("🧠 Training surrogate model...")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)

    # 2. Calculate SHAP (The Explanation)
    print("Mö Calculating simple explanations...")
    explainer = shap.TreeExplainer(model)
    # IMPORTANT: We use explainer(X) to get the full Explanation Object
    shap_values = explainer(X)

    # --- PLOT 1: THE GLOBAL BAR CHART (Simplest Overview) ---
    # This just answers: "What matters most?"
    plt.figure()
    shap.plots.bar(shap_values, show=False, max_display=10)
    plt.title("What drives the Agent's decisions? (Global Importance)")
    plt.savefig("simple_global_bar.png", bbox_inches='tight', dpi=300)
    print("✅ Saved 'simple_global_bar.png' (Use this for Strategy Slide)")

    # --- PLOT 2: THE WATERFALL CHART (Simplest Decision) ---
    # Find the day with the BIGGEST irrigation
    max_idx = y.idxmax()
    day_num = df.loc[max_idx, 'DAP']
    
    print(f"🔍 Creating receipt for Day {day_num} (Irrigation: {y[max_idx]:.2f}mm)")
    
    plt.figure()
    # This generates the "Receipt" style plot
    shap.plots.waterfall(shap_values[max_idx], show=False, max_display=7)
    plt.title(f"Why did I irrigate on Day {day_num}?")
    plt.savefig(f"simple_decision_day_{day_num}.png", bbox_inches='tight', dpi=300)
    print(f"✅ Saved 'simple_decision_day_{day_num}.png' (Use this for Case Study)")

if __name__ == "__main__":
    generate_simple_plots()