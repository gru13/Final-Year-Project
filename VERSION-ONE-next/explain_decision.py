import pandas as pd
import numpy as np
import shap
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
import sys

# --- CONFIGURATION ---
# The columns in your log that represent the "State" (Inputs)
FEATURE_COLUMNS = [
    'DAP', 'days_since_last_rain', 'rainfall_7day', 'phenological_stage',
    'leaf_area_index', 'total_biomass', 'soil_water_content_0_30cm',
    'soil_water_content_30_60cm', 'soil_water_content_60_100cm',
    'available_water_fraction', 'water_stress_factor', 'temperature_avg',
    'solar_radiation', 'days_since_last_irrigation', 'forecast'
]
# The column representing the "Action" (Output)
TARGET_COLUMN = 'action_irrigation_mm'

def explain_log(log_filename, day_to_explain=None):
    print(f"📂 Loading log: {log_filename}...")
    try:
        df = pd.read_csv(log_filename)
    except FileNotFoundError:
        print("❌ File not found.")
        return

    # 1. Train a Surrogate Model (The "Mimic")
    # We train this simple model to learn exactly what your Agent did in this episode.
    print("🧠 Training surrogate model to mimic the agent's behavior...")
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)
    
    # Check how well it learned (R2 score)
    score = model.score(X, y)
    print(f"✅ Surrogate Model Accuracy: {score:.2f} (1.0 means perfect mimicry)")

    # 2. Setup SHAP Explainer
    print("Mö Calculating explanations (this might take a moment)...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # 3. Explain a Specific Moment
    if day_to_explain:
        # Find the row corresponding to the specific DAP (Day After Planting)
        row_mask = df['DAP'] == day_to_explain
        if not row_mask.any():
            print(f"❌ Day {day_to_explain} not found in log.")
            return
        
        row_index = df.index[row_mask][0]
        actual_action = df.iloc[row_index][TARGET_COLUMN]
        
        print(f"\n--- 🔍 ANALYSIS FOR DAY {day_to_explain} ---")
        print(f"💧 Agent Irrigated: {actual_action:.2f} mm")
        
        # Get the SHAP values for this specific row
        vals = shap_values[row_index]
        
        # Sort features by how much they pushed the decision
        feature_importance = pd.DataFrame(list(zip(FEATURE_COLUMNS, vals)), columns=['Feature', 'Impact'])
        feature_importance['Abs_Impact'] = feature_importance['Impact'].abs()
        feature_importance = feature_importance.sort_values(by='Abs_Impact', ascending=False)
        
        print("\nWhy did it do this?")
        for _, row in feature_importance.head(5).iterrows():
            impact_direction = "INCREASED" if row['Impact'] > 0 else "DECREASED"
            print(f"   • {row['Feature']} {impact_direction} irrigation by {abs(row['Impact']):.2f}mm")

        # Generate a "Force Plot" for this single decision
        plt.figure(figsize=(20, 3))
        shap.force_plot(
            explainer.expected_value, 
            vals, 
            X.iloc[row_index], 
            matplotlib=True, 
            show=False
        )
        output_img = f"explanation_day_{day_to_explain}.png"
        plt.savefig(output_img, bbox_inches='tight', dpi=300)
        print(f"\n🖼️  Saved visual explanation to: {output_img}")

    else:
        # Global Summary
        print("\n--- 🌍 GLOBAL POLICY EXPLANATION ---")
        print("Creating summary plot for the entire episode...")
        plt.figure()
        shap.summary_plot(shap_values, X, show=False)
        plt.savefig("global_explanation.png", bbox_inches='tight', dpi=300)
        print("🖼️  Saved global summary to: global_explanation.png")

if __name__ == "__main__":
    # Example Usage: Explain Day 45 of Episode 2
    # You can change the filename and day below
    target_log = r"D:\Final-Year-Project\VERSION-ONE-next\randomized_env_workspace\episode_logs\episode_0052_log.csv" 
    target_day = 10
    
    explain_log(target_log, day_to_explain=target_day)