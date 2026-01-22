# import pandas as pd
# import shap
# import lime
# import lime.lime_tabular
# import numpy as np
# from sklearn.ensemble import RandomForestRegressor
# import os
# import requests
# import warnings

# # Suppress warnings for cleaner terminal output
# warnings.filterwarnings("ignore")

# # --- CONFIGURATION ---
# # UPDATE THIS to your actual log file path
# LOG_FILE = r"D:\Final-Year-Project\VERSION-ONE-next\randomized_env_workspace\episode_logs\episode_0052_log.csv"

# # We strictly use Gemma here
# OLLAMA_MODEL = "gemma3:latest"

# FEATURE_COLUMNS = [
#     'DAP', 'days_since_last_rain', 'rainfall_7day', 'phenological_stage',
#     'leaf_area_index', 'total_biomass', 'soil_water_content_0_30cm',
#     'soil_water_content_30_60cm', 'soil_water_content_60_100cm',
#     'available_water_fraction', 'water_stress_factor', 'temperature_avg',
#     'solar_radiation', 'days_since_last_irrigation', 'forecast'
# ]
# TARGET_COLUMN = 'action_irrigation_mm'

# def get_hybrid_explanation(target_dap):
#     print(f"\n📂 Loading log for Day {target_dap}...")
#     if not os.path.exists(LOG_FILE):
#         print("❌ File not found. Check your path.")
#         return

#     df = pd.read_csv(LOG_FILE)
#     day_row = df[df['DAP'] == target_dap]
    
#     if day_row.empty:
#         print(f"❌ Day {target_dap} not found.")
#         return

#     idx = day_row.index[0]
#     day_data = df.loc[idx, FEATURE_COLUMNS].values
#     action = df.loc[idx, TARGET_COLUMN]

#     # --- 1. TRAIN THE SURROGATE MODEL ---
#     print("🧠 Training Surrogate Model (Random Forest)...")
#     X = df[FEATURE_COLUMNS]
#     y = df[TARGET_COLUMN]
    
#     model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
#     model.fit(X, y)

#     # --- 2. GET SHAP VALUES (Game Theory) ---
#     print("📊 Calculating SHAP (Global Logic)...")
#     shap_explainer = shap.TreeExplainer(model)
#     shap_values = shap_explainer.shap_values(X)
#     sv = shap_values[idx]
    
#     # Extract top 3 SHAP drivers
#     shap_impacts = sorted(list(zip(FEATURE_COLUMNS, sv)), key=lambda x: abs(x[1]), reverse=True)[:3]
#     shap_text = ""
#     for name, val in shap_impacts:
#         direction = "increased irrigation" if val > 0 else "decreased irrigation"
#         shap_text += f"- {name}: {direction} (Impact: {val:.2f})\n"

#     # --- 3. GET LIME VALUES (Local Sensitivity) ---
#     print("🍋 Calculating LIME (Local Perturbation)...")
#     lime_explainer = lime.lime_tabular.LimeTabularExplainer(
#         training_data=np.array(X),
#         feature_names=FEATURE_COLUMNS,
#         class_names=['irrigation'],
#         mode='regression'
#     )
    
#     lime_exp = lime_explainer.explain_instance(
#         data_row=day_data, 
#         predict_fn=model.predict,
#         num_features=3
#     )
    
#     lime_list = lime_exp.as_list()
#     lime_text = ""
#     for condition, weight in lime_list:
#         lime_text += f"- Condition '{condition}' had weight {weight:.2f}\n"

#     # --- 4. GEMMA SYNTHESIS (The Judge) ---
#     print(f"🤖 Sending analysis to {OLLAMA_MODEL}...")
    
#     prompt = f"""
#     You are an expert Agricultural AI Assistant.
    
#     CONTEXT:
#     On Day {target_dap}, the system decided to irrigate {action:.2f} mm.
    
#     MATHEMATICAL EVIDENCE:
#     1. SHAP (Global Drivers):
#     {shap_text}
    
#     2. LIME (Local Conditions):
#     {lime_text}
    
#     INSTRUCTIONS:
#     Synthesize this evidence into ONE simple, natural sentence explaining WHY the system watered the field.
#     - Focus on the crop conditions (e.g. "soil was dry", "temperature was high").
#     - Do NOT mention "SHAP", "LIME", "perturbation", or specific numbers.
#     - Write as if you are speaking to a farmer.
#     """

#     url = "http://localhost:11434/api/generate"
#     data = {
#         "model": OLLAMA_MODEL,
#         "prompt": prompt,
#         "stream": False
#     }

#     try:
#         response = requests.post(url, json=data)
#         if response.status_code == 200:
#             result = response.json()
#             ai_text = result['response'].strip()
            
#             print("\n" + "="*60)
#             print(f"🗣️  GEMMA EXPLANATION (Day {target_dap}):")
#             print("="*60)
#             print(ai_text)
#             print("="*60)
#             print("✅ Verified by SHAP (Game Theory) & LIME (Sensitivity Analysis)")
            
#         else:
#             print("❌ Ollama Error:", response.text)
            
#     except Exception as e:
#         print(f"❌ Connection Failed. Make sure Ollama is running! (Error: {e})")

# if __name__ == "__main__":
#     # Change this to the day you want to explain
#     get_hybrid_explanation(30)


import pandas as pd
import ollama
import sys

# --- CONFIGURATION ---
LOG_FILE = r"D:\Final-Year-Project\VERSION-ONE-next\randomized_env_workspace\episode_logs\episode_0092_log.csv"
MODEL_NAME = "gemma3:latest"
TARGET_DAY = 76  # Change this to look at different days

def generate_explanation(row):
    """
    Constructs a prompt using DATASET STATISTICS (Min/Max/Mean) 
    so the LLM understands if a value is High or Low.
    """
    
    # 1. Extract and Format Data
    # Convert 0-1 range to Percentage for easier reading
    moisture_pct = row['soil_water_content_0_30cm'] * 100 
    
    # Dataset Statistics (Hardcoded from your range_finder.py results)
    # Mean: 34%, Min: 7%, Max: 48%
    moisture_status = "NORMAL"
    if moisture_pct < 20.0: 
        moisture_status = "VERY DRY (Below 20%)"
    elif moisture_pct < 34.0:
        moisture_status = "BELOW AVERAGE"
    
    stress = row['water_stress_factor']
    rain_7day = row['rainfall_7day']
    stage = row['phenological_stage']
    action = row['action_irrigation_mm']
    day = row['DAP']

    # 2. Construct the Context-Aware Prompt
    prompt = f"""
    You are an intelligent agricultural irrigation agent. 
    Analyze the decision for Day {day}.
    
    --- ENVIRONMENTAL CONTEXT (Based on 20,000 timesteps) ---
    * Normal Soil Moisture Range: 7% to 48% (Mean: 34%)
    * Normal Rainfall (7-day): 0 to 126 mm
    
    --- CURRENT SENSOR READINGS ---
    * Soil Moisture (0-30cm): {moisture_pct:.1f}% -> STATUS: {moisture_status}
    * Water Stress Factor: {stress:.3f} (0.0=Healthy, 1.0=Dead)
    * Rainfall (Last 7 Days): {rain_7day} mm
    * Crop Growth Stage: {stage} (0-7 scale)
    
    --- AGENT ACTION ---
    * Irrigated: {action} mm (Max capacity is 50mm)
    
    --- INSTRUCTION ---
    Explain WHY the agent chose to irrigate {action} mm.
    Use the context above. For example, if moisture is 17% and the mean is 34%, explicitly state that soil is 'severely dry'.
    """

    print(f"🤖 Sending analysis request to {MODEL_NAME}...")
    
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[
            {'role': 'user', 'content': prompt}
        ])
        return response['message']['content']
        
    except Exception as e:
        return f"❌ Error: {e}"

def main():
    try:
        print(f"📂 Loading {LOG_FILE}...")
        df = pd.read_csv(LOG_FILE)
    except FileNotFoundError:
        print(f"❌ Error: Could not find '{LOG_FILE}'.")
        return

    row_data = df[df['DAP'] == TARGET_DAY]
    
    if row_data.empty:
        print(f"❌ Error: Day {TARGET_DAY} not found in the log.")
        return

    current_row = row_data.iloc[0]
    explanation = generate_explanation(current_row)

    print("\n" + "="*60)
    print(f"🗣️  GEMMA 3 EXPLANATION (Day {TARGET_DAY})")
    print("="*60)
    print(explanation.strip())
    print("="*60 + "\n")

if __name__ == "__main__":
    main()