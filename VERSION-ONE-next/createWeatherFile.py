import os
import pandas as pd
import numpy as np
import requests
from collections import defaultdict
from datetime import datetime
from typing import Optional

# ... (imports and other code) ...
def create_weather_file(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    wth_file_path: str, # <-- New argument
    api_key: str,
    insi: str = "CHEN",
    site_name: str = "CHENNAI",
    elev: float = -99.0,
) -> str:
# ... (NASA data fetching logic) ...

    # The function no longer builds the path itself. It uses the one provided.
    
    print(f"\nWriting weather data to: {wth_file_path}")

    try:
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        params = {
            "start": pd.to_datetime(start_date).strftime("%Y%m%d"),
            "end": pd.to_datetime(end_date).strftime("%Y%m%d"),
            "latitude": lat, "longitude": lon, "community": "AG",
            "parameters": "ALLSKY_SFC_SW_DWN,T2M_MAX,T2M_MIN,T2MDEW,PRECTOTCORR,WS2M,RH2M,EVPTRNS",
            "format": "JSON"
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()["properties"]["parameter"]
        weather_df = pd.DataFrame(data).reset_index().rename(columns={"index": "date"})
        weather_df["date"] = pd.to_datetime(weather_df["date"], format="%Y%m%d")
        weather_df = weather_df.replace([-999, -99], np.nan)
        weather_df = weather_df.rename(columns={
            "ALLSKY_SFC_SW_DWN": "srad", "T2M_MAX": "tmax", "T2M_MIN": "tmin",
            "T2MDEW": "dewp", "PRECTOTCORR": "rain", "WS2M": "wind",
            "RH2M": "rhum", "EVPTRNS": "evap"
        })
        print("...NASA data fetched successfully.")
    except requests.exceptions.RequestException as e:
        print(f"FATAL: Error fetching NASA POWER data: {e}")
        raise

    # --- O3 Data Fetching (Optional) ---
    o3_df = pd.DataFrame()
    if api_key and api_key != "YOUR_API_KEY_HERE":
        print("Fetching OpenWeatherMap O3 data...")
        try:
            start_ts = int(pd.to_datetime(start_date).timestamp())
            end_ts = int(pd.to_datetime(end_date).replace(hour=23, minute=59).timestamp())
            api_url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start_ts}&end={end_ts}&appid={api_key}"
            
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json().get('list', [])

            if data:
                daily_data = defaultdict(list)
                for entry in data:
                    local_date = datetime.fromtimestamp(entry['dt']).date()
                    daily_data[local_date].append(entry['components'].get('o3', 0))
                records = [{'date': date, 'ozon7': np.mean(vals)} for date, vals in sorted(daily_data.items())]
                o3_df = pd.DataFrame(records)
                o3_df['date'] = pd.to_datetime(o3_df['date'])
                print("...O3 data fetched successfully.")
            else:
                print("...O3 data fetched, but no records returned for the period.")
        except requests.exceptions.RequestException as e:
            print(f"Warning: Error fetching O3 data: {e}. Proceeding without it.")

    df = weather_df
    if not o3_df.empty:
        df = pd.merge(df, o3_df, on='date', how='left')

    df['ozon7'] = df.get('ozon7', 50.0)
    df['ozon7'] = df['ozon7'].fillna(50.0)
    df['dco2'] = 421.0
    df["wind"] = df["wind"] * 86.4
    df["month"] = df["date"].dt.month
    monthly_srad_avg = df.groupby("month")["srad"].mean().to_dict()
    df["par"] = df["month"].map(monthly_srad_avg)
    df["vapr"] = 0.6108 * np.exp((17.27 * df["dewp"]) / (df["dewp"] + 237.3))
    df["YRDOY"] = df["date"].dt.strftime("%y%j")
    
    tav = ((df["tmax"] + df["tmin"]) / 2).mean()
    amp = (df["tmax"].mean() - df["tmin"].mean())

    df_out = df.fillna(-99)
    
    output_cols = ["YRDOY","srad","tmax","tmin","rain","rhum","wind","dewp","par","vapr","dco2","ozon7","evap"]
    
    
    print(f"\nWriting weather data to: {wth_file_path}")

    with open(wth_file_path, "w") as f:
        f.write(f"*WEATHER DATA : {site_name},NASA\n\n")
        f.write("@ INSI      LAT     LONG    ELEV   TAV   AMP REFHT WNDHT   CCO2\n")
        f.write(f"  {insi:<4s}  {lat:7.3f} {lon:7.3f} {elev:5.1f} {tav:5.1f} {amp:5.1f}   2.0   2.0 {df['dco2'].mean():6.1f}\n\n")
        f.write("@DATE  SRAD  TMAX  TMIN  RAIN  RHUM  WIND  DEWP   PAR  VAPR   DCO2  OZON7  EVAP\n")
        
        for _, row in df_out[output_cols].iterrows():
            f.write(f"{row.YRDOY:>5s}"
                    f"{row.srad:6.1f}{row.tmax:6.1f}{row.tmin:6.1f}{row.rain:6.1f}"
                    f"{row.rhum:6.1f}{row.wind:6.1f}{row.dewp:6.1f}{row.par:6.1f}"
                    f"{row.vapr:6.3f}{row.dco2:6.1f}{row.ozon7:6.0f}{row.evap:6.1f}\n")
    
    print("✅ Weather file created successfully.")
    return wth_file_path

if __name__ == '__main__':
    # Example usage when running the script directly
    print("Attempting to generate weather file directly...")
    create_weather_file(
        lat=12.3811,
        lon=78.9366,
        start_date="2013-01-01",
        end_date="2013-12-31",
        wth_file_path="./we.wth", # Save to current directory
        api_key="eddbc7c0c9e63e225934add809624c6e" # Replace if you have one
    )