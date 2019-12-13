import sqlite3
import pandas as pd
import plotly.graph_objects as go
from ipywidgets import widgets


conn = sqlite3.connect("data/movies.db")
df = ''
fig1 = ''
award_name = ''
award_type = ''


def award_produced():
    global df, fig1, award_name, award_type
    # df saves geographic information and the number of overall produced movies of each country
    df = pd.read_sql_query("Select * from Country c Join Location l on (c.country_id = l.id)", conn)
    df['e'] = df.iloc[:, 2:31].sum(axis=1)
    df = df[['country_name', 'iso_2', 'iso_3', 'long', 'lat', 'e']]
    df = df[df['e'] != 0]

    # df1 saves the number of the Oscars movies of each country
    df1 = pd.read_sql_query(
        "SELECT l.country_name, Count(m.country) as count, m.title from Movies m join Country c on (m.country = c.country_id) join Award a on (m.id = a.movie_id) join AwardType at on (a.type = at.id) join Location l on (c.country_id = l.id) where at.name = 'Best Picture' and at.type = 'winner' group by l.country_name",
        conn)

    # df2 merges df1 and df on the attribute of country_name
    df2 = pd.merge(df1, df, how='left', on='country_name')

    # award_df saves the type of the Oscars movies
    award_df = pd.read_sql_query("SELECT name, type from AwardType", conn)

    # award_name and award_type are two widgets that are used to control the data of the plot
    award_name = widgets.Dropdown(
        options=list(award_df['name'].unique()),
        value='Best Picture',
        description='Award name',
    )

    award_type = widgets.Dropdown(
        options=list(award_df['type'].unique()),
        value='winner',
        description='Award type',
    )

    container = widgets.HBox([award_name, award_type])

    # Create the plot
    fig1 = go.FigureWidget()

    fig1.add_trace(
        go.Scatter(
            x=df2['country_name'],
            y=df2['count'],
            yaxis='y2',
            name='Award Movies',
            line=dict(
                color='turquoise'
            )
        ))

    fig1.add_trace(
        go.Bar(
            x=df2['country_name'],
            y=df2['e'],
            name='Produced Movies',
            marker_color='darkcyan'
        ))

    fig1.update_layout(
        title_text='Award Movies and Produced Movies',
        yaxis=dict(
            title="Number of Produced Movies"
        ),
        yaxis2=dict(
            title="Number of Award Movies",
            anchor="free",
            overlaying="y",
            side="right",
            position=1
        ),
        legend=dict(
            x=1.07
        )
    )

    # monitor the changes of the widgets
    award_name.observe(response, names="value")
    award_type.observe(response, names="value")

    return widgets.VBox([container, fig1])


def response(change):
    # change the data of the plot
    df1 = pd.read_sql_query(
        "SELECT l.country_name, Count(m.country) as count, m.title from Movies m join Country c on (m.country = c.country_id) join Award a on (m.id = a.movie_id) join AwardType at on (a.type = at.id) join Location l on (c.country_id = l.id) where at.name = '" + award_name.value + "' and at.type = '" + award_type.value + "' group by l.country_name",
        conn)
    df2 = pd.merge(df1, df, how='left', on='country_name')
    with fig1.batch_update():
        fig1.data[0].x = df2['country_name']
        fig1.data[0].y = df2['count']
        fig1.data[1].x = df2['country_name']
        fig1.data[1].y = df2['e']