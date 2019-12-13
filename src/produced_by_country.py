import sqlite3
import pandas as pd
import plotly.graph_objects as go
from ipywidgets import widgets


year = ''
allyear = ''
df = ''
fig = ''


def produced_by_country():
    global year, allyear, df, fig
    conn = sqlite3.connect("data/movies.db")

    # df saves the number of produced movies each year and in total
    df = pd.read_sql_query("Select * from Country c Join Location l on (c.country_id = l.id)", conn)
    # df.dropna(axis='rows',inplace=True)
    df['e'] = df.iloc[:, 2:31].sum(axis=1)

    conn.close()

    # year and allyear are two widgets that are used to control the data of the map
    year = widgets.IntSlider(
        value=1.0,
        min=1989,
        max=2017,
        step=1.0,
        description='Year:',
        continuous_update=False
    )

    allyear = widgets.Checkbox(
        description='1989 - 2017',
        value=False,
    )

    container = widgets.HBox(children=[allyear, year])

    # create the map
    fig = go.FigureWidget(go.Choropleth(
        locations=df['iso_3'],
        z=df.N1989,
        colorscale='oranges',
        autocolorscale=False,
        marker_line_color='darkgray',
        marker_line_width=0.5,
        colorbar_title='Number of movies'))

    fig.update_layout(
        title_text='Number of Produced Movies',
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'
        )
    )

    # monitor the changes of the widgets
    year.observe(response, names="value")
    allyear.observe(response, names="value")

    return widgets.VBox([container, fig])


def response(change):
    # change the data of the map
    if allyear.value:
        with fig.batch_update():
            fig.data[0]['z'] = df['e']
    else:
        with fig.batch_update():
            fig.data[0]['z'] = df['N' + str(year.value)]