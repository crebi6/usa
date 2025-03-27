import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import numpy as np

# Load data
df = pd.read_csv("https://raw.githubusercontent.com/JoshData/historical-state-population-csv/refs/heads/primary/historical_state_population_by_year.csv", names=['state', 'year', 'population'])

# Preprocessing
df['state'] = df['state'].str.upper()

# Calculate national population trend
national_trend = df.groupby('year')['population'].sum().reset_index()

# Advanced layout with multiple tabs and more interactive components
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("US Population Dynamics Explorer", 
                        className="text-center my-4 display-4"), 
                width=12)
    ]),
    
    # Tabs for different views
    dbc.Tabs([
        # Population Overview Tab
        dbc.Tab(label="Population Overview", children=[
            dbc.Row([
                # Year Selector
                dbc.Col([
                    html.Label("Select Year", className="fw-bold"),
                    dcc.Dropdown(
                        id='year-dropdown',
                        options=[{'label': str(year), 'value': year} for year in sorted(df['year'].unique())],
                        value=df['year'].max(),
                        clearable=False,
                        className="mb-3"
                    )
                ], width=6),
                
                # Visualization Type Selector
                dbc.Col([
                    html.Label("Visualization Type", className="fw-bold"),
                    dcc.Dropdown(
                        id='map-type-dropdown',
                        options=[
                            {'label': 'Total Population', 'value': 'total'},
                            {'label': 'Population Growth', 'value': 'growth'}
                        ],
                        value='total',
                        clearable=False,
                        className="mb-3"
                    )
                ], width=6)
            ]),
            
            # Choropleth Map
            dcc.Graph(id='state-population-map')
        ]),
        
        # Population Trends Tab
        dbc.Tab(label="Population Trends", children=[
            dbc.Row([
                dbc.Col([
                    # Population Trend Graph
                    dcc.Graph(id='population-trend-graph')
                ], width=12)
            ])
        ])
    ]),
], fluid=True)

# Callback for Population Map
@app.callback(
    Output('state-population-map', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('map-type-dropdown', 'value')]
)
def update_map(selected_year, map_type):
    filtered_data = df[df['year'] == selected_year].copy()
    
    if map_type == 'growth':
        # Calculate growth rate
        prev_year_data = df[df['year'] == selected_year-1].copy()
        filtered_data = filtered_data.merge(
            prev_year_data[['state', 'population']], 
            on='state', 
            suffixes=('_current', '_previous')
        )
        filtered_data['growth_rate'] = (filtered_data['population_current'] - filtered_data['population_previous']) / filtered_data['population_previous'] * 100
        color_column = 'growth_rate'
        title = f'Population Growth Rate {selected_year-1} to {selected_year}'
        color_scale = 'RdYlGn'
    else:
        color_column = 'population'
        title = f'Total Population in {selected_year}'
        color_scale = 'Plasma'
    
    fig = px.choropleth(
        filtered_data, 
        locations='state', 
        locationmode="USA-states", 
        color=color_column,
        scope="usa",
        color_continuous_scale=color_scale,
        title=title,
        labels={color_column: 'Value'}
    )
    fig.update_layout(height=600, title_x=0.5)
    return fig

# Callback for Population Trend Graph
@app.callback(
    Output('population-trend-graph', 'figure'),
    [Input('year-dropdown', 'value')]
)
def update_population_trend(selected_year):
    # Top 10 most populous states in the most recent year
    top_states = df[df['year'] == selected_year].nlargest(10, 'population')['state'].unique()
    
    # Prepare data for top states
    trend_data = df[df['state'].isin(top_states)]
    
    # Create line plot for top states
    fig = px.line(
        trend_data, 
        x='year', 
        y='population', 
        color='state',
        title='Population Trends for Top 10 Most Populous States',
        labels={'population': 'Population', 'year': 'Year'}
    )
    
    # Add national trend as a thick black line
    fig.add_trace(
        go.Scatter(
            x=national_trend['year'], 
            y=national_trend['population'], 
            mode='lines', 
            name='National Total', 
            line=dict(color='black', width=4, dash='dot')
        )
    )
    
    fig.update_layout(
        height=600, 
        title_x=0.5,
        xaxis_title='Year',
        yaxis_title='Population'
    )
    
    return fig



#for deployment
server = app.server

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=10000, debug=True)
