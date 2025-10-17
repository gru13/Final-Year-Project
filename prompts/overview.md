Please act as an expert Python developer with experience in agricultural modeling and the DSSAT Cropping System Model. Your task is to create a complete, self-contained, and fully functional Python script that programmatically runs a DSSAT simulation using the DSSATTools library.

Part 1: The Core Simulation Environment
The primary goal is to develop a robust and generalized script that serves as a foundational environment for complex tasks, such as Reinforcement Learning experiments. The script must be flexible enough to handle the entire simulation workflow—from data acquisition to execution and result retrieval—without any manual intervention, and be easily configured for different crops and locations.

Source Material:
Your response must be based on the logic and classes demonstrated in the provided Jupyter Notebooks: Example 1 (Basics).ipynb, Example 2 (Perennial Forage).ipynb, and Example 3 (Modify cultivar parameters).ipynb. You need to synthesize the best practices from these files to create the final script.

Detailed Requirements for the Script:

1. Data Handling Options: The script must provide three distinct methods for acquiring necessary input data (.WTH and .SOL files). The user can choose a method by passing an argument to the main script.

Default/Programmatic Download: The script must programmatically download the specified .WTH and .SOL files from their public URLs. This is the default option and should be easily configurable for different files.

Local File Loading: The script must be able to load both weather and soil data from local files if they already exist in the working directory.

Real-Time Weather Generation: The script should be able to call a separate Python function (provided in a file named createWeatherFile.py) to generate a .WTH file using real-time weather data from an external API (like NASA POWER) based on a given location and date range. For now, this option applies only to the weather file, and the soil file must be loaded from a local file or downloaded.

2. Simulation Setup: The script must be designed to be generalized and easily configured. It must correctly define all necessary components as DSSATTools objects:

A WeatherStation object.

A SoilProfile object.

A Crop cultivar object.

All required management sections from the filex module, including Field, InitialConditions, Planting, and SimulationControls.

3. Output Configuration: The simulation must be configured to generate the most comprehensive daily reports possible. Within the SimulationControls object, ensure that the outputs for daily plant growth (PlantGro.OUT), daily soil water (SoilWat.OUT), and daily soil nitrogen (SoilNi.OUT) are all enabled.

4. Execution Environment: The script should create its simulation workspace (the folder containing all DSSAT input and output files) in a sub-directory named dssat_simulation_workspace within the current working directory of the script. It should not use the system's temporary directory.

5. Anticipate and Solve Common Errors: The script must be robust and account for potential issues discovered during development. Specifically, it must correctly handle:

Data Parsing Errors: Use the most reliable method for reading the fixed-width .WTH files (e.g., pandas.read_fwf) to avoid errors that lead to a RuntimeError from the DSSAT executable.

Data Integrity Errors: The script must explicitly handle and remove any duplicate dates that may arise from concatenating multiple weather files, as this is known to cause an AssertionError: date values must be unique within the DSSATTools library.

Attribute Errors: Ensure all class names from the DSSATTools library are correct (e.g., SCOutputs vs. SCOputs).

Part 2: Reinforcement Learning Environment Integration
The script must be designed to function as an environment for a Reinforcement Learning agent. This requires a modular, class-based structure that exposes key functions for an agent to interact with the simulation.

A Note on DSSAT's Simulation Timestep:
DSSAT is a daily, batch-oriented model. This means that a standard simulation run is executed for an entire season from start to finish. However, for a Reinforcement Learning agent to function, it needs an iterative environment where it can take an action and observe the outcome on a per-step basis. The DSSATEnvironment class will be designed to handle this by orchestrating a series of full-season DSSAT simulations.

Required Class Methods:

__init__(self, simulation_config, data_source): The constructor should accept a dictionary containing all simulation details (e.g., crop, cultivar, location, dates) to make it highly configurable. It should then handle data acquisition (using one of the options from Part 1) and initialize the DSSAT simulation object.

reset(self): This method should reset the simulation to the initial conditions for a new episode (e.g., planting date). It will run a full baseline simulation (without any agent actions) and save all outputs to an internal state. This method should return the initial state and any relevant info to the agent.

step(self, action): This is the core function. It must:

Receive an action from the agent (e.g., a specific amount of irrigation in millimeters).

Use the action to dynamically update the simulation's management parameters for the current day.

Run a new, full-season DSSAT simulation from the initial seed state. This new simulation must incorporate all past actions (from previous steps) and the current action.

Extract the state from the outputs of this new run (key variables like soil moisture, plant water stress, and cumulative growth for the new day).

Calculate a reward (a metric reflecting the success of the action, such as change in yield potential or reduction in water stress).

Return (next_state, reward, done), where done is a boolean indicating if the simulation has reached its end date.

Incorporate Forecasts: The step function should be able to optionally incorporate a weather forecast for the next day or week, which the agent can use to inform its decisions.

Final Deliverable:
Provide the complete and final Python script (dssat_rl_env.py) that meets all the above requirements, including the necessary functions for data acquisition. After the script runs successfully, it should print the head of the resulting daily DataFrames for plant growth, soil water, and soil nitrogen to the console to verify that the simulation was successful and the detailed outputs were generated and parsed correctly.