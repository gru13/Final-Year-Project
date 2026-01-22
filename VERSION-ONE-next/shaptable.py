import glob
import os
import pandas as pd
import numpy as np
import shap
from sklearn.ensemble import RandomForestRegressor

# --- CONFIGURATION ---
# UPDATE THIS PATH to your actual logs folder
LOG_FOLDER = r"D:\Final-Year-Project\VERSION-ONE-next\randomized_env_workspace\episode_logs"

FEATURE_COLUMNS = [
    'DAP', 'days_since_last_rain', 'rainfall_7day', 'phenological_stage',
    'leaf_area_index', 'total_biomass', 'soil_water_content_0_30cm',
    'soil_water_content_30_60cm', 'soil_water_content_60_100cm',
    'available_water_fraction', 'water_stress_factor', 'temperature_avg',
    'solar_radiation', 'days_since_last_irrigation', 'forecast'
]
TARGET_COLUMN = 'action_irrigation_mm'

def generate_global_table():
    print(f"📂 Scanning folder: {LOG_FOLDER}...")
    all_files = glob.glob(os.path.join(LOG_FOLDER, "*.csv"))
    
    if not all_files:
        print("❌ No CSV files found!")
        return

    # 1. LOAD ALL DATA (The "Big Data" Step)
    print(f"   Merging {len(all_files)} log files...")
    df_list = [pd.read_csv(f) for f in all_files]
    master_df = pd.concat(df_list, axis=0, ignore_index=True)
    
    print(f"✅ Loaded Dataset: {len(master_df)} total decisions.")

    X = master_df[FEATURE_COLUMNS]
    y = master_df[TARGET_COLUMN]

    # 2. TRAIN GLOBAL SURROGATE
    # We use a slightly deeper tree (depth=12) because we have more data now
    print("🧠 Training Global Surrogate Model on entire history...")
    model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    score = model.score(X, y)
    print(f"✅ Global Model Accuracy (R2): {score:.2f}")

    # 3. CALCULATE GLOBAL IMPORTANCE
    # To save time, we sample 2000 random points if the dataset is huge
    # (Statistical significance is still preserved)
    sample_size = min(2000, len(X))
    print(f"Mö Calculating SHAP values on {sample_size} representative samples...")
    
    X_sample = X.sample(n=sample_size, random_state=42)
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_sample)

    # 4. GENERATE THE TABLE
    # Global Importance = The Average Absolute SHAP Value for each feature
    # (i.e., How much does this feature move the needle on average?)
    global_importance = np.abs(shap_values.values).mean(0)
    
    table_data = []
    for i, feature_name in enumerate(FEATURE_COLUMNS):
        table_data.append({
            "Feature Name": feature_name,
            "Global Importance (Avg Impact in mm)": round(global_importance[i], 4)
        })

    # Sort by Importance
    results_df = pd.DataFrame(table_data)
    results_df = results_df.sort_values(by='Global Importance (Avg Impact in mm)', ascending=False)
    
    # 5. OUTPUT
    print("\n" + "="*60)
    print("🌍 GLOBAL FEATURE IMPORTANCE TABLE (For All Logs)")
    print("="*60)
    print(results_df.to_string(index=False))
    
    output_csv = "global_feature_importance.csv"
    results_df.to_csv(output_csv, index=False)
    print("\n" + "="*60)
    print(f"✅ Saved to: {output_csv}")
    print("👉 Copy this table into your 'Results' section to prove your strategy.")

if __name__ == "__main__":
    generate_global_table()