import os
import pandas as pd
import numpy as np
import requests
import time
import logging
import sys
from typing import List, Dict

# Suppress DeprecationWarning if DSSATTools is imported elsewhere
import warnings
warnings.filterwarnings(
    "ignore",
    message="DSSATTools version 3.0.0 is a major upgrade.*",
    category=DeprecationWarning
)

try:
    from DSSATTools import SoilProfile, SoilLayer
    from DSSATTools.soil import estimate_from_texture
except ImportError:
    print("❌ DSSATTools not found. Please install it using: pip install DSSATTools")
    sys.exit(1)


# --- Configuration Constants ---
SOILGRIDS_DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
SOILGRIDS_PROPERTIES = [
    "sand", "silt", "clay", "bdod", "cfvo", "wv0033", "wv1500",
    "soc", "phh2o", "cec", "nitrogen"
]

# --- Helper Functions (copied from flow.ipynb) ---

def _fetch_soilgrids_data_robust(latitude: float, longitude: float, properties: List[str], depths: List[str]) -> pd.DataFrame:
    """Fetches soil property data robustly with a retry mechanism."""
    logging.info(f"Fetching SoilGrids data for lat={latitude}, lon={longitude}")
    base_url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    all_properties_data = []
    max_retries = 4
    initial_retry_delay_seconds = 5

    for prop in properties:
        logging.info(f"--> Fetching property: {prop}")
        params = {'lon': longitude, 'lat': latitude, 'property': prop, 'depth': depths, 'value': 'mean'}
        for attempt in range(max_retries):
            try:
                response = requests.get(base_url, params=params, timeout=45)
                response.raise_for_status()
                data = response.json()
                layers = data.get('properties', {}).get('layers', [])
                if not layers:
                    logging.warning(f"No layer data for {prop}. Skipping.")
                    break
                parsed_data = {
                    depth_data['label']: depth_data.get('values', {}).get('mean', np.nan)
                    for depth_data in layers[0]['depths']
                }
                prop_df = pd.DataFrame.from_dict(parsed_data, orient='index', columns=[prop])
                all_properties_data.append(prop_df)
                time.sleep(1)
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [429, 503] and attempt < max_retries - 1:
                    wait_time = initial_retry_delay_seconds * (2 ** attempt)
                    logging.warning(f"Rate limit or server error for '{prop}'. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"HTTP error for '{prop}': {e}. It will be missing.")
                    break
            except (requests.exceptions.RequestException, ValueError, KeyError) as e:
                logging.error(f"Failed on property '{prop}': {e}. Skipping.")
                break
    if not all_properties_data:
        raise ValueError("Failed to fetch any data from SoilGrids.")
    final_df = pd.concat(all_properties_data, axis=1).reindex(depths)
    for prop in properties:
        if prop not in final_df.columns:
            final_df[prop] = np.nan
    return final_df

def _process_and_estimate_dssat_format(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Converts raw SoilGrids data and calculates hydraulic properties."""
    logging.info("Processing raw data and estimating hydraulic properties with DSSATTools...")
    
    dssat_df = pd.DataFrame(index=raw_df.index)
    dssat_df['SLB'] = [int(label.split('-')[1].replace('cm', '')) for label in raw_df.index]
    dssat_df['SLOC'] = raw_df['soc'] / 1000  # Correct conversion from dg/kg to kg/kg
    dssat_df['SLNI'] = raw_df['nitrogen'] / 10000 # Correct conversion from cg/kg to kg/kg
    dssat_df['SLHW'] = raw_df['phh2o'] / 10
    dssat_df['SCEC'] = raw_df['cec'] / 10
    dssat_df['SLCF'] = raw_df['cfvo'] / 10
    
    rgf_map = {'0-5cm': 1.0, '5-15cm': 1.0, '15-30cm': 1.0, '30-60cm': 0.8, '60-100cm': 0.5, '100-200cm': 0.2}
    dssat_df['SRGF'] = dssat_df.index.map(rgf_map)
    
    dssat_df['SLCL'] = raw_df['clay'] / 10
    dssat_df['SLSI'] = raw_df['silt'] / 10
    dssat_df['SBDM'] = raw_df['bdod'] / 100
    
    # Corrected: Convert wv0033 and wv1500 to fractions by dividing by 1000
    dssat_df['SDUL'] = raw_df['wv0033'] / 1000.0
    dssat_df['SLLL'] = raw_df['wv1500'] / 1000.0

    for index, row in dssat_df.iterrows():
        if pd.notna(row['SLCL']) and pd.notna(row['SLSI']) and pd.notna(row['SBDM']):
            try:
                estimated_props = estimate_from_texture(slcl=row['SLCL'], slsi=row['SLSI'], sbdm=row['SBDM'])
                dssat_df.loc[index, 'SSAT'] = estimated_props['ssat']
                dssat_df.loc[index, 'SSKS'] = estimated_props['ssks']
            except Exception as e:
                logging.warning(f"Could not estimate SSAT/SSKS for layer {index}: {e}. Using NaN.")
                dssat_df.loc[index, 'SSAT'] = np.nan
                dssat_df.loc[index, 'SSKS'] = np.nan
        else:
            logging.warning(f"Missing texture/bulk density for layer {index}. Cannot estimate SSAT/SSKS.")

    return dssat_df

def _get_texture_class(sand: float, silt: float, clay: float) -> str:
    """Determines USDA soil texture class from sand, silt, clay percentages."""
    if (silt + 1.5 * clay) < 15: return 'S'
    if (silt + 1.5 * clay) >= 15 and (silt + 2 * clay) < 30: return 'LS'
    if (clay >= 7 and clay < 20) and (sand > 52) and ((silt + 2 * clay) >= 30): return 'SL'
    if (clay < 7) and (silt < 50) and ((silt + 2 * clay) >= 30): return 'SL'
    if (clay >= 7 and clay < 27) and (silt >= 28 and silt < 50) and (sand <= 52): return 'L'
    if (silt >= 50 and clay >= 12 and clay < 27): return 'SIL'
    if (silt >= 50 and clay < 12) or (silt >= 80 and clay < 12): return 'SI'
    if (clay >= 20 and clay < 35) and (silt < 28) and (sand > 45): return 'SCL'
    if (clay >= 27 and clay < 40) and (sand > 20 and sand <= 45): return 'CL'
    if (clay >= 27 and clay < 40) and (sand <= 20): return 'SICL'
    if (clay >= 35) and (sand > 45): return 'SC'
    if (clay >= 40) and (silt >= 40): return 'SIC'
    if (clay >= 40) and (sand <= 45) and (silt < 40): return 'C'
    return 'UNKNOWN'

def _write_sol_file_with_dssattools(df: pd.DataFrame, lat: float, lon: float, country: str, filename: str, soil_id: str):
    """Builds a SoilProfile object and writes it to a file."""
    logging.info(f"Building SoilProfile object with DSSATTools...")
    
    soil_layers = []
    for _, row in df.iterrows():
        # Ensure required keys exist, even if NaN, before creating the layer
        row_dict = row.to_dict()
        for key in ['slll', 'sdul', 'ssat']:
            if key.upper() not in row_dict or pd.isna(row_dict[key.upper()]):
                 raise ValueError(f"Missing required hydraulic property '{key.upper()}' for a soil layer.")
        
        kwargs = {k.lower(): v for k, v in row_dict.items() if pd.notna(v)}
        soil_layers.append(SoilLayer(**kwargs))

    top_layer = df.iloc[0]
    sand_pct = 100 - top_layer.get('SLCL', 0) - top_layer.get('SLSI', 0)
    texture = _get_texture_class(sand_pct, top_layer.get('SLSI', 0), top_layer.get('SLCL', 0))
    
    SLDR_LOOKUP = {
        'S': 0.75, 'LS': 0.70, 'SL': 0.65, 'L': 0.60, 'SIL': 0.55, 'SI': 0.55,
        'SCL': 0.50, 'CL': 0.50, 'SICL': 0.45, 'SC': 0.40, 'SIC': 0.35, 'C': 0.30,
    }
    sldr_value = SLDR_LOOKUP.get(texture, 0.5)
    logging.info(f"Determined soil texture as '{texture}', setting SLDR to {sldr_value}")
    
    soil_profile = SoilProfile(
        name=soil_id,
        soil_series_name='SoilGrids Auto-Generated Profile',
        soil_clasification=texture,
        site='SoilGrids',
        country=country,
        lat=lat,
        long=lon,
        salb=0.13, slu1=6.0, slro=75.0, 
        sldr=sldr_value,
        slnf=1.0, slpf=1.0,
        table=soil_layers
    )
    
    logging.info(f"Writing DSSAT .SOL file to {filename}")
    with open(filename, 'w') as f:
        f.write(soil_profile._write_sol())

# --- Main Function ---

def create_soil_file(lat: float, lon: float, output_dir: str, soil_id: str, country: str = "Generic") -> str:
    """
    Main function to generate a DSSAT soil file from SoilGrids data.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
    
    try:
        raw_soil_data = _fetch_soilgrids_data_robust(lat, lon, SOILGRIDS_PROPERTIES, SOILGRIDS_DEPTHS)
        final_dssat_profile = _process_and_estimate_dssat_format(raw_soil_data)

        print("\n--- Final Processed DSSAT Data ---")
        print(final_dssat_profile.round(3).to_string())

        lat_str = str(int(abs(lat * 100))).zfill(4)
        lon_str = str(int(abs(lon * 100))).zfill(4)
        output_filename = f"soil{lat_str}{lon_str}.SOL"
        output_path = os.path.join(output_dir, output_filename)

        _write_sol_file_with_dssattools(final_dssat_profile, lat, lon, country, output_path, soil_id)
        print(f"\n✅ Successfully created soil file using DSSATTools: {output_path}")

        print(f"\nVerifying '{output_path}' with soil ID '{soil_id}'...")
        SoilProfile.from_file(soil_id, output_path)
        print("✅ Verification successful! The file can be read by DSSATTools.")
        
        return output_path

    except Exception as e:
        logging.error(f"❌ Script failed during soil file creation: {e}")
        raise

if __name__ == "__main__":
    # Example usage when running the script directly
    print("Attempting to generate soil profile file from SoilGrids API...")
    LATITUDE = 12.3811
    LONGITUDE = 78.9366
    SOIL_ID = f"SG{str(int(abs(LATITUDE*100))):0>4}{str(int(abs(LONGITUDE*100))):0>4}"
    
    create_soil_file(
        lat=LATITUDE,
        lon=LONGITUDE,
        soil_id=SOIL_ID,    
        country="India",
        output_dir="." # Save to current directory
    )

