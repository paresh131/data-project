import os
import sys
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

# Pathing fix to ensure 'src' utilities are found correctly
current_script = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_utils import AirlineDBConnection
from src.utils.read_utils import AppConfig
from src.utils.logger_utils import AppLogger
from src.utils.decorators import log_execution_time

logger = AppLogger().get_logger("AviationDash")
config = AppConfig()
app = dash.Dash(__name__)

@log_execution_time
def fetch_and_clean_data():
    try:
        with AirlineDBConnection() as conn:
            table = config.get_table_name()
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            
            if df.empty:
                return df

            # Standardize columns to lowercase based on your provided list
            df.columns = [c.strip().lower() for c in df.columns]

            # 1. UPDATED AGE GROUPS: 0-17, 18-29, 30-44, 45-59, 60-75, 76+
            bins = [0, 17, 29, 44, 59, 75, 120]
            labels = ['0-17', '18-29', '30-44', '45-59', '60-75', '76+']
            df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels)
            
            # 2. Route String for Chart 4
            df['route'] = df['airport_name'] + " ➔ " + df['arrival_airport']
            
            # 3. Date conversion for Seasonal Trends
            df['departure_date'] = pd.to_datetime(df['departure_date'])
            
            return df
    except Exception as e:
        logger.error(f"Data Fetch Failure: {e}")
        return pd.DataFrame()

app.layout = html.Div([
    html.H1("Airline Passenger Intelligence", 
            style={'textAlign': 'center', 'fontFamily': 'Arial'}),
    
    html.Div([
        html.Label("🌍 Filter by Continent:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(id='continent-dropdown', multi=True, placeholder="Select Continent..."),
    ], style={'width': '95%', 'margin': '0 auto', 'padding': '20px', 'backgroundColor': '#f9f9f9'}),

    # 5-Chart Grid Logic
    html.Div([
        html.Div([dcc.Graph(id='age-dist-bar')], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='seasonal-trend-line')], style={'width': '49%', 'display': 'inline-block'}),
    ]),

    html.Div([
        html.Div([dcc.Graph(id='risk-outlier-box')], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='top-routes-h-bar')], style={'width': '49%', 'display': 'inline-block'}),
    ]),

    html.Div([dcc.Graph(id='gender-dest-stacked')], style={'padding': '20px'}),
    
    html.Div(id='footer', style={'textAlign': 'center', 'padding': '10px', 'color': 'gray'})
])

@app.callback(
    [Output('continent-dropdown', 'options'),
     Output('age-dist-bar', 'figure'),
     Output('seasonal-trend-line', 'figure'),
     Output('risk-outlier-box', 'figure'),
     Output('top-routes-h-bar', 'figure'),
     Output('gender-dest-stacked', 'figure'),
     Output('footer', 'children')],
    [Input('continent-dropdown', 'value')]
)
def update_dashboard(selected_continents):
    df = fetch_and_clean_data()
    if df.empty:
        return [], *([px.scatter(title="No Data Found")] * 5), "Error: Check Database"

    options = [{'label': str(c), 'value': str(c)} for c in sorted(df['continents'].unique()) if c]
    
    # Strictly analyze the filtered dataset
    f_df = df[df['continents'].isin(selected_continents)] if selected_continents else df

    # 1. Passenger Age Groups
    fig1 = px.bar(f_df['age_group'].value_counts().reindex(['0-17', '18-29', '30-44', '45-59', '60-75', '75+']).reset_index(),
                  x='age_group', y='count', title="1. Passenger Age Distribution", 
                  text_auto='.2s', color_discrete_sequence=['#636EFA'])

    # 2. Seasonal Status Trends (3-Month Development)
    trend_df = f_df.groupby([pd.Grouper(key='departure_date', freq='3ME'), 'flight_status']).size().reset_index(name='flights')
    fig2 = px.line(trend_df, x='departure_date', y='flights', color='flight_status', 
                   title="2. Seasonal Status Trends (3-Month Development)", markers=True)

    # 3. Risk Analysis: Daily Delay Outliers (Scatter + Box)
    daily_delays = f_df[f_df['flight_status'] == 'Delayed'].groupby(f_df['departure_date'].dt.date).size().reset_index(name='Daily Delays')
    fig3 = px.box(daily_delays, y='Daily Delays', points="all", title="3. Risk Analysis: Daily Delay Outliers")

    # 4. Top 10 Routes
    route_counts = f_df['route'].value_counts().nlargest(10).reset_index()
    fig4 = px.bar(route_counts, x='count', y='route', orientation='h', title="4. Top 10 Routes", text_auto=True)
    fig4.update_layout(yaxis={'categoryorder':'total ascending'})

    # 5. Gender by Top Destinations
    dest_df = f_df.groupby(['country_name', 'gender']).size().reset_index(name='Count')
    top_countries = f_df['country_name'].value_counts().nlargest(10).index
    dest_df = dest_df[dest_df['country_name'].isin(top_countries)]
    fig5 = px.bar(dest_df, x='country_name', y='Count', color='gender', 
                  title="5. Gender by Top Destinations", text_auto='.2s',
                  color_discrete_map={'Male': '#EF553B', 'Female': '#636EFA'})

    logger.info(f"Dashboard Updated: {len(f_df)} records displayed.")
    return options, fig1, fig2, fig3, fig4, fig5, f"Analysis based on {len(f_df)} records."

if __name__ == '__main__':
    app.run(debug=True)