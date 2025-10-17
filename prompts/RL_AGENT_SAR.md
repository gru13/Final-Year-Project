This document describes the structure and components of a Reinforcement Learning (RL) environment designed for training an agent to make optimal irrigation decisions. The environment is built around the DSSAT crop simulation model.

1. Environment Specification
Name: DSSAT-RL Irrigation Environment

Description: A Reinforcement Learning environment for optimal irrigation scheduling using the DSSAT crop simulation model.

2. State Space
Type: Continuous

Dimensions: 26

Description: A multi-dimensional continuous state space representing the current crop, soil, and weather conditions, as well as the history of irrigation events.

2.1. State Variable Structure
The state vector is a flattened array of 26 values, composed of four distinct groups of variables.

Crop Variables
These variables describe the current crop growth and development status.

days_after_planting: Days since planting. Unit: days. Range: [0, 200].

phenological_stage: Encoded growth stage. Unit: normalized. Range: [0, 1].

leaf_area_index: Leaf area index. Unit: m²/m². Range: [0, 8].

total_biomass: Total above-ground biomass. Unit: kg/ha. Range: [0, 20000].

cumulative_gdd: Cumulative growing degree days. Unit: °C-days. Range: [0, 3000].

Soil Variables
These variables describe the soil water status and conditions.

soil_water_content_0_30cm: Volumetric soil water content. Unit: m³/m³. Range: [0.1, 0.5].

soil_water_content_30_60cm: Volumetric soil water content. Unit: m³/m³. Range: [0.1, 0.5].

soil_water_content_60_100cm: Volumetric soil water content. Unit: m³/m³. Range: [0.1, 0.5].

available_water_fraction: Fraction of available water capacity. Unit: fraction. Range: [0, 1].

water_stress_factor: Water stress index. Unit: stress index. Range: [0, 1].

days_since_last_rain: Days since last significant rainfall. Unit: days. Range: [0, 60].

Weather Variables
These variables represent current and recent weather conditions.

rainfall_1day: Rainfall in the last 1 day. Unit: mm. Range: [0, 100].

rainfall_3day: Cumulative rainfall in last 3 days. Unit: mm. Range: [0, 200].

rainfall_7day: Cumulative rainfall in last 7 days. Unit: mm. Range: [0, 300].

temperature_min: Recent minimum temperature. Unit: °C. Range: [0, 40].

temperature_max: Recent maximum temperature. Unit: °C. Range: [15, 50].

temperature_avg: Recent average temperature. Unit: °C. Range: [10, 45].

solar_radiation: Daily solar radiation. Unit: MJ/m²/day. Range: [5, 35].

reference_et: Reference evapotranspiration. Unit: mm/day. Range: [1, 12].

forecast_rain_mm: Forecast rainfall amount for the next day. Unit: mm. Range: [0, 100].

Irrigation History Variables
These variables track previous irrigation decisions.

last_irrigation_amount: Most recent irrigation amount. Unit: mm. Range: [0, 100].

irrigation_amount_t1: Irrigation amount 1 step ago. Unit: mm. Range: [0, 100].

irrigation_amount_t2: Irrigation amount 2 steps ago. Unit: mm. Range: [0, 100].

irrigation_amount_t3: Irrigation amount 3 steps ago. Unit: mm. Range: [0, 100].

irrigation_amount_t4: Irrigation amount 4 steps ago. Unit: mm. Range: [0, 100].

days_since_last_irrigation: Days since last irrigation event. Unit: days. Range: [0, 30].

cumulative_irrigation: Total irrigation applied this season. Unit: mm. Range: [0, 1000].

irrigation_interval_avg: Average days between irrigation events. Unit: days. Range: [1, 30].

2.2. Normalization
All state variables are normalized to the range [0, 1] using min-max scaling, where the formula is:
normalized_value= 
max_value−min_value
raw_value−min_value
​
 

3. Action Space
Type: Continuous

Dimensions: 1

Description: The decision of how much irrigation to apply on a given day.

3.1. Action Processing
The agent's action is processed through a pipeline before being applied to the simulation:

Clipping: The action is clipped to the range [0, 50] mm.

Thresholding: Any action less than 5 mm is set to 0 mm.

Constraint Checking: The action is set to 0 mm if it violates operational constraints (e.g., maximum 3 irrigations per week, minimum 2 days between events).

4. Reward Functions
Type: Step-wise

Description: The reward is calculated and returned at every step of the simulation.

4.1. Primary Composite Reward Function
This is a weighted combination of multiple reward components.

Component

Formula

Weight

Range

Crop Health Reward

(1−water_stress_factor)×0.4

0.4

[0,0.4]

Soil Moisture Reward

$-\left





\text{avg_soil_water_content} - \text{optimal_swc} \right







\times 0.3$

0.3

[-0.3, 0]



Water Use Efficiency (WUE) Reward

If irrigation_amount > 0: min( 
irrigation_amount+0.001
daily_biomass_gain
​
 ,1.0)×0.2. Otherwise: daily_biomass_gain×0.2.

0.2

[0, 0.2]

Water Conservation Penalty

−irrigation_amount×0.01

0.1

[-0.5, 0]

Reward Modifiers:

Growth Stage Multiplier: The total reward is multiplied by 1.5 during critical growth stages (flowering, grain filling, pod filling).

Stress Relief Bonus: A bonus of 0.2 is added if the water_stress_factor is greater than 0.3 and irrigation_amount is greater than 10 mm.

The expected range of the final composite reward is [-1.0, 1.0].

Final Formula:
The total composite reward is calculated as:
Reward=(((1−water_stress_factor)×0.4)+(−avg_soil_water_content−optimal_swc×0.3)+R 
wue
​
 +(−irrigation_amount×0.01)+R 
bonus
​
 )×M 
stage
​
 
where:

R 
wue
​
  is the Water Use Efficiency Reward.

R 
bonus
​
  is the Stress Relief Bonus, which is 0.2 if water_stress_factor > 0.3 and irrigation_amount > 10, otherwise 0.

M 
stage
​
  is the Growth Stage Multiplier, which is 1.5 during critical stages, otherwise 1.0.

4.2. Alternative Reward Functions
The environment also provides three alternative, simpler reward functions.

Simple Daily Reward: (1−water_stress_factor)−(0.02×irrigation_amount)

Biomass Focused Reward: (daily_biomass_gain×10)−(irrigation_amount×0.01)

Yield Efficiency Reward:  
irrigation_amount
daily_biomass_gain
​
  if irrigation_amount > 0 else daily_biomass_gain.

4.3. Dynamic Stage-Based Reward Weighting
A more advanced approach to the composite reward function is to dynamically adjust the weights based on the crop's phenological_stage. This allows the agent to prioritize different objectives (e.g., water conservation vs. stress avoidance) as the season progresses.

Early Vegetative Stage (phenological_stage<0.3)

Objective: Establish the crop efficiently with a focus on water conservation.

Weights: Crop Health: 0.2, Soil Moisture: 0.2, WUE: 0.4, Water Conservation: 0.2.

Critical Reproductive Stages (0.5≤phenological_stage<0.8)

Objective: Avoid water stress at all costs to maximize final yield.

Weights: Crop Health: 0.6, Soil Moisture: 0.3, WUE: 0.1, Water Conservation: 0.0.

Late Season/Maturity Stage (phenological_stage≥0.8)

Objective: Minimal water application to prevent disease and facilitate harvest.

Weights: Crop Health: 0.1, Soil Moisture: 0.1, WUE: 0.1, Water Conservation: 0.7.

5. Episode Configuration
Episode Length: A full growing season, typically lasting 90-150 days.

Termination Conditions: An episode ends when the crop reaches maturity, the maximum length is reached, or the crop fails due to severe stress.

Reset Conditions: The environment resets at the end of an episode, on a manual reset call, or upon simulation failure.

6. Implementation Notes
State Vector Construction: Flatten all state variables into a single NumPy array of length 26.

Action Processing: Constraints and thresholds should be applied before passing the action to the DSSAT simulation.

Reward Computation: The reward should be calculated after each DSSAT simulation step.

Normalization: All state variables must be normalized before being passed to the RL agent.

Memory: The implementation requires storing irrigation history for the last 5 actions and relevant statistics.