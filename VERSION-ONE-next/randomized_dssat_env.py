
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
import os
import shutil
import time
import random
from datetime import datetime, timedelta

# --- Import your custom file creation scripts ---
from createSoilFile import create_soil_file
from createWeatherFile import create_weather_file

# --- Import DSSATTools ---
from DSSATTools import (
    crop, WeatherStation, SoilProfile, filex, DSSAT
)
from DSSATTools.filex import IrrigationEvent

class RandomizedDSSATEnv(gym.Env):
    """
    A Gym environment for DSSAT that randomizes the location (lat/lon) and
    dates (year, planting date) at the beginning of each episode.
    """
    def __init__(self, parameter_ranges, workspace_dir, api_key=None, action_low=0.0, action_high=50.0):
        super(RandomizedDSSATEnv, self).__init__()

        # --- 1. Store Core Parameters ---
        self.parameter_ranges = parameter_ranges
        self.workspace = workspace_dir
        self.api_key = api_key
        print(f"🌍 Initializing Randomized Environment. Scenarios will be generated within the provided ranges.")
        print(f"📂 Using workspace: {self.workspace}")

        # --- 2. Define Action and Observation Spaces ---
        self.action_space = spaces.Box(low=np.array([action_low]), high=np.array([action_high]), dtype=np.float32)
        self.state_size = 21
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.state_size,), dtype=np.float32)

        # --- 3. Simulation Configuration ---
        self.max_growth_days = 200
        self.reward_factors = {
            'GROWTH_FACTOR': 0.01, 'WATER_COST_FACTOR': 0.01,
            'STRESS_PENALTY_FACTOR': 1.5, 'DRAINAGE_PENALTY_FACTOR': 0.5,
            'DRYNESS_PENALTY_FACTOR': 0.5, 'DRYNESS_THRESHOLD': 0.4,
        }

        # --- 4. Initialize DSSAT ---
        os.makedirs(self.workspace, exist_ok=True)
        self.dssat = DSSAT(self.workspace)
        self.scenario_configured = False # Flag to ensure configuration happens on first reset

        # --- MODIFICATION START: Add attributes for logging ---
        self.episode_counter = 0
        self.log_dir = os.path.join(self.workspace, 'episode_logs')
        os.makedirs(self.log_dir, exist_ok=True)
        print(f"📝 Episode logs will be saved to: {self.log_dir}")
        self.current_episode_data = []
        # --- MODIFICATION END ---


    def _generate_random_scenario(self):
        """Generates a new random scenario from the specified parameter ranges."""
        lat = random.uniform(*self.parameter_ranges['lat_range'])
        lon = random.uniform(*self.parameter_ranges['lon_range'])
        year = random.randint(*self.parameter_ranges['year_range'])
        planting_doy = random.randint(*self.parameter_ranges['planting_day_range'])

        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        planting_date = start_date + timedelta(days=planting_doy - 1)

        return {
            'lat': lat, 'lon': lon, 'start_date': start_date,
            'end_date': end_date, 'planting_date': planting_date
        }

    def _configure_for_scenario(self, scenario):
        """Sets up the entire DSSAT simulation for a given scenario."""
        # Unpack scenario parameters
        self.lat = scenario['lat']
        self.lon = scenario['lon']
        self.start_date = scenario['start_date']
        self.end_date = scenario['end_date']
        self.planting_date = scenario['planting_date']

        print(f"\n--- [NEW EPISODE #{self.episode_counter}] Configuring for Lat={self.lat:.2f}, Lon={self.lon:.2f}, Planting Date={self.planting_date.strftime('%Y-%m-%d')} ---")

        # --- File and ID Generation ---
        lat_str = str(int(abs(self.lat * 100))).zfill(4)
        lon_str = str(int(abs(self.lon * 100))).zfill(4)
        
        self.insi = f"WRLD".upper()
        year_2_digit = self.start_date.strftime('%y')
        day_of_year = self.start_date.timetuple().tm_yday
        
        weather_filename = f"{self.insi}{year_2_digit}{day_of_year:02d}.WTH"
        self.weather_file_path = os.path.join(self.workspace, weather_filename)
        
        self.soil_id = f"SG{lat_str}{lon_str}"
        soil_filename = f"{self.soil_id}.SOL"
        self.soil_file_path = os.path.join(self.workspace, soil_filename)

        # --- Create Input Files (if they don't already exist for this location) ---
        if not os.path.exists(self.weather_file_path):
            print(f"🌦️  Weather file not found. Generating '{weather_filename}'...")
            create_weather_file(
                lat=self.lat, lon=self.lon,
                start_date=self.start_date.strftime('%Y-%m-%d'),
                end_date=self.end_date.strftime('%Y-%m-%d'),
                wth_file_path=self.weather_file_path, api_key=self.api_key, insi=self.insi
            )
            shutil.copy(self.weather_file_path, f"{self.workspace}/Weather/{weather_filename}")
        else:
            print(f"👍 Found existing weather file: '{weather_filename}'")

        if not os.path.exists(self.soil_file_path):
            print(f"📜 Soil file not found. Generating '{soil_filename}'...")
            create_soil_file(
                lat=self.lat, lon=self.lon, output_dir=self.workspace,
                soil_id=self.soil_id
            )
        else:
            print(f"👍 Found existing soil file: '{soil_filename}'")
        
        # --- Load DSSAT Configuration Objects ---
        print("⚙️  Loading DSSAT configurations for new scenario...")
        self.cultivar = crop.Sorghum('IB0026')
        weather_station = WeatherStation.from_files([self.weather_file_path])
        self.soil_profile = SoilProfile.from_file(self.soil_id, self.soil_file_path)
        self.field = filex.Field(id_field='REALTIME', wsta=weather_station, id_soil=self.soil_profile)
        self.planting = filex.Planting(pdate=self.planting_date, ppop=18, ppoe=18, plrs=45, pldp=5)
        self.soil_depths = [int(layer['slb']) for layer in self.soil_profile.table]
        initial_values = [(depth, 0.20, 1.5, 1.5) for depth in self.soil_depths]
        self.initial_conditions = filex.InitialConditions(
            pcr='SG', icdat=self.planting_date, icres=1300, icren=0.5,
            table=pd.DataFrame(initial_values, columns=['icbl', 'sh2o', 'snh4', 'sno3'])
        )
        self.simulation_controls = filex.SimulationControls(
            general=filex.SCGeneral(sdate=self.planting_date),
            options=filex.SCOptions(water='Y', nitro='N', symbi='N'),
            methods=filex.SCMethods(infil='S'),
            management=filex.SCManagement(irrig='R', ferti='N', resid='N', harvs='M'),
            outputs=filex.SCOutputs(grout='Y', waout='Y', niout='Y', ovvew='Y')
        )
        self.scenario_configured = True
        print("✅ Scenario setup complete.")

    def reset(self, *, seed=None, options=None):
        """
        Resets the environment by generating a new random scenario and
        reconfiguring the entire DSSAT simulation.
        """
        super().reset(seed=seed)
        
        # --- MODIFICATION START: Prepare for new episode logging ---
        self.episode_counter += 1
        self.current_episode_data = [] # Clear data from the previous episode
        # --- MODIFICATION END ---

        new_scenario = self._generate_random_scenario()
        self._configure_for_scenario(new_scenario)
        
        self.current_day = 1
        self.irrigation_events = []
        self.dssat_output = self._run_simulation()

        if self.dssat_output is None:
            raise RuntimeError("Initial DSSAT simulation failed on reset. Check DSSAT setup.")

        self.previous_state = self._get_state(self.current_day)
        if self.previous_state is None:
             self.previous_state = self._get_state(self.current_day-1)
             if self.previous_state is None:
                 print("Critical Error: Could not get state even for day 0. Resetting again.")
                 return self.reset(seed=seed)
        
        # --- MODIFICATION START: Log initial state ---
        if self.previous_state:
            log_entry = self.previous_state.copy()
            log_entry['action_irrigation_mm'] = 0.0 # No action taken on day 0
            log_entry['reward'] = 0.0 # No reward for initial state
            self.current_episode_data.append(log_entry)
        # --- MODIFICATION END ---
        
        observation = self._normalize_state(self.previous_state)
        
        return observation, {}

    def step(self, action):
        if not self.scenario_configured:
            raise RuntimeError("Environment has not been configured. Call reset() before step().")
        self.current_day += 1
        action_value = float(action[0])

        if action_value > 0.1:
            irr_date = self.planting_date + timedelta(days=self.current_day - 1)
            event = IrrigationEvent(idate=irr_date, irop="IR001", irval=action_value)
            self.irrigation_events.append(event)

        self.dssat_output = self._run_simulation()
        if self.dssat_output is None:
            return np.zeros(self.state_size), -200, True, True, {}

        current_state_dict = self._get_state(self.current_day)
        if current_state_dict is None:
            return np.zeros(self.state_size), -100, True, True, {}

        reward = self._calculate_reward(self.previous_state, current_state_dict, action_value)
        terminated = current_state_dict['phenological_stage'] >= 7
        truncated = self.current_day >= self.max_growth_days
        
        # --- MODIFICATION START: Log state, action, and reward for this step ---
        if current_state_dict:
            log_entry = current_state_dict.copy()
            log_entry['action_irrigation_mm'] = action_value
            log_entry['reward'] = reward
            self.current_episode_data.append(log_entry)
        # --- MODIFICATION END ---

        # --- MODIFICATION START: Save log to CSV when episode ends ---
        if (terminated or truncated) and self.current_episode_data:
            log_df = pd.DataFrame(self.current_episode_data)
            filename = f"episode_{self.episode_counter:04d}_log.csv"
            filepath = os.path.join(self.log_dir, filename)
            log_df.to_csv(filepath, index=False)
            print(f"💾 Saved episode log with {len(log_df)} steps to '{filepath}'")
        # --- MODIFICATION END ---

        self.previous_state = current_state_dict
        observation = self._normalize_state(current_state_dict)
        return observation, reward, terminated, truncated, {}

    def _run_simulation(self):
        irrigation = filex.Irrigation(efir=1, idep=30, iame='IR001', table=self.irrigation_events)
        try:
            self.dssat.run_treatment(
                field=self.field, cultivar=self.cultivar, planting=self.planting,
                initial_conditions=self.initial_conditions, irrigation=irrigation,
                simulation_controls=self.simulation_controls
            )
            return self.dssat.output_tables
        except Exception as e:
            print(f"❌ DSSAT Run Error on day {self.current_day} for Lat/Lon {self.lat:.2f}/{self.lon:.2f}: {e}")
            return None

    def _get_state(self, current_day):
        try:
            plantgro_df = self.dssat_output['PlantGro']
            if current_day not in plantgro_df['DAS'].values:
                if not plantgro_df.empty:
                    last_day_data = plantgro_df.iloc[-1]
                    current_day = last_day_data['DAS']
                else:
                    return None

            soilwat_df = self.dssat_output['SoilWat']
            if 'DRNC_D' not in soilwat_df.columns:
                 soilwat_df['DRNC_D'] = soilwat_df['DRNC'].diff().fillna(0)
                 soilwat_df['DPREC'] = soilwat_df['PREC'].diff().fillna(soilwat_df['PREC'].iloc[0])
                 soilwat_df['Rainfall7DaySum'] = soilwat_df['DPREC'].rolling(window=7, min_periods=1).sum()
                 rain_mask = (soilwat_df['DPREC'] > 0).cumsum()
                 soilwat_df['DaysSinceLastRain'] = soilwat_df.groupby(rain_mask).cumcount()
            
            current_weather = self.dssat_output['Weather'].loc[self.dssat_output['Weather']['DAS'] == current_day].iloc[0]
            current_plantgro = plantgro_df.loc[plantgro_df['DAS'] == current_day].iloc[0]
            current_soilwat = soilwat_df.loc[soilwat_df['DAS'] == current_day].iloc[0]

            def get_sw_by_depth(l, h):
                sw_cols = [c for c in soilwat_df.columns if c.startswith("SW") and c.endswith("D") and c[2:-1].isdigit()]
                vals = [current_soilwat[col] for col, depth in zip(sw_cols, self.soil_depths) if l < depth <= h]
                return np.mean(vals) if vals else 0.20

            days_since_last_irrigation = 0
            last_irrigation_amount = 0
            if self.irrigation_events:
                 last_irr_event = self.irrigation_events[-1]
                 days_since_last_irrigation = self.current_day - (last_irr_event.get('idate') - self.planting_date.date()).days
                 last_irrigation_amount = last_irr_event.get('irval')
            
            state = {
                'DAP': current_day, 'days_since_last_rain': current_soilwat['DaysSinceLastRain'],
                'rainfall_7day': current_soilwat['Rainfall7DaySum'], 'HarvestIndex': current_plantgro['HIAD'],
                'phenological_stage': current_plantgro['GSTD'], 'leaf_area_index': current_plantgro['LAID'],
                'total_biomass': current_plantgro['CWAD'], 'soil_water_content_0_30cm': get_sw_by_depth(0, 30),
                'soil_water_content_30_60cm': get_sw_by_depth(30, 60), 'soil_water_content_60_100cm': get_sw_by_depth(60, 100),
                'available_water_fraction': current_soilwat['SWXD'], 'water_stress_factor': current_plantgro['WSGD'],
                'temperature_avg': current_weather['TAVD'], 'solar_radiation': current_weather['SRAD'],
                'last_irrigation_amount': last_irrigation_amount, 'days_since_last_irrigation': days_since_last_irrigation,
                'cumulative_irrigation': current_soilwat['IRRC'], 'totalnumberIrrigation': current_soilwat['IR#C'],
                'forecast': soilwat_df.loc[soilwat_df['DAS'] == current_day + 1, 'DPREC'].iloc[0] if current_day + 1 in soilwat_df['DAS'].values else 0.0,
                'harverst_grain_weight': plantgro_df['GWAD'].iloc[-1],
                'daily_drainage': current_soilwat['DRNC_D']
            }
            return state
        except (IndexError, KeyError) as e:
            print(f"📉 State extraction failed on day {current_day}: {e}")
            return None

    def _calculate_reward(self, prev_state, curr_state, action):
        if not prev_state or not curr_state: return -10
        growth = (curr_state['total_biomass'] - prev_state.get('total_biomass', 0)) * self.reward_factors['GROWTH_FACTOR']
        bonus = curr_state['harverst_grain_weight'] / 100 if curr_state['phenological_stage'] >= 7 else 0
        cost = action * self.reward_factors['WATER_COST_FACTOR']
        stress = (1 - curr_state['water_stress_factor']) * self.reward_factors['STRESS_PENALTY_FACTOR']
        drainage = curr_state['daily_drainage'] * self.reward_factors['DRAINAGE_PENALTY_FACTOR']
        slll, sdul = self.soil_profile.table[0]['slll'], self.soil_profile.table[0]['sdul']
        pawf = (curr_state['soil_water_content_0_30cm'] - slll) / (sdul - slll) if sdul > slll else 0
        dryness = (self.reward_factors['DRYNESS_THRESHOLD'] - pawf) * self.reward_factors['DRYNESS_PENALTY_FACTOR'] if pawf < self.reward_factors['DRYNESS_THRESHOLD'] else 0
        return float(growth + bonus - (cost + stress + drainage + dryness))

    def _normalize_state(self, state_dict):
        if state_dict is None: return np.zeros(self.state_size)
        ordered_keys = sorted(state_dict.keys())
        state_vector = [state_dict[key] for key in ordered_keys]
        return np.array(state_vector, dtype=np.float32)