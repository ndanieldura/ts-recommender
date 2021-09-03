import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots 
import plotly
import json
import numpy as np
import pandas as pd
import flask
from flask import Flask, render_template, request
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import cosine_similarity
import json
import os 

app = flask.Flask(__name__, template_folder='templates')

ts_ratings = pd.read_csv('tv_shows.csv').iloc[:, 1:]

#Import TfIdfVectorizer from scikit-learn
from sklearn.feature_extraction.text import TfidfVectorizer

#Define a TF-IDF Vectorizer Object. Remove all english stop words such as 'the', 'a'
tfidf = TfidfVectorizer(stop_words='english')

#Construct the required TF-IDF matrix by fitting and transforming the data
tfidf_matrix = tfidf.fit_transform(ts_ratings['description'])

# Compute the cosine similarity matrix
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

#Construct a reverse map of indices and movie titles
indices = pd.Series(ts_ratings.index, index=ts_ratings['tvshow']).drop_duplicates()

all_titles = [ts_ratings['tvshow'][i] for i in range(len(ts_ratings['tvshow']))]

# Function that takes in movie title as input and outputs most similar movies
def get_recommendations(title, cosine_sim=cosine_sim):
    # Get the index of the movie that matches the title
    idx = indices[title]

    # Get the pairwsie similarity scores of all movies with that movie
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort the movies based on the similarity scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the scores of 5 most similar movies
    sim_scores = sim_scores[1:6]

    # Get the movie indices
    movie_indices = [i[0] for i in sim_scores]

    # Return the top 5 most similar movies
    return ts_ratings[['tvshow','year','rating','votes']].iloc[movie_indices]
    
def get_suggestions():
    data_lst = pd.read_csv('tv_shows.csv')
    return list(data_lst['tvshow'])

# Set up the main route
@app.route('/', methods=['GET', 'POST'])

def main():

  if flask.request.method == 'GET':
    ts_suggestions = get_suggestions()
    return(flask.render_template('index.html',suggestions=ts_suggestions))

  if flask.request.method == 'POST':
    ts_name = flask.request.form['movie_name']
    ts_name = ts_name.title()
    if ts_name not in all_titles:
      return(flask.render_template('negative.html'))
    else:
      result = get_recommendations(ts_name)
      tv_show = []
      ts_years = []
      ts_ratings = []
      ts_votes = []
      for i in range(len(result)):
        tv_show.append(result.iloc[i][0])
        ts_years.append(result.iloc[i][1])
        ts_ratings.append(result.iloc[i][2])
        ts_votes.append(result.iloc[i][3])

  return flask.render_template('positive.html',  ts_names=tv_show, ts_years= ts_years, 
                                                 ts_ratings = ts_ratings, ts_votes = ts_votes, search_name=ts_name)

    
@app.route('/dashboard')
def dashboard():                       

    # First plot
    category_tr = ts_ratings[ts_ratings['year']==2021][['rating','tvshow']].sort_values(by='rating',ascending=False).head(10)

    fig1 = px.bar(category_tr, x='rating', y='tvshow',
                color='tvshow',template='simple_white')
    fig1.update_layout(showlegend=False,
                    title="Most popular TV-shows by rating",
                    title_x=0.5,
                    xaxis_title='Rating',
                    yaxis_title='Tvshow')

    graph1JSON = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)

    # Second plot

    donut_df = ts_ratings[ts_ratings['year']==2021][['votes','tvshow']].sort_values(by='votes',ascending=False).head(10)

    fig2 = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])
    fig2.add_trace(go.Pie(labels=donut_df['tvshow'], values=donut_df['votes'], name="Votes"),
                row=1, col=1)
    fig2.update_traces(hole=.5, hoverinfo="label+value+name")
    fig2.update_layout(
        title="TV-shows with the highest votes",
        title_x=0.3,
        legend=dict(
            x=0.5,
            y=1,
            traceorder="reversed",
            title_font_family="Times New Roman",
            font=dict(
                family="Courier",
                size=12,
                color="black")
        ))
    
    graph2JSON = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    # Third plot 

    fig3 = px.histogram(ts_ratings,'year',nbins=22,template = 'simple_white')
    fig3.update_layout(showlegend=False,
                    title="TV-shows' distribution per year",
                    title_x=0.5,
                    xaxis_title='Year',
                    yaxis_title='Nr of TV-shows')

    graph3JSON = json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder)

    # Fourth plot

    strip_df = ts_ratings[(ts_ratings['year']>=2010)&(ts_ratings['year']<=2021)]

    fig4 = px.strip(strip_df, x="year", y="rating",color='year',hover_data=['tvshow'],template='simple_white')
    fig4.update_layout(showlegend=False,
                    title="Rating based on year",
                    title_x=0.5,
                    xaxis_title='Year',
                    yaxis_title='Rating')

    graph4JSON = json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder)
        
    return render_template('plots.html', graph1JSON=graph1JSON,  graph2JSON=graph2JSON,
                                         graph3JSON=graph3JSON, graph4JSON=graph4JSON)

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host='0.0.0.0',port=port)