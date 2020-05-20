import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output
import os
import boto3
from io import BytesIO



external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Retrieving lookup file from s3 bucket
s3 = boto3.client('s3')
obj = s3.get_object(
    Bucket="investpy",
    Key=f"lookup.feather"
)
lookup = pd.read_feather(BytesIO(obj["Body"].read()))

# For local testing env
# lookup = pd.read_feather('~/Desktop/thinkpad/greatbear/twk_tasks/investpy/dash/inv_data/lookup.feather')

# Replace Nonetype in lookup file with 'Unspecified'
lookup = lookup.fillna('Unspecified')

###################################################################################################
# User Defined functions

def get_stock_data(name):
    # Using data from s3 bucket
    obj = s3.get_object(
    Bucket="investpy",
    Key=f"{name}/data.feather"
)
    s_data = pd.read_feather(BytesIO(obj["Body"].read()))
    
    # For Local testing env
#     s_path = '/Users/angziqing/Desktop/thinkpad/greatbear/twk_tasks/investpy/dash/inv_data/'+ name + '/data.feather'
#     s_data = pd.read_feather(s_path)

    return s_data

def get_sector_vol(sector_name):
    sector_stock_list = lookup[lookup['sector']==sector_name]['ticker'].tolist()
    sec_vol_list = []
    for i in sector_stock_list:
        sec_vol_list.append(get_stock_data(i).iloc[-1]['Volume'])
    
    return sum(sec_vol_list)


##################################################################################################
# Layout setup

app.layout = html.Div([
    
    # Uppermost big block: Title
    html.Div([
        html.H1(
            children='Malaysian Stocks by Sector',
            style={'textAlign': 'center'}
        )
    ]),
        
    # Second upper big block: 1. Choose Sector & Stock, 2. Top info bar
    # 1.
    html.Div([
        html.Label("Select sector: ( Try 'Unspecified' if stock is unavailabe in selected sector. )"),
        dcc.Dropdown(
            id = 'choose_sector',
            options=[{'label': i, 'value':i} for i in lookup.append(pd.DataFrame({'sector':['All']})\
                                                                    ,ignore_index=True).sector.unique().tolist()],
            value = 'Pharmaceuticals'),
        html.Label('Select stock:'),
        dcc.Dropdown(id = 'choose_stock')
    ], 
        style={'width': '20%', 'display': 'inline-block','padding': '0px 50px 0px 20px'}), #padding: 't','r','b','l'
    
    # 2.
    html.Div([
        html.H4(children = "Last Closing Price (RM):"),
        html.H4(id = 'sto_last_close')
    ],
        style={'width': '14%', 'display': 'inline-block','textAlign':'center'}),

    html.Div([
        html.H4(children = "Last Traded Volume:"),
        html.H4(id = 'sto_last_vol'),
    ], 
        style={'width': '14%', 'display': 'inline-block','textAlign':'center', 'padding': '0px 20px 0px 0px'}),
       
    html.Div([
        html.H4(children = "Sector Traded Volume:"),
        html.H4(id = 'sec_last_vol', children = get_sector_vol('Pharmaceuticals')),
    ], 
        style={'width': '14%', 'display': 'inline-block','textAlign':'center','padding': '0px 30px 0px 0px'}),
     
    html.Div([
        html.H4(children = "% Contribution to Sector Volume:"),
        html.H4(id='perc_vol_contr',
            children = str(round((get_stock_data("APER").iloc[-1]['Volume'])/(get_sector_vol('Pharmaceuticals')),4)*100)+'%'),
    ], 
        style={'width': '17%', 'display': 'inline-block','textAlign':'center'}),
    
    # Third block: Figure
    dcc.Graph(id='main_graph', 
              config={'displayModeBar': False})
])
###################################################################################################
# Callbacks

# Sector level
@app.callback(
    Output('choose_stock','options'),
    [Input('choose_sector','value')])
def set_stock_options(selected_sector):
    
    if selected_sector == 'All':
        all_sec_list = lookup['sector'].unique().tolist()
        stock_options = []
        for sec in all_sec_list:
              stock_options.extend([{'label': i['ticker']+" "+i['counter_id'],'value':i['ticker']} for i in\
                                   lookup.loc[lookup['sector']== sec].reset_index()[['ticker','counter_id']].to_dict('records')])

        return stock_options
    
    else:
        stock_options = [{'label': i['ticker']+" "+i['counter_id'], 'value':i['ticker']} for i in\
                         lookup.loc[lookup['sector']==selected_sector].reset_index()[['ticker','counter_id']].to_dict('records')]
    
        return stock_options


# Set first name of stock list as default stock for whichever selected sector
@app.callback(
    Output('choose_stock', 'value'),
    [Input('choose_stock', 'options')])
def set_stockname_value(available_options):
    return available_options[0]['value']

# Stock level
@app.callback(
    [Output('sto_last_close','children'), 
     Output('sto_last_vol', 'children'),
     Output('sec_last_vol', 'children'),
     Output('perc_vol_contr', 'children'),     
     Output('main_graph','figure')],
    [Input('choose_stock','value'), 
     Input('choose_sector','value')])
def update_graph(ticker, selected_sector):
        
    # Get sector volume
    if selected_sector == 'All':
        all_sec_list = lookup['sector'].unique().tolist()
        sec_vol_list = []
        for sec in all_sec_list:
              sec_vol_list.append(get_sector_vol(sec))
    
        sector_volume = sum(sec_vol_list)

    else:        
        sector_volume = get_sector_vol(selected_sector)
    
    # Get latest closed price and volume for selected stock
    data = get_stock_data(ticker) 
    latest_sto_close = data.iloc[-1]['Close']
    latest_sto_vol = data.iloc[-1]['Volume']
    
    # Get stock percentage contribution of volume
    percentage = (latest_sto_vol)/(sector_volume)*100
    percentage_str =  "{0:.5f}%".format(percentage)
  
    # Set up overlap graphs
    figure = plotly.subplots.make_subplots(specs=[[{"secondary_y": True}]])
    figure.add_trace(
        go.Scatter(
            x = data['Date'],
            y = data['Close'],
            mode = "lines",
            name = 'Stock Price'),
            secondary_y=False,
    )
        
    figure.add_trace(
        go.Bar(
            x = data['Date'],
            y = data['Volume'],
            name = 'Volume Traded'),
        secondary_y=True
    )
        
    # Set x-axis title
    figure.update_xaxes(title_text="Date")

    # Set y-axes titles
    figure.update_yaxes(title_text="Volume traded", secondary_y=True)
    figure.update_yaxes(title_text="Price (RM)", secondary_y=False)
    figure.update_xaxes(rangeslider_visible=True, 
                        rangeselector=dict(
                            buttons=list([
                                dict(count=7, label="1w", step="day", stepmode="backward"),
                                dict(count=1, label="1m", step="month", stepmode="backward"),
                                dict(count=6, label="6m", step="month", stepmode="backward"),
                                dict(count=1, label="1y", step="year", stepmode="backward"),
                                dict(step="all")])),
                        rangebreaks=[
                            dict(enabled= True, bounds=['sat','mon']), #hide weekends (not working atm)
                        ]
                       )
    figure.update_layout(
        autosize=False,
        height=380,
        width = 1400,
        margin=dict(l=80,r=0,b=0,t=50,pad=0),
        legend=dict(x=0.8, y=1.3))
    
    return([latest_sto_close,latest_sto_vol,sector_volume,percentage_str,figure])


if __name__ == '__main__':
    app.run_server(debug=True)