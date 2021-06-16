import glob
import pandas as pd
import geopandas
import six
import numpy
import re
import  geopandas
import matplotlib.pyplot as plt
from matplotlib import colors

from geodata_functions import *
# six,munch,cligj, Shapely,GDAL, click_plugins, Fiona, pyproj, Rtree,geopandas
files = [f for f in glob.glob("./data/csse_*.csv")]
dfs = []
columns = ['Province/State', 'Country/Region', 'Last Update', 'Confirmed']
for f in files:
    df = pd.read_csv(f, parse_dates=['Last Update'], usecols=columns)
    dfs.append(df)
df = pd.concat(dfs)
def clean_data():
    df.loc[df['Country/Region']=='UK']='United Kingdom'
def to_state(row):
    specificColumn1=row['Province/State']
    if pd.isna(specificColumn1):
            return specificColumn1
    m = re.match(r'\w+[ \-]?\w+, ([A-Z]{2})$',specificColumn1)
    if m is None:
         return specificColumn1
    list=m.groups()
    for x in list:
        return states_abbr_to_full[x]
def create_location(row): 
        if pd.isna(row['Province/State']):
                return row['Country/Region']
        else:
                return row['Province/State'] + ', ' + row['Country/Region']
# clean_data()
df['Province/State']=df.apply(to_state,axis=1)
# print(df.loc[68])
df['Location'] = df.apply(create_location, axis=1)
# print(df.loc[68])
# print(df['Location'].value_counts(dropna=False))

dates=df['Last Update'].unique()
dates=list(dates)
dates.sort()

date_rng = pd.date_range(start=dates[0], end=dates[len(dates)-1], freq='D')
print(date_rng)
location_timeseries = {}
location_details = {}
locations = df['Location'].unique().tolist()
for location in locations:
        values=df.loc[df['Location']==location]
        ldf = values.set_index('Last Update').resample('D').mean()
        ldf=ldf.reindex(index=date_rng)
        location_timeseries[location] = ldf.fillna(method='ffill')
        location_details[location]={'Province/State':values.iloc[0]['Province/State'], 'Country/Region': values.iloc[0]['Location']}
print(location_timeseries['Arizona, US'])
print(location_details['Arizona, US'])

daily_confirmed = pd.DataFrame(index=date_rng, columns=locations)
for location in locations:
        daily_confirmed[location] = location_timeseries[location]

print(daily_confirmed['Arizona, US'])

def build_df_for_datetime(d):
        day_df=pd.DataFrame(daily_confirmed.loc[d])
        day_df.columns = ['Confirmed']
        day_df[['Province/State','Country/Region']]=day_df.apply(lambda x: pd.Series(location_details[x.name]),axis=1)
        day_df.dropna(subset=['Confirmed'], inplace=True)
        return day_df
day_df=build_df_for_datetime(date_rng[0])
print(day_df)
ncov = build_ncov_geodf(day_df)
ncov=ncov.sort_values('Confirmed')
print(ncov[['name','Confirmed','geometry']])
# *********************************************
COLOR = 'black'
plt.rcParams['text.color'] = COLOR
plt.rcParams['axes.labelcolor'] = COLOR
plt.rcParams['xtick.color'] = COLOR
plt.rcParams['ytick.color'] = COLOR

world_lines = geopandas.read_file('zip://./files/ne_50m_admin_0_countries.zip')
world = world_lines[(world_lines['POP_EST'] > 0) & (world_lines['ADMIN'] != 'Antarctica')]

# fig, ax = plt.subplots(figsize=(18, 6))
# world.plot(
#     ax=ax,
#     color="lightslategray",
#     edgecolor="slategray",
#     linewidth=0.5);
# ax.axis('off')
#
# ax.set_title(date_rng[0].strftime("%b %d %Y"))
# ncov = build_ncov_geodf(day_df)
#
# ncov.plot(
#     ax=ax,
#     column='Confirmed',
#     norm=colors.LogNorm(vmin=1, vmax=1000),
#     legend=True,
#     legend_kwds={'label': "Confirmed 2019-nCoV Cases"},
#     cmap='OrRd')
# # plt.show()

def output_images():
    i=0
    for x in date_rng:
        fig, ax = plt.subplots(figsize=(18, 6))
        world.plot(
            ax=ax,
            color="lightslategray",
            edgecolor="slategray",
            linewidth=0.5)
        ax.axis('off')

        ax.set_title(x.strftime("%b %d %Y"))
        day_df = build_df_for_datetime(x)

        ncov = build_ncov_geodf(day_df)

        ncov.plot(
            ax=ax,
            column='Confirmed',
            norm=colors.LogNorm(vmin=1, vmax=1000),
            legend=True,
            legend_kwds={'label': "Confirmed 2019-nCoV Cases"},
            cmap='OrRd')
        fig.savefig('./static/images/map' + str(i) + '.png', facecolor='slategrey', dpi=150, bbox_inches='tight')
        i+=1
output_images()