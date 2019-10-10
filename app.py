import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import plotly.graph_objs as go

#setup
colors = {
    'background':'#1D313F',
    'paper': '#192A35',
    'text':'#D6D6D6',
    'title':'#FFFFFF'
}
line_colors = ['#006DDB', '#D16C00', '#E076D5']
static_columns = ['Level', 'Tier', 'Goal Copies']
var_columns = ['Champ Owned', 'Tier Owned']
levels = [1, 2, 3, 4, 5, 6, 7, 8, 9]
tiers = [1, 2, 3, 4, 5]
uniques = [13, 13, 13, 10, 8]
copies = [39, 26, 18, 13, 10]
weights = [[100,0,0,0,0],[100,0,0,0,0],[65,30,5,0,0],
            [50,35,15,0,0],[37,35,25,3,0],[24.5,35,30,10,0.5],
            [20,30,33,15,2],[15,20,35,22,8],[10,15,30,30,15]]

def calculate_final_state(level, tier, goal, c_owned, t_owned, rolls):
    """Take in a scenario to produce the final state vector"""
    #intial state vector
    start = np.zeros((1,goal+1))
    start[0,0] = 1
    #transition matrix on each slot
    m = np.zeros((goal+1,goal+1))
    for i in range(goal):
        if copies[tier-1]-c_owned-i > 0:
            prob = weights[level-1][tier-1]/100*(copies[tier-1]-c_owned-i)/(copies[tier-1]*uniques[tier-1]-t_owned-i)
        else:
            prob = 0
        m[i,i] = 1-prob
        m[i,i+1] = prob
    m[goal,goal] = 1
    #full transition matrix
    full_transition_matrix = np.linalg.matrix_power(m, rolls*5)
    #final state vector based on inital state and transition matrix
    final = np.matmul(start, full_transition_matrix)
    return final[0,-1]

tabtitle='TFT Search Odds'

#initiate
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title=tabtitle
            
#app
app.layout = html.Div([
        html.H1([
            'TFT Search Odds'
            ],
            style={
                'textAlign':'center',
                'color': colors['title'],
                'padding-top': '20px'
            }
        ),
        html.H5([
                'Input Scenario Parameters:'
                ],
                style={
                    'textAlign':'center',
                    'color': colors['text']
                }
            ),
        html.Div([
                dash_table.DataTable(
                    id='search-input-table',
                    columns=(
                        [{'name': 'Scenario',
                          'id': 'Scenario', 
                          'type': 'numeric', 
                          'editable': False}
                        ] +
                        [{'name': f'{i}', 
                          'id': f'{i}',
                          'type': 'numeric',
                          'presentation':'input'}
                        for i in static_columns+var_columns
                        ]
                    ),
                    data=[
                        {'Scenario':i, **{static_columns[-j]: i+j-1 for j in range(3,0,-1)}, 
                        **{column: 0 for column in var_columns}}
                        for i in range(1, 4)
                    ],
                    editable=True,
                    style_as_list_view=True,
                    style_header={
                        'fontWeight': 'bold'
                    },
                    style_cell={
                        'backgroundColor': colors['paper'],
                        'color': colors['text'],
                        'textAlign':'center'
                    },
                    css=[
                        { 'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: #1A2C38 !important;'},
                        { 'selector': 'td.cell--selected *, td.focused *', 'rule': 'color: #FFFFFF !important;'}
                    ]
                ),
            ],
            style={
                'width':'50%',
                'display': 'inline-block',
                'padding-bottom':'20px'
            }
        ),
        html.Div([
                dcc.Graph(
                    id='search-graph',
                    style={
                        'height':'500px',
                        'padding-bottom': '20px',
                        'backgroundColor':colors['paper']
                    },
                    config={
                        'displayModeBar': False
                    }
                )    
            ],
            style={
                'width':'60%',
                'display': 'inline-block'
            }
        ),
        
    ],
    style={
        'backgroundColor':colors['background'],
        'textAlign': 'center'
    }
)
            
@app.callback(
    Output('search-graph', 'figure'),
    [Input('search-input-table', 'data'),
    Input('search-input-table', 'columns')])      
def update_graph(rows, columns): 
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    scenario = {'1':[], '2':[], '3':[]}
    for scen in range(3):
        for i in range(0,101):        
            scenario[f'{scen+1}'].append(
                calculate_final_state(
                    df.Level[scen], df.Tier[scen], df['Goal Copies'][scen],
                    df['Champ Owned'][scen], df['Tier Owned'][scen], i
                )
            )
    return {
        'data': [
            go.Scatter(
                x=list(range(101)),
                y=scenario['1'], 
                mode='lines',
                line={
                    'color':line_colors[0]
                },
                name='Scenario 1'
            ),
            go.Scatter(
                x=list(range(101)),
                y=scenario['2'], 
                mode='lines',
                line={
                    'color':line_colors[1]
                },
                name='Scenario 2'
            ),
            go.Scatter(
                x=list(range(101)),
                y=scenario['3'], 
                mode='lines',
                line={
                    'color':line_colors[2]
                },
                name='Scenario 3'
            )
        ],
        'layout': go.Layout(
            title=(
                f'Prob(Objective completed) vs Rolls ' 
            ),
            titlefont={
                'color':colors['title']
            },
            xaxis={
                'title':'Rolls',
                'showline':True,
                'linewidth':2, 
                'linecolor':colors['text'],
                'showgrid':True,
                'gridwidth':1,
                'gridcolor':colors['text'],
                'range':[0,100]
            },
            yaxis={
                'title':'Probability of objective completed',
                'showline':True,
                'linewidth':2, 
                'linecolor':colors['text'],
                'showgrid':True,
                'gridwidth':1,
                'gridcolor':colors['text'],
                'range':[0,1],
                'hoverformat':'.2f'
            },
            legend={
                'orientation':'h', 
                'y':1.1,
                'x':0
            },                   
            font={
                'color':colors['text']
            },
            margin=go.layout.Margin(
                l=80,
                r=60,
                b=60,
                t=80,
                pad=3
            ),
            plot_bgcolor=colors['paper'],
            paper_bgcolor=colors['paper']
        )
    }

if __name__ == '__main__':
    app.run_server()