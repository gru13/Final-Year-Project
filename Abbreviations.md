# DSSAT Parameters and Abbreviations Guide

## Weather File (.WTH) Parameters

### Header Information
- **INSI**: Station identifier (4 characters)
- **LAT**: Latitude (decimal degrees, positive for North)
- **LONG**: Longitude (decimal degrees, negative for West)
- **ELEV**: Elevation above sea level (meters)
- **TAV**: Long-term average annual temperature (°C)
- **AMP**: Amplitude of temperature (difference between hottest and coldest month, °C)
- **REFHT**: Reference height for wind and temperature measurements (meters)
- **WNDHT**: Wind measurement height (meters)

### Daily Weather Data
- **DATE**: Date in YYDDD format (YY=year, DDD=day of year)
- **SRAD**: Solar radiation (MJ/m²/day)
- **TMAX**: Maximum temperature (°C)
- **TMIN**: Minimum temperature (°C)
- **RAIN**: Rainfall (mm)

## Soil File (.SOL) Parameters

### Site Information
- **SITE**: Site identifier
- **COUNTRY**: Country name
- **LAT**: Latitude
- **LONG**: Longitude
- **SCS FAMILY**: USDA Soil Classification System family

### Soil Profile Properties
- **SCOM**: Soil series name/identifier
- **SALB**: Soil albedo (fraction, 0-1)
- **SLU1**: Stage 1 evaporation limit (mm)
- **SLDR**: Drainage rate factor
- **SLRO**: Runoff curve number
- **SLNF**: Mineralization factor
- **SLPF**: Photosynthesis factor
- **SMHB**: pH buffer method code
- **SMPX**: pH extraction method code
- **SMKE**: Potassium extraction method code

### Layer-Specific Properties
- **SDUL**: Drained upper limit (field capacity) - volumetric fraction
- **SLLL**: Lower limit (wilting point) - volumetric fraction
- **SSAT**: Saturated volumetric water content - volumetric fraction
- **SRGF**: Root growth factor (0-1)
- **SSKS**: Saturated hydraulic conductivity (cm/hr)
- **SBDM**: Bulk density (g/cm³)
- **SLOC**: Organic carbon content (%)
- **SLCL**: Clay content (%)
- **SLSI**: Silt content (%)
- **SLCF**: Coarse fragment content (%)
- **SLNI**: Total nitrogen content (%)
- **SLHW**: pH in water
- **SLHB**: pH in buffer
- **SCEC**: Cation exchange capacity
- **SADC**: Soil aluminum content

## Experimental File (.MZX) Parameters

### General Information
- **PEOPLE**: Person responsible for experiment
- **ADDRESS**: Institution/address
- **SITE**: Experimental site location
- **PLOT INFO**: Plot information
- **NOTES**: Additional notes

### Treatment Structure
- **N**: Treatment number
- **R**: Replication number
- **O**: Option (future use)
- **C**: Crop rotation (future use)
- **TNAME**: Treatment name
- **CU**: Cultivar factor level
- **FL**: Field factor level
- **SA**: Soil analysis factor level
- **IC**: Initial conditions factor level
- **MP**: Management-planting factor level
- **MI**: Management-irrigation factor level
- **MF**: Management-fertilizer factor level
- **MR**: Management-residue factor level
- **MC**: Management-chemical factor level
- **MT**: Management-tillage factor level
- **ME**: Management-environment factor level
- **MH**: Management-harvest factor level
- **SM**: Simulation control factor level

### Cultivars
- **C**: Cultivar number
- **CR**: Crop code (MZ = Maize)
- **INGENO**: Cultivar genetic coefficient file identifier
- **CNAME**: Cultivar name

### Fields
- **L**: Field level number
- **ID_FIELD**: Field identifier
- **WSTA**: Weather station code
- **FLSA**: Field slope (%)
- **FLOB**: Field obstacles (%)
- **FLDT**: Drainage type
- **FLDD**: Drainage density
- **FLDS**: Drainage depth
- **FLST**: Field stone content (%)
- **SLTX**: Soil texture code
- **SLDP**: Soil depth (cm)
- **ID_SOIL**: Soil profile identifier
- **FLNAME**: Field name

### Initial Conditions
- **PCR**: Previous crop code
- **ICDAT**: Initial conditions date (YYDDD)
- **ICRT**: Root weight (kg/ha)
- **ICND**: Number of days since last tillage
- **ICRN**: Residue nitrogen content (kg/ha)
- **ICRE**: Residue carbon content (kg/ha)
- **ICWD**: Initial water table depth (cm)
- **ICRES**: Residue weight (kg/ha)
- **ICREN**: Residue incorporation (%)
- **ICREP**: Residue placement code
- **ICRIP**: Residue incorporation depth (cm)
- **ICRID**: Residue incorporation days ago
- **ICNAME**: Initial condition name

### Soil Profile Initial Conditions
- **ICBL**: Bottom of layer (cm)
- **SH2O**: Initial soil water content (volumetric fraction)
- **SNH4**: Initial ammonium-N content (mg/kg)
- **SNO3**: Initial nitrate-N content (mg/kg)

### Planting Details
- **PDATE**: Planting date (YYDDD)
- **EDATE**: Emergence date (YYDDD, -99 = calculate)
- **PPOP**: Plant population at seeding (plants/m²)
- **PPOE**: Plant population at emergence (plants/m²)
- **PLME**: Planting method (S=seed, T=transplant)
- **PLDS**: Planting distribution (R=rows, B=broadcast)
- **PLRS**: Row spacing (cm)
- **PLRD**: Row direction (degrees from North)
- **PLDP**: Planting depth (cm)
- **PLWT**: Seed weight (mg/seed)
- **PAGE**: Age of transplants (days)
- **PENV**: Planting environment
- **PLPH**: Plants per hill
- **SPRL**: Spiral planting (cm between plants)
- **PLNAME**: Planting name

### Irrigation Management
- **EFIR**: Irrigation efficiency (fraction)
- **IDEP**: Irrigation depth (cm)
- **ITHR**: Irrigation threshold (% of available water)
- **IEPT**: Irrigation end point (% of available water)
- **IOFF**: Irrigation offset (days)
- **IAME**: Irrigation application method
- **IAMT**: Irrigation amount (mm)
- **IRNAME**: Irrigation description

### Fertilizer Management
- **FDATE**: Fertilizer application date (YYDDD)
- **FMCD**: Fertilizer material code
- **FACD**: Fertilizer application code
- **FDEP**: Application depth (cm)
- **FAMN**: Fertilizer amount - nitrogen (kg N/ha)
- **FAMP**: Fertilizer amount - phosphorus (kg P/ha)
- **FAMK**: Fertilizer amount - potassium (kg K/ha)
- **FAMC**: Fertilizer amount - carbon (kg C/ha)
- **FAMO**: Fertilizer amount - organic matter (kg/ha)
- **FOCD**: Fertilizer organic carbon code
- **FERNAME**: Fertilizer description

### Simulation Controls
- **NYERS**: Number of years to simulate
- **NREPS**: Number of replications
- **START**: Start of simulation (S=specified date, A=automatic)
- **SDATE**: Start date (YYDDD)
- **RSEED**: Random seed number
- **SNAME**: Simulation name
- **SMODEL**: Simulation model

### Simulation Options
- **WATER**: Water balance (Y=yes, N=no)
- **NITRO**: Nitrogen balance (Y=yes, N=no)
- **SYMBI**: Symbiotic nitrogen fixation (Y=yes, N=no)
- **PHOSP**: Phosphorus balance (Y=yes, N=no)
- **POTAS**: Potassium balance (Y=yes, N=no)
- **DISES**: Disease simulation (Y=yes, N=no)
- **CHEM**: Pesticide simulation (Y=yes, N=no)
- **TILL**: Tillage effects (Y=yes, N=no)
- **CO2**: CO₂ effects (Y=yes, N=no, M=measured)

### Simulation Methods
- **WTHER**: Weather method (M=measured, G=generated, S=simulated)
- **INCON**: Initial conditions (M=measured, E=estimated)
- **LIGHT**: Light method (E=estimated, D=daily totals)
- **EVAPO**: Evapotranspiration method (R=Ritchie, P=Penman, F=FAO)
- **INFIL**: Infiltration method (S=SCS curve number, R=Ritchie)
- **PHOTO**: Photosynthesis method (L=leaf level, C=canopy level)
- **HYDRO**: Hydrology method (R=Ritchie)
- **NSWIT**: Nitrogen switch (1=on, 0=off)
- **MESOM**: Soil organic matter method (G=Godwin, P=Parton)
- **MESEV**: Evaporation method (S=Suleiman-Ritchie, R=Ritchie)
- **MESOL**: Soil layer method (1=fixed, 2=adaptive)

### Management Controls
- **PLANT**: Planting control (A=automatic, R=reported)
- **IRRIG**: Irrigation control (A=automatic, R=reported)
- **FERTI**: Fertilization control (A=automatic, R=reported)
- **RESID**: Residue control (A=automatic, R=reported)
- **HARVS**: Harvest control (A=automatic, M=maturity, R=reported)

### Output Controls
- **FNAME**: Output file name (Y=yes, N=no)
- **OVVEW**: Overview output (Y=yes, N=no)
- **SUMRY**: Summary output (Y=yes, N=no)
- **FROPT**: Frequency option (1=daily, 2=monthly, 3=seasonal)
- **GROUT**: Growth output (Y=yes, N=no)
- **CAOUT**: Carbon output (Y=yes, N=no)
- **WAOUT**: Water output (Y=yes, N=no)
- **NIOUT**: Nitrogen output (Y=yes, N=no)
- **MIOUT**: Mineral output (Y=yes, N=no)
- **DIOUT**: Detailed output (Y=yes, N=no)
- **VBOSE**: Verbose mode (Y=yes, N=no)
- **CHOUT**: Chemical output (Y=yes, N=no)
- **OPOUT**: Operational output (Y=yes, N=no)
- **FMOPT**: Format option (A=ASCII, C=CSV)

## Output File Variables

### PlantGro.OUT (Plant Growth Output)
- **YEAR**: Year
- **DOY**: Day of year
- **DAS**: Days after simulation start
- **DAP**: Days after planting
- **LAID**: Leaf area index
- **CWAD**: Canopy weight above ground (dry weight, kg/ha)
- **RWAD**: Root weight (kg/ha)
- **GWAD**: Grain weight (kg/ha)
- **VLAI**: Vegetative leaf area index
- **VWAD**: Vegetative weight above ground (kg/ha)

### Summary.OUT (Summary Output)
- **HWAM**: Harvested weight at maturity (kg/ha)
- **HWUM**: Harvest units at maturity
- **H#AM**: Harvest units number at maturity
- **MDAT**: Maturity date
- **ADAT**: Anthesis date
- **PDAT**: Planting date

## Batch File Parameters
- **FILEX**: FileX name (experimental file)
- **TRTNO**: Treatment number
- **RP**: Replication number
- **SQ**: Sequence number
- **OP**: Operation number (1=run simulation)
- **CO**: Continue option (0=no, 1=yes)

## Common Codes and Values

### Special Values
- **-99**: Missing data or not applicable
- **-98**: Data not available

### Date Format
- **YYDDD**: 5-digit date format where YY=year (last 2 digits) and DDD=day of year (001-365/366)

### Crop Codes
- **MZ**: Maize (Corn)
- **WH**: Wheat
- **SB**: Soybean
- **RI**: Rice
- **PT**: Potato
- **CO**: Cotton

### Units
- **Temperature**: Degrees Celsius (°C)
- **Rainfall**: Millimeters (mm)
- **Solar Radiation**: Megajoules per square meter per day (MJ/m²/day)
- **Plant Population**: Plants per square meter (plants/m²)
- **Fertilizer**: Kilograms per hectare (kg/ha)
- **Soil Water**: Volumetric fraction (cm³/cm³)
- **Soil Depth**: Centimeters (cm)

This guide covers the most commonly used parameters in DSSAT. The specific parameters available may vary depending on the crop model and version being used.