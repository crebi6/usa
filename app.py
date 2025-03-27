import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import numpy as np

# Load data
df = pd.read_csv("https://raw.githubusercontent.com/JoshData/historical-state-population-csv/refs/heads/primary/historical_state_population_by_year.csv", names=['state', 'year', 'population'])

# Preprocessing
df['state'] = df['state'].str.upper()

# Calculate national population trend
national_trend = df.groupby('year')['population'].sum().reset_index()

# Create Dash app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# App Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("US State Population Explorer", 
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
                # State Selector
                dbc.Col([
                    html.Label("Select State for Trend", className="fw-bold"),
                    dcc.Dropdown(
                        id='state-trend-dropdown',
                        options=[{'label': state, 'value': state} for state in sorted(df['state'].unique())],
                        value='NY',  # Default to New York
                        clearable=False,
                        className="mb-3"
                    )
                ], width=12)
            ]),
            
            # Population Trend Graph
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='state-population-trend-graph')
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

# Callback for State Population Trend
@app.callback(
    Output('state-population-trend-graph', 'figure'),
    [Input('state-trend-dropdown', 'value')]
)
def update_state_population_trend(selected_state):
    # Filter data for the selected state
    state_data = df[df['state'] == selected_state]
    
    # Create line plot for the selected state
    fig = go.Figure()
    
    # Add state trend line
    fig.add_trace(
        go.Scatter(
            x=state_data['year'], 
            y=state_data['population'], 
            mode='lines+markers', 
            name=f'{selected_state} Population',
            line=dict(color='blue', width=3)
        )
    )
    
    # Add national trend line for comparison
    fig.add_trace(
        go.Scatter(
            x=national_trend['year'], 
            y=national_trend['population'], 
            mode='lines', 
            name='National Total', 
            line=dict(color='red', width=2, dash='dot')
        )
    )
    
    # Calculate and add trend line annotations
    first_pop = state_data['population'].iloc[0]
    last_pop = state_data['population'].iloc[-1]
    total_growth = ((last_pop - first_pop) / first_pop) * 100
    
    fig.update_layout(
        title=f'Population Trend for {selected_state} (Total Growth: {total_growth:.2f}%)',
        xaxis_title='Year',
        yaxis_title='Population',
        height=600,
        title_x=0.5,
        annotations=[
            dict(
                x=state_data['year'].iloc[-1],
                y=last_pop,
                xref="x", yref="y",
                text=f'Current: {last_pop:,}',
                showarrow=True,
                arrowhead=7,
                ax=0,
                ay=-40
            )
        ]
    )
    
    return fig

# For Render deployment
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
