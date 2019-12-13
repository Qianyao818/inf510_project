import pandas as pd
import sqlite3
import plotly.graph_objects as go


def genre():
    conn = sqlite3.connect("data/movies.db")
    # df1, df2, df3 saves the number of the genre type of top-rated movies, Oscars winner and Oscars nominees
    df1 = pd.read_sql_query(
        "SELECT g.name, Count(m.genre_id1) as count1 from Movies m join Genre g on (g.genre_id = m.genre_id1) where m.rank>=1 and m.rank<=250 group by g.name",
        conn)
    df2 = pd.read_sql_query(
        "SELECT g.name, Count(m.genre_id1) as count2 from Movies m join Genre g on (g.genre_id = m.genre_id1) join Award a on (m.id = a.movie_id) join AwardType at on (a.type = at.id) where at.type = 'winner' group by g.name",
        conn)
    df3 = pd.read_sql_query(
        "SELECT g.name, Count(m.genre_id1) as count3 from Movies m join Genre g on (g.genre_id = m.genre_id1) join Award a on (m.id = a.movie_id) join AwardType at on (a.type = at.id) where at.type = 'winner' or at.type = 'nominee' group by g.name",
        conn)

    # genre saves all genre types
    genre = pd.read_sql_query("SELECT name from Genre", conn)

    # df merges genre, df1, df2, df3 on genre's name
    df = pd.merge(genre, df1, how='left', on='name')
    df = pd.merge(df, df2, how='left', on='name')
    df = pd.merge(df, df3, how='left', on='name')
    df = df.fillna(0)

    # create the plot
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        histfunc="sum",
        x=df.name,
        y=df.count1,
        name='Top Rated Movies',
        marker_color='indianred'
    ))
    fig.add_trace(go.Histogram(
        histfunc="sum",
        x=df.name,
        y=df.count2,
        name='Oscars Winner',
        marker_color='navajowhite'
    ))
    fig.add_trace(go.Histogram(
        histfunc="sum",
        x=df.name,
        y=df.count3,
        name='Oscars Nominee',
        marker_color='lightsalmon'
    ))

    fig.update_layout(
        title_text='Genre of Award Movies and Top Rated Movies',
        xaxis=dict(
            title=dict(
                text='Genre'
            ),
            tickangle=-45
        ),
        yaxis=dict(
            title=dict(
                text='Number of Movies'
            )
        ),
        barmode='group'
    )
    return fig
