import os
import io
import sys
import logging
import numpy as np
import pandas as pd
from owslib.wcs import WebCoverageService
from concurrent.futures import ThreadPoolExecutor, as_completed

# Libraries for Coordinate math and Tiff reading
try:
    import rasterio
    from pyproj import Transformer
except ImportError:
    print("❌ Missing libraries. Run: pip install rasterio pyproj OWSLib")
    sys.exit(1)

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

try:
    from DSSATTools import SoilProfile, SoilLayer
    from DSSATTools.soil import estimate_from_texture
except ImportError:
    print("❌ DSSATTools not found. Please install it using: pip install DSSATTools")
    sys.exit(1)

# --- Configuration ---
SOILGRIDS_DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
# Note: nitrogen and phh2o map names often differ slightly in WCS, we handle this below.
SOILGRIDS_PROPERTIES = ["sand", "silt", "clay", "bdod", "cfvo", "soc", "phh2o", "cec", "nitrogen", "wv0033", "wv1500"]

# --- Helper: Coordinate Projection ---
def _latlon_to_homolosine(lat, lon):
    """
    Converts GPS (Lat/Lon) to SoilGrids Native (Homolosine Meters).
    Input: WGS84 (EPSG:4326)
    Output: Interrupted Goode Homolosine (IGH)
    """
    # Define the projection strings
    wgs84 = "EPSG:4326"
    # This is the standard proj string for Goode Homolosine
    igh = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"
    
    transformer = Transformer.from_crs(wgs84, igh, always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y

def _fetch_owslib_value(prop, depth, x_meter, y_meter):
    """
    Uses OWSLib to fetch a single pixel from the WCS 2.0.1 service.
    """
    # 1. Setup the Service Connection
    # Map filenames are usually just the property name, e.g., 'sand.map'
    map_url = f'http://maps.isric.org/mapserv?map=/map/{prop}.map'
    
    try:
        wcs = WebCoverageService(map_url, version='2.0.1')
        
        # 2. Construct the Coverage ID (e.g., 'sand_0-5cm_mean')
        cov_id = f"{prop}_{depth}_mean"
        
        # Check if this coverage exists in the contents
        if cov_id not in wcs.contents:
            # Sometimes Nitrogen is named 'nitrogen' but the map is 'nitrogen.map'
            logging.warning(f"  ⚠️ Coverage {cov_id} not found in {map_url}")
            return np.nan

        # 3. Define the Subset (The Slice)
        # We want a tiny 1x1 pixel area. SoilGrids resolution is ~250m.
        # We create a small buffer around our center point.
        buffer = 150 # meters
        subsets = [
            ('X', x_meter - buffer, x_meter + buffer),
            ('Y', y_meter - buffer, y_meter + buffer)
        ]

        # 4. Request the Data (GetCoverage)
        response = wcs.getCoverage(
            identifier=cov_id, 
            subsets=subsets, 
            format='image/tiff' # As per snippet logic
        )
        
        # 5. Read the result using Rasterio (in-memory)
        with io.BytesIO(response.read()) as f:
            with rasterio.open(f) as src:
                # Read the first band
                data = src.read(1)
                # Get the center pixel
                val = data[0][0]
                
                # Handle NoData (SoilGrids uses negative numbers for empty space)
                if val < 0: return np.nan
                return float(val)

    except Exception as e:
        logging.warning(f"  ⚠️ WCS Error for {prop} at {depth}: {e}")
        return np.nan

def _get_soilgrids_via_owslib(lat, lon):
    logging.info(f"Connecting to SoilGrids WCS via OWSLib for {lat}, {lon}")
    
    # Convert Coordinates Step
    x, y = _latlon_to_homolosine(lat, lon)
    logging.info(f"  Converted Coords: Lat/Lon ({lat},{lon}) -> Homolosine X/Y ({int(x)}, {int(y)})")

    # Prepare a dictionary to store results: (depth, prop) -> value
    results = {}
    
    # Use ThreadPoolExecutor for parallel fetching
    # Adjust max_workers as needed (e.g., 10-20)
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_key = {}
        for depth in SOILGRIDS_DEPTHS:
            for prop in SOILGRIDS_PROPERTIES:
                future = executor.submit(_fetch_owslib_value, prop, depth, x, y)
                future_to_key[future] = (depth, prop)
        
        for future in as_completed(future_to_key):
            depth, prop = future_to_key[future]
            try:
                val = future.result()
                results[(depth, prop)] = val
            except Exception as e:
                logging.error(f"Error fetching {prop} at {depth}: {e}")
                results[(depth, prop)] = np.nan

    # Reconstruct the DataFrame
    data_dict = {p: [] for p in SOILGRIDS_PROPERTIES}
    for depth in SOILGRIDS_DEPTHS:
        for prop in SOILGRIDS_PROPERTIES:
            val = results.get((depth, prop), np.nan)
            data_dict[prop].append(val)
            
    df = pd.DataFrame(data_dict, index=SOILGRIDS_DEPTHS)
    
    # Check for empty data
    if df.isnull().all().all():
        logging.error("❌ OWSLib failed to retrieve data. Using Fallback.")
        return None

    # Check for missing critical data (NaNs or Zeros)
    # If critical properties are missing for ANY layer, we should fallback to ensure valid DSSAT input.
    critical_props = ['bdod', 'sand', 'clay', 'wv0033', 'wv1500']
    for prop in critical_props:
        if prop in df.columns:
            # Check for NaNs
            if df[prop].isnull().any():
                logging.warning(f"⚠️ Property '{prop}' has missing values (NaN) in some layers. Triggering fallback.")
                return None
            # Check for all zeros (unlikely for valid soil data)
            if (df[prop].fillna(0) == 0).all():
                logging.warning(f"⚠️ Property '{prop}' is all zeros. Triggering fallback.")
                return None
        
    return df

# --- Fallback Generator (Same as before) ---
def _generate_fallback_data():
    logging.warning("⚠️ USING FALLBACK DATA (Red Sandy Loam).")
    mock_values = {
        "sand": 650, "silt": 200, "clay": 150, "bdod": 145, 
        "cfvo": 50, "wv0033": 180, "wv1500": 80, "soc": 80, 
        "phh2o": 65, "cec": 100, "nitrogen": 100
    }
    data = {prop: [val for _ in SOILGRIDS_DEPTHS] for prop, val in mock_values.items()}
    return pd.DataFrame(data, index=SOILGRIDS_DEPTHS)

# --- Helper: Estimate Static Parameters ---
def _estimate_soil_parameters(df):
    """
    Estimates static DSSAT parameters based on SoilGrids data.
    """
    top_layer = df.iloc[0] # 0-5cm
    
    # 1. SALB (Albedo) - Based on Organic Carbon
    # soc is in dg/kg. 100 dg/kg = 1%.
    soc_pct = top_layer['soc'] / 100
    # Simple heuristic: Higher SOC = Darker = Lower Albedo
    # Base 0.20 (light), decrease by 0.03 per 1% SOC, min 0.08
    salb = max(0.08, 0.20 - (0.03 * soc_pct))
    
    # 2. SLU1 (Stage 1 Evaporation) - Based on Clay/Sand
    clay_pct = top_layer['clay'] / 10
    sand_pct = top_layer['sand'] / 10
    
    if sand_pct > 80:
        slu1 = 2.5
    elif clay_pct > 50:
        slu1 = 9.0
    else:
        # Interpolate between 6 and 9 based on clay
        slu1 = 6.0 + (clay_pct / 50) * 3
        
    # 3. SLDR (Drainage Rate) - Based on average texture
    # We'll look at the whole profile average clay
    avg_clay = df['clay'].mean() / 10
    
    if avg_clay < 15: # Sandy
        sldr = 0.80
    elif avg_clay < 25: # Loamy
        sldr = 0.60
    elif avg_clay < 35: # Loam/Clay Loam
        sldr = 0.40
    else: # Clay
        sldr = 0.15
        
    # 4. SLRO (Runoff Curve Number) - Based on Texture (Hydrologic Group)
    # Slope is unknown, assuming 2-5% (average)
    if avg_clay < 20: # Group A
        slro = 65
    elif avg_clay < 30: # Group B
        slro = 75
    else: # Group C/D
        slro = 85
        
    return {
        "salb": round(salb, 2),
        "slu1": round(slu1, 1),
        "sldr": round(sldr, 2),
        "slro": int(slro),
        "slnf": 1.0, # Keep default
        "slpf": 1.0  # Keep default
    }

# --- Helper: DSSAT ID Generator ---
def construct_dssat_id(institute, site, year, number):
    """
    Constructs a 10-character DSSAT Soil ID.
    Format: II SS YY NNNN
    Example: MSKB890001
    """
    return f"{institute[:2].upper()}{site[:2].upper()}{str(year)[-2:]}{int(number):04d}"

# --- Main Processing Logic ---
def create_soil_file(lat, lon, output_dir, soil_id):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', stream=sys.stdout)
    
    # Ensure soil_id is exactly 10 characters (DSSAT requirement)
    if len(soil_id) > 10:
        soil_id = soil_id[:10]
    elif len(soil_id) < 10:
        soil_id = soil_id.ljust(10, '_')

    # 1. Fetch Data
    df = _get_soilgrids_via_owslib(lat, lon)
    
    if df is None:
        df = _generate_fallback_data()
    else:
        # Validation: Check if data is all zeros or very low (e.g. ocean)
        # SoilGrids units: sand/silt/clay are in g/kg (0-1000)
        # If sum of texture is < 100 g/kg (10%), it's likely invalid/water.
        texture_sum = df[['sand', 'silt', 'clay']].sum(axis=1).mean()
        if texture_sum < 50: # Very low texture content
             logging.warning(f"⚠️ Retrieved data seems invalid (Texture sum {texture_sum:.1f} < 50). Using Fallback.")
             df = _generate_fallback_data()

    # 2. Process for DSSAT (Unit Conversions)
    logging.info("Converting to DSSAT format...")
    dssat_layers = []
    
    # Root Growth Factor Map
    rgf_map = {'0-5cm': 1.0, '5-15cm': 1.0, '15-30cm': 1.0, '30-60cm': 0.8, '60-100cm': 0.5, '100-200cm': 0.2}

    for label, row in df.iterrows():
        # Clean defaults if NaN
        row = row.fillna(0) 
        
        # Create SoilLayer Object
        try:
            lay = SoilLayer(
                slb  = int(label.split('-')[1].replace('cm', '')),
                slcl = row['clay'] / 10,   # g/kg -> %
                slsi = row['silt'] / 10,
                slcf = row['cfvo'] / 10,   # cm3/dm3 -> %
                sbdm = row['bdod'] / 100,  # cg/cm3 -> g/cm3
                sloc = row['soc'] / 100,   # dg/kg -> %
                slni = row['nitrogen'] / 100,
                slhw = row['phh2o'] / 10,  # pH x 10 -> pH
                scec = row['cec'] / 10,
                slll = row['wv1500'] / 1000, # Fraction
                sdul = row['wv0033'] / 1000,
                ssat = (row['wv0033'] / 1000) + 0.15, # Estimate saturation
                ssks = 1.0,
                srgf = rgf_map.get(label, 1.0) # Default to 1.0 if not found
            )
            dssat_layers.append(lay)
        except Exception as e:
            logging.error(f"Error creating layer {label}: {e}")

    # 3. Create Profile
    top = df.iloc[0]
    sand = 100 - (top['clay']/10) - (top['silt']/10)
    texture_class = "SL" if sand > 50 else "CL" # Simplified classifier
    
    # Estimate dynamic parameters
    params = _estimate_soil_parameters(df)
    logging.info(f"Estimated Parameters: {params}")

    profile = SoilProfile(
        name=soil_id, 
        soil_series_name=f"SG_{texture_class}_OWS", 
        soil_clasification=texture_class,
        site="SoilGrids-OWS", country="India", 
        lat=lat, long=lon,
        table=dssat_layers,
        salb=params['salb'],
        slu1=params['slu1'],
        sldr=params['sldr'],
        slro=params['slro'],
        slnf=params['slnf'],
        slpf=params['slpf']
    )

    filename = os.path.join(output_dir, f"{soil_id}.SOL")
    with open(filename, 'w') as f:
        f.write(profile._write_sol())
        
    print(f"\n✅ Created: {filename}")
    print(df.head())
    return filename

if __name__ == "__main__":
    # Test Coordinates
    # Generate DSSAT ID: II SS YY NNNN
    # SG: SoilGrids, IN: India, 25: 2025, 0001: Profile 1
    soil_id = construct_dssat_id("SG", "IN", "25", "0001")
    
    create_soil_file(19.2815, 73.9781, ".", soil_id)

