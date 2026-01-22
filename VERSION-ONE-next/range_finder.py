import glob
import os
import pandas as pd

# --- CONFIGURATION ---
# UPDATE THIS PATH to your actual logs folder
LOG_FOLDER = r"D:\Final-Year-Project\VERSION-ONE-next\randomized_env_workspace\episode_logs"

def get_data_ranges():
    print(f"📂 Scanning folder: {LOG_FOLDER}...")
    all_files = glob.glob(os.path.join(LOG_FOLDER, "*.csv"))
    
    if not all_files:
        print("❌ No CSV files found! Check your path.")
        return

    print(f"   Found {len(all_files)} log files. Merging data...")
    
    # 1. Load and Merge all files
    # We use a list generator for speed
    df_list = [pd.read_csv(f) for f in all_files]
    master_df = pd.concat(df_list, axis=0, ignore_index=True)
    
    print(f"✅ Loaded {len(master_df)} total timesteps (decisions).")
    print("-" * 60)
    print(f"{'FEATURE':<35} | {'MIN':<10} | {'MAX':<10} | {'MEAN':<10}")
    print("-" * 60)

    # 2. Calculate Min/Max for every column
    # We exclude non-numeric columns just in case
    numeric_df = master_df.select_dtypes(include=['float64', 'int64'])

    for col in numeric_df.columns:
        min_val = numeric_df[col].min()
        max_val = numeric_df[col].max()
        mean_val = numeric_df[col].mean()
        
        # Print formatted row
        print(f"{col:<35} | {min_val:<10.2f} | {max_val:<10.2f} | {mean_val:<10.2f}")

    print("-" * 60)
    
    # 3. Check for Anomalies (Optional but smart)
    # Example: If soil moisture is negative, something is wrong.
    if 'soil_water_content_0_30cm' in numeric_df.columns:
        if numeric_df['soil_water_content_0_30cm'].min() < 0:
            print("\n⚠️ ALERT: Negative Soil Moisture detected! Check your simulation code.")
        else:
            print("\n✅ Data Health Check: Soil Moisture ranges look valid (Non-negative).")

if __name__ == "__main__":
    get_data_ranges()