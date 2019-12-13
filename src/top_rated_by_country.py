import folium, sqlite3, math
import pandas as pd
import plotly.graph_objects as go
from folium import plugins


def top_rated_by_country_map():
    # get the geojson file for visualization
    url = 'data/custom.geo.json'
    world_geo = f'{url}'
    world_map = folium.Map(
        min_zoom=1,
        max_zoom=6,
        zoom_start=2,
        location=(40, 15)
    )

    conn = sqlite3.connect("data/movies.db")

    # df saves geographic information and the number of overall produced movies of each country
    df = pd.read_sql_query(
        "Select *, Count(m.country) as count from Country c Join Location l on (c.country_id = l.id) Join Movies m on (c.country_id = m.country) where m.rank>=1 and m.rank<=250 group by m.country",
        conn)
    df['e'] = df.iloc[:, 2:31].sum(axis=1)
    df = df[['country_name', 'iso_2', 'iso_3', 'long', 'lat', 'e', 'count']]
    df = df[df['e'] != 0]\

    conn.close()

    # create the choropleth map
    choropleth = folium.Choropleth(
        geo_data=world_geo,
        name='Number of Produced Movies',
        data=df,
        columns=['iso_3', 'e'],
        key_on='feature.properties.iso_a3',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        bins=8,
        legend_name='Number of Produced Movies'
    ).add_to(world_map)

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=['sovereignt'],
            labels=False))

    #  create the layer of the distribution of top-rated movies
    incidents = plugins.MarkerCluster(
        name='Distribution of 250 Top Rated Movies'
    ).add_to(world_map)

    for lat, lng, label, in zip(df.lat, df.long, df['count']):
        for i in range(label):
            folium.Marker(
                location=[lat, lng],
                icon=plugins.BeautifyIcon(
                    icon="leaf",
                    iconSize=[36, 36],
                    background_color="#87CEFA",
                    border_color="#B0E0E6",
                    borderWidth=5,
                    inner_icon_style='size : 18px',
                    number=label
                ),
                popup=label,
            ).add_to(incidents)
        i += 1

    world_map.add_child(incidents)

    folium.LayerControl().add_to(world_map)

    return world_map


def ln(x):
    return math.log(x)


def top_rated_by_country_scatter():
    conn = sqlite3.connect("data/movies.db")

    # df saves the number of top-rated movies of each country
    df = pd.read_sql_query(
        "Select l.country_name, Count(m.country) as count from Country c Join Location l on (c.country_id = l.id) Join Movies m on (c.country_id = m.country) where m.rank>=1 and m.rank<=250 group by m.country",
        conn)
    df = df[['country_name', 'count']]

    # df1 saves geographic information and the number of overall produced movies of each country
    df1 = pd.read_sql_query("Select * from Country c Join Location l on (c.country_id = l.id)", conn)
    df1['e'] = df1.iloc[:, 2:31].sum(axis=1)
    df1 = df1[['country_name', 'iso_2', 'iso_3', 'long', 'lat', 'e']]
    df1 = df1[df1['e'] != 0]

    # df2 merges df2 and df1 on country_name and calculate log
    df2 = pd.merge(df1, df, how='left', on='country_name')
    df2 = df2.fillna(0)
    df2['ln'] = df2['e'].map(ln)

    conn.close()

    # create the plot
    fig = go.Figure(data=go.Scatter(
        x=df2['ln'],
        y=df2['count'],
        mode='markers',
        marker=dict(
            size=8,
            color=df2['count'],  # set color equal to a variable
            colorscale='Viridis',  # one of plotly colorscales
            showscale=True
        ),
        text=df2['country_name']
    ))

    fig.update_layout(
        title_text='Top Rated Movies and Produced Movies of each Country',
        xaxis=dict(
            title=dict(
                text='Ln(Number of Produced Movies)'
            )
        ),
        yaxis=dict(
            title=dict(
                text='Number of Top Rated Movies'
            )
        )
    )

    return fig

