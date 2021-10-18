# |------------------------------------------------------------------
# | # Geospatial Data Exercise
# |------------------------------------------------------------------
# |
# | This is the exercise note for the second lesson of the kaggle course
# | ["Geospatial Analysis"](https://www.kaggle.com/learn/geospatial-analysis)
# | offered by Alexis Cook and Jessica Li. The main goal of the lesson is
# | to get used to __Coordinate Reference System__.
# |

# | ## 1. Task
# |
# | Purple martin (a species of bird) spend the summer in the eastern United
# | States, and migrate to South America in the winter. Show how the
# | birds migrate. Overlay their winter residence with the public
# | sanctuaries. See if the protected areas really provide the useful
# | life infrastructure to the birds.
# |
# | 1. __Assessment of current situation__ : Are the protected areas functioning?
# | 2. __Future strategy__ : What is the first priority for the next move?
# |

# | ## 2. Data
# |
# | We have
# |
# | 1. Tracking records of 11 purple matins in migration. They carry wireless
# | devices that send the positions of the bird with timestamps.
# |
# | 2. Map (= Boundary info) of the protected areas in South America.
# |
# | 3. General world map with the country borders, etc.
# |

# | ## 3. Coordinate Reference System 
# |
# | Coordinate Reference System (CRS) tells how the axes are set for 
# | the positional data stored in a GeoDataFrame.
# | CRS specifies where the coordinate origin (0, 0) is,
# | which directions the axes point to (e.g. northing and easting),
# | what the unit of the numbers is (feet, meters, kilo-meters).
# | When we manipulate one GeoDataFrame with another, for instance,
# | to calculate intersections, make sure both GeoDataFrame have 
# | the same CRS.
# |
# | ### CRS most often used
# |
# | We need to know at least following three.
# |
# | 1. [__epgs: 4326__](https://epsg.io/4326)
# | Usual latitude and longitude (in this order).
# | Equivalent to WGS 84. Origin is the intersection of the meridian
# | and the equator. Unit is degree (e.g. X=8.2505556, Y=48.7627778)
# |
# | 2. [__epgs: 32630__](https://epsg.io/32630)
# | Mercator projection. Origin is
# | somewhere between Iceland and mainland Norway. Unit is meter.
# | (e.g. X=918447.648154, Y=6234705.18923)
# |
# | 3. [__epgs: 2272__](https://epsg.io/2272)
# | Often used in US and Canada. Origin is somewhere on the
# | south edge of Victoria Island in Canada. Unit is foot.
# |
# | Additionally,
# | 4. [__epgs: 2263__](https://epsg.io/2263)
# | Often used in the data obtained in New York.
# |

# | ### Convert pandas to geopandas
# |
# | When we have latitude and longitude columns in a `pandas` DataFrame
# | and would like to convert it to `geopandas`, we need to do two things.
# |
# | 1. Tell `gpd.GeoDataFrame` (`gpd` is the shorthand of `geopandas` that is
# | usually used when the package is imported) which information
# | (X, Y or latitude and
# | longitude) should be used to construct `geometry` column.
# |
# | 2. After a GeoDataFrame is created, specify the coordinate reference system.
# |
# | The code snippet is as follows.
# |
# |```
# |# Create lists of latitude and longitude.
# |lat = [7.0, 7.1]
# |lon = [40.0, 40.1]
# |
# |# Create `Points` object from y and x (latitude and longitude here).
# |# Those point will be stored in the `geometry` column of gpd.GeoDataFrame
# |
# |loc_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lat, lon))
# |
# |# Tell newly made GeoDataFrame, X and Y in `geometry` columns are latitude and longitude.
# |loc_gdf.crs = {'inti': 'epsg:4326'}
# |```

# |## 4. Notebook
# |
# | Import packages.

import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import plotly.graph_objs as go
import folium
import webbrowser
import uuid
import os
import zipfile
import pretty_errors
import pdb

# | If we are not in our working directory, move there.

CWD = '/Users/meg/git6/kaggle/'
DATA_DIR = '../input/geospatial-learn-course-data/'
if Path.cwd() != CWD:
    os.chdir(CWD)

# | If we have not downloaded the course data, get it from Alexis Cook's
# | kaggle public dataset.

if not Path(DATA_DIR).exists():
    command = 'kaggle d download alexisbcook/geospatial-learn-course-data'
    os.system(command)
    os.chdir(DATA_DIR)
    with zipfile.ZipFile('geospatial-learn-course-data', 'r') as zip_ref:
        zip_ref.extractall('.')
    os.chdir(CWD)

# | Some housekeeping stuff. Change `pandas`' options so that we can see
# | whole DataFrame without skipping the lines.

pd.options.display.max_rows = 999
pd.options.display.max_columns = 99


# | This is to store the folium visualization to an html file, and show it
# | on the local browser.

def embed_map(m, file_name):
    from IPython.display import IFrame
    m.save(file_name)
    return IFrame(file_name, width='100%', height='500px')


def embed_plot(fig, file_name):
    from IPython.display import IFrame
    fig.write_html(file_name)
    return IFrame(file_name, width='100%', height='500px')


def show_on_browser(m, file_name):
    '''
    m   : folium Map object
    Do not miss the trailing '/'
    '''
    m.save(file_name)
    url = 'file://'+file_name
    webbrowser.open(url)


def style_function(x): return {'fillColor': 'coral', 'stroke': False}

# | Read the data of purple martin's seasonal migration.


birds_dir = "../input/geospatial-learn-course-data/"
birds_df = pd.read_csv(birds_dir + "purple_martin.csv",
                       parse_dates=['timestamp'])

# | With `parse_dates`. `timestamp` column will be returned as `datetime64`.

print(birds_df.info())

# | Without `parse_dates`. `timestamp` column will be returned as
# | `object` (=string).

birds_no_parse_df = pd.read_csv(birds_dir + "purple_martin.csv")
print(birds_no_parse_df.info())

# | Check the data how many independent birds in the record.

birds_df['tag-local-identifier'].unique()
birds_df['tag-local-identifier'].nunique()
birds_df.groupby('tag-local-identifier').count()['timestamp']

# | Indeed there are 11 birds in the record.
# | Each has 6 to 10 readings during the trip.
# | Conversion of pd.DataFrame to gpd.GeoDataFrame goes
# | in the following steps.
# |
# | 1. Specify how to make `geometry` column. In this case 'location-long'
# | (=longitude) and 'location-lat' (=latitude) columns will be used to
# | create `geometry`.
# |
# | 2. Specify that CRS is EPSG 4326, i.e., standard latitude and longitude.

birds = gpd.GeoDataFrame(birds_df, geometry=gpd.points_from_xy(
    birds_df['location-long'], birds_df['location-lat']))
birds.crs = {'init': 'epsg:4326'}

# | Read underlying world map. The map is under the package directory of `geopandas`.

gpd.datasets.get_path('naturalearth_lowres')
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
americas = world.loc[world['continent'].isin(
    ['North America', 'South America'])]

# | Read the boundary information of the protected areas.
# | The data originally comes from
# | [World Database on Protected Areas(WDPA)](https://www.protectedplanet.net/en/thematic-areas/wdpa?tab=WDPA).
# |

protected_dir = DATA_DIR + 'SAPA_Aug2019-shapefile/SAPA_Aug2019-shapefile/'
protected_areas = gpd.read_file(
    protected_dir+'SAPA_Aug2019-shapefile-polygons.shp')
protected_areas.head(3)

# | Make Polygons more handy.

protected_areas['geometry'] = protected_areas['geometry'].simplify(
    0.02, preserve_topology=False)

# | Calculate the center of the map.

center = [birds_df['location-lat'].mean(), birds_df['location-long'].mean()]
zoom = 5
tiles = 'Stamen Terrain'

# | Random color scheme.

color = [hex(x).replace('0x', '#')
         for x in
         np.random.randint(0, 256**3 - 1, birds['tag-local-identifier'].nunique())]

# | Draw map.

# m_1 = folium.Map(location=center, tiles=tiles, zoom_start=5)
m_1 = folium.Map(location=center, zoom_start=zoom)
folium.GeoJson(data=americas.__geo_interface__).add_to(m_1)
for i_g, (n, g) in enumerate(birds.groupby('tag-local-identifier')):
    _ = folium.PolyLine(locations=g[['location-lat', 'location-long']],
                        weight=2,
                        opacity=1.0,
                        color=color[i_g]).add_to(m_1)
    _ = [folium.CircleMarker(location=(r['location-lat'],
                                       r['location-long']),
                             radius=8,
                             color='transparent',
                             fill_color=color[i_g],
                             fill_opacity=0.7,
                             fill=True).add_to(m_1) for i, r in g.iterrows()]
# -
embed_map(m_1, 'm_1.html')

# -
show_on_browser(m_1, CWD+'m_1b.html')

# -
# | To extract the starting points, do the following (we do not use them here).

start_df = birds.groupby(
    'tag-local-identifier')['geometry'].apply(list).apply(lambda x: x[0]).reset_index()
start_gdf = gpd.GeoDataFrame(start_df, geometry=start_df['geometry'])
start_gdf.crs = {"init": 'epsg:4326'}

# | To extract the ending points do the following  (we do not use them here).

end_df = birds.groupby(
    "tag-local-identifier")['geometry'].apply(list).apply(lambda x: x[-1]).reset_index()
end_gdf = gpd.GeoDataFrame(end_df, geometry=end_df['geometry'])
end_gdf.crs = {"init": 'epsg:4326'}

# | Before we check how the birds' winter-residences
# | overlap with the protected areas, we will quickly
# | see how much fraction of the lands in South
# | America is designated as protected area. The relevant columns are
# |
# | * `REP_M_AREA` : Marine area in square kilometers.
# | * `REP_AREA` : Area in square kilometers.

# | The table attribute is available on downloading of the data. 
# | The documents are found in `./doc` directory.

protected_areas[['REP_AREA', 'REP_M_AREA']]

# | There are somehow 5 areas out of 4748 registered areas where `REP_AREA`
# | is smaller than `REP_M_AREA`.
# | The differences are small, though, and we will use them as they are.
protected_areas.shape
protected_areas.loc[(protected_areas['REP_AREA']
                     - protected_areas['REP_M_AREA'] < 0),
                    ['REP_AREA', 'REP_M_AREA']]

# | Check CRS.
protected_areas.crs

# | Convert the CRS of `protected_areas`
# | to [EPSG 3035](https://spatialreference.org/ref/epsg/etrs89-etrs-laea/).
# | This is equivalent to ETRS 89 with the 'Lambert' projection, and
# | is a [equal area](http://crs.bkg.bund.de/crseu/crs/eu-description.php?crs_id=Y0VUUlM4OS1MQUVB)
# | CRS. Show only the protection areas on the land, but not on the ocean (no 'MARINE' area).

protected_areas_on_land = protected_areas[protected_areas['MARINE'] != '2'].reset_index(
    drop=True)

# | Check if there is any records outside South America in `protected_areas`
# | by plotting them.


m_2 = folium.Map(location=center, zoom_start=zoom)
folium.GeoJson(data=protected_areas.__geo_interface__,
               style_function=style_function).add_to(m_2)

# -
embed_map(m_2, 'm_2.html')

# -
show_on_browser(m_2, CWD+'m_2b.html')

# | `tiles` parameter in `Map` specifies the type of the map to lay underneath.
# | Here 'Stamen Toner' is used to save the memory.
# | Other choices, that do not require API keys to download the map data are
# |
# | - OpenStreetMap
# | - Mapbox Bright
# | - Mapbox Control Room
# | - Stamen (Terrain, Toner, Watercolor)

# | The total area of the protected sites in square km
total_protected_area = (protected_areas['REP_AREA']
                        - protected_areas['REP_M_AREA']).sum()
print(f'\033[33mtotal protected area \033[31m{total_protected_area:.4}\
     \033[33m[km^2]\033[0m')

# | Now calculate the whole area of the South American continent. Make sure
# | to convert the CRS to epsg 3035. As the unit of epsg 3035 is meters, divide
# | the area 1km<sup>2</sup> = 10<sup>6</sup> m<sup>2</sup> to convert the unit
# | to km<sup/2</sup>.
south_america = world[world['continent'] ==
                      'South America'].reset_index(drop=True)
total_area = south_america.to_crs(epsg=3035)['geometry'].area.sum() / 10**6
p_frac = total_protected_area / total_area
print(
    f'\033[33mProtected land fraction in south america \033[31m{p_frac:.3}\033[0m')

# | Here is the final task. Visualize following three all together.
# |
# | 1. Map of American continents (North America and South America combined)
# | 2. Plot the migration paths of the 11 birds, and
# | 3. the registered protected areas.

# | Tell if the birds really spend the winter in or near these sanctuaries.
# | Is the presence of the protected areas really provide the winter habitats
# | for the birds?


m_3 = folium.Map(location=center, tiles='Stamen Terrain', zoom_start=zoom)
# m_3 = folium.Map(location=center, zoom_start=zoom)
folium.GeoJson(data=protected_areas_on_land.__geo_interface__,
               style_function=style_function).add_to(m_3)
for i_g, (n, g) in enumerate(birds.groupby('tag-local-identifier')):
    _ = folium.PolyLine(locations=g[['location-lat', 'location-long']],
                        weight=2,
                        opacity=1.0,
                        color=color[i_g]).add_to(m_3)
    _ = [folium.CircleMarker(location=(r['location-lat'],
                                       r['location-long']),
                             radius=8,
                             color='transparent',
                             fill_color=color[i_g],
                             fill_opacity=0.7,
                             fill=True).add_to(m_3) for i, r in g.iterrows()]
# -
embed_map(m_3, 'm_3.html')

# -
show_on_browser(m_3, CWD+'m_3b.html')

# |  ------------------------------------------
# | Qualitative observations of the map are as follows.
# |
# | 1. Purple martin seem to stop near the edges of the protected areas, rather
# |   than in the middle of them. If we use a bit of imagination, the birds would
# |   like to
# |   rest in the protected area, as soon as they arrive, or would like to
# |   have the last stop at its edge before starting a long stretch of
# |  the next flight.
# |
# | 2. There are few protected area where the paths of different purple martins converge
# |   (e.g. the one near Humaita), although their paths are widely separated at
# |   the beginning. These areas are probably most valuable sanctuaries as the birds apparently
# |   strive to the sites intentionally.
# |
# | 3. Purple martin spend their winter at the southern-east half of
# |  the Amazon Rainforest 
# |  in a relatively concentrated manner (in particular in comparison with
# |  their northern residence).
# |  From there to the south, the protected areas obviously  become much smaller,
# |  fewer, and sparser. Looking at the residence of the birds, it is most beneficial
# |  to create more protected areas at the southeast of Amazon to extend
# |  the habitat of purple martin.
# |
# | ------------------------------------------------------
# |
# | Let us quickly look at which countries in South America have the
# | largest fraction of the protected area with respect to their whole territory.
# | We use `overlap` methods of `geopandas` geometry. The fractions of the
# | protected areas can be taken
# | as the indies how these countries are supportive for the
# | protection of the wildlife.

p_area = []  # protected area of the country
t_area = []  # total area of the country
f_area = []  # fraction of protected are

for i in south_america.index:
    p = np.array([south_america.loc[i, 'geometry'].intersection(
        protected_areas_on_land.loc[j, 'geometry']).area
        for j in protected_areas_on_land.index]).sum()
    p_area.append(p)
    t = south_america.loc[i, 'geometry'].area
    t_area.append(t)
    f = p / t
    f_area.append(f)
south_america['protected_area_total'] = p_area
south_america['area_total'] = t_area
south_america['protected_area_fraction'] = f_area
south_america['non_protected_area_total'] = south_america['area_total'] - \
    south_america['protected_area_total']
south_america.info()

# -----------------------------------------------------
# | Plotly Bar plot.

trace = go.Bar(y=south_america.sort_values(
    'protected_area_fraction')['name'],
    x=south_america.sort_values(
    'protected_area_fraction')['protected_area_fraction'],
    orientation='h')
data = [trace]
layout = go.Layout(height=512, width=1024,
                   font=dict(size=20),
                   xaxis=dict(title=dict(text='Fraction of Protected Area')))
fig = go.Figure(data=data, layout=layout)
_ = fig.add_vline(x=p_frac)
# -
embed_plot(fig, 'p_1.html')
# -
fig.show()

# -----------------------------------------------------
# | Plotly Stacked Bar plot.

trace_protected = go.Bar(name='protected', y=south_america.sort_values(
    'protected_area_total')['name'],
    x=south_america.sort_values(
    'protected_area_total')['protected_area_total'],
    orientation='h')

trace_non_protected = go.Bar(name='not protected', y=south_america.sort_values(
    'protected_area_total')['name'],
    x=south_america.sort_values(
    'protected_area_total')['non_protected_area_total'],
    orientation='h')

data = [trace_protected, trace_non_protected]

layout = go.Layout(height=512, width=1024,
                   font=dict(size=20),
                   barmode='stack',
                   xaxis=dict(title=dict(text='Area Use [km^2]')))

fig = go.Figure(data=data, layout=layout)

# -
embed_plot(fig, 'p_2.html')
# -
fig.show()

# -----------------------------------------------------
south_america[south_america['name'] == 'Brazil']['protected_area_total'].values[0] \
    / south_america['protected_area_total'].sum()

# -----------------------------------------------------
# | ## 5. Conclusion
# |
# | 1. The protected area shown here is the one on the land only.
# |    Ecuador, Chile, and Falkland Islands have large protected
# |    areas in the ocean, but they are not included here.
# |
# | 2. Among 13 countries in South America, only three (Venezuela,
# |    Brazil, Chile) exceed the average fraction of the protected area
# |    (0.31)
# |
# | 3. In particular, Venezuela boasts the largest fraction of the
# |    protected area in spite of their relatively small area of the whole country.
# |    The data stems from the year 2019.
# |
# | 4. More than half (55%) of the protected area
# |    (in area, as opposed to in number)
# |    in South America is located in Brazil.
# |
# | 5. The fraction of the protected area in Argentina,
# |   the second largest country in South America, is 13% and less than
# |   half the South American average. Further effort to promote
# |   the protection of the wildlife habitat in the country should be
# |   warranted.
# |

# | ## Appendix
# | ### intersects and intersection
# |
# | Note that 'intersects' (that returns boolean) need the arguments
# | gpd.GeoDataFrame, while 'intersections' (that returns Polygon)
# | need the arguments to be gpd.GeoSeries.
# |
# | - for gpd.GeoDataFrame 'south_america.loc[i:i, 'geometry']'
# | - for gpd.Series       'south_america.loc[i, 'geometry']'

# x = [south_america.loc[i:i, 'geometry'].intersects(
#     protected_areas_on_land.loc[j:j, :])
#     for i in south_america.index
#     for j in protected_areas_on_land.index]

# | ### Tech Stack
# |
# | 1. __Data format__<br>
# |`geopandas`, since it is an industrial standard.

# | 2. __Quick review of `geopandas` data structure__<br>
# | * Except `geometry` column that usually comes at the end,
# | GeoDataFrame is totally same with
# | `pandas` DataFrame. In short, GeoDataFrame is pandas DataFrame
# | plus 'geometry' column at the end.
# |
# | * `geometry` data has its own attributes (=parameters) and
# | methods (=functions) that are useful for the GIS (Geographic
# | Information System). One of them is __Coordinate Reference
# | System (CRS)__ discussed above.

# | 3. __Visualization__<br>
# | I have a bit of experience with `MapBox` of
# | `plotly` in creating maps of the urban highways.
# | I spent long time with `plotly`
# | to have a map (underlying land image) and plots (points and lines),
# | but finally gave it up. I learned `folium` through this kaggle
# | course, and found it much easier than `plotly` when we deal with
# | geospatial data. There are lots of attractive plugins for `folium`
# | as well.

# | 4. __IDE / Editor__<br>
# | Choices are
# | - VS Code on my laptop
# | - Jupyter Notebook on my laptop
# | - Jupyter Notebook on Kaggle platform
# |
# | In terms of the speed of coding, VS Code is the sole choice.
# | However, when it comes to the infrastructure, like
# | getting a hint in coding, checking the solution, and getting
# | the certificate, there is no other choice than using Jupyter
# | Notebook on kaggle platform.
# | Jupyter Notebook also makes it easier to
# | see `folium` visualizations than VS Code.

# | 5. __Converting Jupyter Notebook to Python script__<br>
# | I downloaded notebook files to local laptop
# | after I finished all lessons and got the certificate.
# | I wanted to edit them further on my comfortable VS Code to post
# | them to GitHub. The first challenge was that it was not straightforward
# | to have `folium` visualization while using VS Code. A short function
# | `show_on_browser` was written so that I can see the visualization
# | on the local browser seamlessly. The jupyter notebooks were converted
# | to plain Python script by `nbconvert` package.
# |
# |```
# |# Install nbconvert
# |pip install nbconvert
# |
# |# Convert Jupyter Notebook 'ex_1.ipynb' to 'ex_1.py'.
# |# 'script means the command convert the input to python script.
# |jupyter nbconvert --to script ex_1.ipynb
# |```

# | 6. __Converting Python script back to Jupyter Notebook__<br>
# | After editing, and testing the code on VS Code, I would like to
# | convert it back to Jupyter Notebook to post them on GitHub.
# | I also would like to touch up the markdown part of the notebook.
# | There are choices:
# |
# | * Finish touching up markdown on VS Code, then convert it to Notebook
# | * Convert the script to Notebook, and finish touching up markdown on Jupyter.
# |
# | First option was difficult because it is not easy to check the formatted markdown
# | while you are working plain Python script on VS Code.
# |
# | Second option also difficult. I cannot edit a long code fast enough on GUI-based
# | platform.
# |
# | The final solution I took (not perfectly satisfied, though) is to use either VS Code
# | or Emacs (my preference) to edit a plain Python code, and time to time,
# | check the formatted markdown with equivalent Notebook code. For the quick conversion
# | of *.py to *.ipynb, the choices are
# |
# | * jupytext
# | * p2j
# | * py2nb
# |
# | each requires preparing  markdown-part  in *.py differently.
# | For instance, in `p2j` all lines starting with `#` are taken as
# | markdown, while `py2nb` with `# |`. Drawbacks in editing markdown
# | as comment text in a plain python script are
# |
# | * no syntax highlighting
# | * no automatic justification of text
# | * no spell check
# |
# | `py2nb` was chosen because with `py2nb`, it is more straightforward
# | than other two to use markdown syntax in the comment text.
# |
# |```
# |# Install py2nb
# |pip install py2nb
# |
# |# Convert python script 'ex_1.py' back to Jupyter Notebook 'ex_1.ipynb'.
# |py2nb ex_1.py
# |```

# | ***
# | END
