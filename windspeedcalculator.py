#%% imports
import pandas as pd
import numpy as np
from API import get
import geopandas as gpd
import geoplot as gplt
import matplotlib.pyplot as plt
import seaborn as sns

#%% import geojson data RES
url = "https://opendata.arcgis.com/datasets/6d91187a2f9f4bc589d2c6fb5699d7c0_0.geojson"
res = gpd.read_file(url)
url = "https://opendata.arcgis.com/datasets/2e77ce6f6df0482fb34ef2634385ec73_0.geojson"
gemeenten = gpd.read_file(url)



#%% configuration

rc = {
    'font.family':'Poppins',
    'font.size': 20
    }
plt.rcParams.update(rc)



#%% find gemeentes within RES
_indices = [1, 4, 8, 20, 21, 23]
resgld = res.iloc[_indices]

_indices = []

for gemeente in gemeenten.geometry:
    match = []
    
    for regio in resgld.geometry:
        match.append(gemeente.centroid.within(regio))

    _indices.append(any(match))

gemeentes = gemeenten[_indices]

#%% Plot Netherlands RES
fig, ax = plt.subplots(figsize=(10, 10))
plt.axis('off')
res.plot(ax=ax, alpha=0.1, color='grey', edgecolor='black')
resgld.plot(ax=ax, alpha=0.3, color='green', edgecolor='black')

plt.title('RES Gelderland binnen Nederland')


#%% plot RES only

fig, ax = plt.subplots(figsize=(10, 10))
plt.axis('off')
# plot RES within Gelderland
resgld.to_crs(epsg= 3035).plot(ax=ax, alpha=0.3, color='none', edgecolor='black')
gemeentes.to_crs(epsg= 3035).plot(ax=ax, alpha=0.1, color='green', edgecolor='black')

# get and plot centroids
centroids = gemeentes.to_crs(epsg= 3035).centroid
centroids.plot(ax=ax, alpha=0.5, color='orangered', edgecolor='none')

plt.title("RES'en en centroids binnen Gelderland")




# %% Calculate average windspeed

hubheight = 166 # m
roughness = 0.25


coordinates = centroids.to_crs(epsg = 4326)
df = pd.DataFrame(gemeentes.Gemeentenaam.values, columns = ['Gemeente'], index = centroids.index)
df['lon'] = coordinates.x
df['lat'] = coordinates.y
df['Wind 10m'] = pd.Series(0, index= df.index)
df['Wind 166m'] = pd.Series(0, index= df.index)
df['Vollasturen'] = pd.Series(0, index= df.index)

from feedinfunctions import _prepare_wind_data
from feedinfunctions import windpower
from windpowerlib import wind_speed

# call PVGIS API
for index in df.index:
    tmy = get(df.lat[index], df.lon[index])
    df.loc[index, 'Wind 10m'] = tmy['WS10m'].mean()
    
    # create windpowerlib friendly dataframe
    wind_df = _prepare_wind_data(tmy, roughness)

    # calculate windspeed at hubheigt
    hub_speed = wind_speed.logarithmic_profile(tmy.WS10m, 10, hubheight, roughness)
    df.loc[index, 'Wind 166m'] = hub_speed.mean()

    full_load_hours = windpower(wind_df)
    df.loc[index, 'Vollasturen'] = full_load_hours

# %% Save data 

df.to_pickle('e126.pkl')
df.to_csv('resultatenanalyse.csv')
#%% read data & write to gemeentes
df = pd.read_pickle('e126.pkl')

for col in df.columns[3:]:
    gemeentes[col] = df.loc[:, col]
# %% windspeeds
from mpl_toolkits.axes_grid1 import make_axes_locatable
fig, axi = plt.subplots(1, 2, figsize=(20, 10))

vmin = 3.5
vmax = 8.25
divider = make_axes_locatable(axi[0])
c1 = divider.append_axes("right", size="5%", pad=0.1)
c1.remove()
divider = make_axes_locatable(axi[1])
cax = divider.append_axes("right", size="5%", pad=0.1)

cm = plt.cm.get_cmap('Spectral_r', 20)

# 10m
axi[0].axis('off')
gemeentes.to_crs(epsg= 3035).plot(
    ax=axi[0], 
    alpha=0.8, 
    column='Wind 10m', 
    edgecolor='black',
    cmap = cm,
    legend = False,
    vmin = vmin,
    vmax = vmax,
    )

# 166m
axi[1].axis('off')
gemeentes.to_crs(epsg= 3035).plot(
    ax=axi[1], 
    alpha=0.8, 
    column='Wind 166m', 
    edgecolor='black',
    cmap = cm,
    vmin = vmin,
    vmax = vmax,
    legend= True,
    legend_kwds = {
        'label': '$[m/s]$',
    },
    cax = cax
    )
axi[0].set_title('Gemiddelde windsnelheid op 10 meter')
axi[1].set_title('Gemiddelde windsnelheid op 166 meter')


filename = 'windsnelheden'
fig.savefig(f'figures/{filename}.jpg', 
            transparent=False, 
            dpi=72.72,
            bbox_inches="tight")




# %% Vollasturen
fig, ax = plt.subplots(figsize=(10, 10))
plt.axis('off')
cm = plt.cm.get_cmap('Spectral_r', 6)

divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.1)

gemeentes.to_crs(epsg= 3035).plot(
    ax=ax, 
    alpha=0.8, 
    column='Vollasturen', 
    edgecolor='black',
    cmap = cm,
    vmin = 2800,
    vmax = 4000,
    legend= True,
    legend_kwds = {
        'label': '$[uren/jaar]$',
    },
    cax = cax
    )

ax.set_title('Vollasturen per jaar per gemeente')

filename = 'vollasturen'
fig.savefig(f'figures/{filename}.jpg', 
            transparent=False, 
            dpi=72.72,
            bbox_inches="tight")

# %%
