import pandas as pd
import sqlite3
import plotly.figure_factory as ff


def rate():
    conn = sqlite3.connect("data/movies.db")

    # df1 and df2 saves the rate of 'Best Picture' movies and 'Foreign Language Film' movies
    df1 = pd.read_sql_query(
        "SELECT m.title, m.vote_average, at.name from Movies m join Award a on (m.id = a.movie_id) Join AwardType at on (a.type = at.id) where at.name='Best Picture'",
        conn)
    df2 = pd.read_sql_query(
        "SELECT m.title, m.vote_average, at.name from Movies m join Award a on (m.id = a.movie_id) Join AwardType at on (a.type = at.id) where at.name='Foreign Language Film'",
        conn)

    # create the plot
    hist_data = [df1.vote_average, df2.vote_average]
    group_labels = ['Best Picture', 'Foreign Language Film']
    colors = ['rgb(32, 178, 170)', 'rgb(248, 187, 208)']
    fig = ff.create_distplot(hist_data, group_labels, bin_size=.1, colors=colors, show_rug=False)
    fig.update_layout(
        title_text='Rate of Award Movies',
        xaxis=dict(
            title=dict(
                text='Rate'
            )
        ),
        yaxis=dict(
            title=dict(
                text='Tenth of All Movies'
            )
        ),
        barmode='group'
    )
    return fig
