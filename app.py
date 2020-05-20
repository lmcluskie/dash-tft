import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from bisect import bisect

# setup
colors = {
    'background': '#1D313F',
    'paper': '#192A35',
    'text': '#D6D6D6',
    'title': '#FFFFFF',
    'cells': '#3D4770'
}
line_colors = ['#47D0E8', '#EF9A45', '#8DF279', '#006DDB', '#D16C00', '#477A3D']
static_columns = ['Level', 'Tier', 'Copies Wanted']
var_columns = ['Unit Copies Owned', 'Tier Copies Owned']
patch_current = '10.10'
levels = [1, 2, 3, 4, 5, 6, 7, 8, 9]
tiers = [1, 2, 3, 4, 5]
uniques = [12, 12, 12, 9, 7]
copies = [29, 22, 16, 12, 10]
weights = [
        [100, 0, 0, 0, 0], [100, 0, 0, 0, 0], [75, 25, 0, 0, 0],
        [60, 30, 10, 0, 0], [40, 35, 20, 5, 0], [25, 35, 30, 10, 0],
        [19, 30, 35, 15, 1], [14, 20, 35, 25, 6], [10, 15, 25, 35, 15]
]


def calculate_final_state(level, tier, goal, c_owned, t_owned, rolls):
    """Take in scenario parameters to produce the final state vector"""
    try:
        # initial state vector
        start = np.zeros((1, goal + 1))
        start[0, 0] = 1
        # transition matrix on each slot
        m = np.zeros((goal + 1, goal + 1))
        base_prob = weights[level - 1][tier - 1] / 100
        for i in range(goal):
            if copies[tier - 1] - c_owned > i:
                prob = base_prob * (copies[tier - 1] - c_owned - i) / (
                            copies[tier - 1] * uniques[tier - 1] - t_owned - i)
            else:
                prob = 0
            m[i, i] = 1 - prob
            m[i, i + 1] = prob
        m[goal, goal] = 1
        # full transition matrix on each roll
        roll_transition_matrix = np.linalg.matrix_power(m, rolls * 5)
        # final state vector based on inital state and transition matrix
        final = np.matmul(start, roll_transition_matrix)
        return final[0, -1]
    except TypeError:
        return 0


def iterate_calculations(df):
    probabilities = {'1': [], '2': []}
    percentiles = {'1': [], '2': []}
    for scenario in range(2):
        try:
            for i in range(0, 101):
                prob = calculate_final_state(
                    df.Level[scenario], df.Tier[scenario], df['Copies Wanted'][scenario],
                    df['Unit Copies Owned'][scenario], df['Tier Copies Owned'][scenario], i
                )
                probabilities[f'{scenario + 1}'].append(prob)
        except IndexError:
            probabilities[f'{scenario + 1}'] = [0] * 100
    percentiles['1'].extend((bisect(probabilities['1'], 0.1)+1, bisect(probabilities['1'], 0.5)+1, bisect(probabilities['1'], 0.9)+1))
    percentiles['2'].extend((bisect(probabilities['2'], 0.1)+1, bisect(probabilities['2'], 0.5)+1, bisect(probabilities['2'], 0.9)+1))
    prob_increase = {
        '1': [t - s for s, t in zip(probabilities['1'], probabilities['1'][1:])],
        '2': [t - s for s, t in zip(probabilities['2'], probabilities['2'][1:])]
    }
    return prob_increase, probabilities, percentiles


# initiate
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = f'Interactive TFT Shop Calculator ({patch_current})'

# app
app.layout = html.Div([
        html.H1([
            f'{app.title}'
            ],
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title'],
                'padding-top': '10px'
            }
        ),
                html.Div(
            'Level: Level the rolls take place at',
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title']
            }
        ),
        html.Div(
            'Tier: The tier of the unit you want to find',
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title']
            }
        ),
        html.Div(
            'Copies Wanted: How many copies of the unit you want to find',
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title']
            }
        ),
        html.Div(
            'Unit Copies Owned: How many copies of the unit being searched for are owned by all players combined',
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title']
            }
        ),
        html.Div(
            'Tier Copies Owned: How many copies of all units in the relevant tier are owned by all players combined',
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title']
            }
        ),
        html.Div([
            dash_table.DataTable(
                id='search-input-table',
                columns=[
                    {'name': 'Scenario',
                     'id': 'Scenario',
                     'type': 'numeric',
                     'editable': False}
                ] + [
                    {'name': f'{i}',
                     'id': f'{i}',
                     'type': 'numeric',
                     'presentation': 'dropdown'}
                    for i in static_columns
                ] + [
                    {'name': f'{i}',
                     'id': f'{i}',
                     'type': 'numeric',
                     'presentation': 'input'}
                    for i in var_columns
                ],
                data=[
                    {'Scenario': 'A', 'Level': 4, 'Tier': 1, 'Copies Wanted': 5,
                     'Unit Copies Owned': 6, 'Tier Copies Owned': 80
                     },
                    {'Scenario': 'B', 'Level': 4, 'Tier': 1, 'Copies Wanted': 5,
                     'Unit Copies Owned': 13, 'Tier Copies Owned': 80
                    }
                ],
                dropdown={
                    'Level': {
                        'options': [
                            {'label': i, 'value': i}
                            for i in range(2, 10)
                        ]
                    },
                    'Tier': {
                         'options': [
                            {'label': i, 'value': i}
                            for i in range(1, 6)
                        ]
                    },
                    'Copies Wanted': {
                         'options': [
                            {'label': i, 'value': i}
                            for i in range(1, 10)
                        ]
                    }
                },
                editable=True,
                style_as_list_view=True,
                style_header={
                    'backgroundColor': colors['paper'],
                    'fontWeight': 'bold',
                    'color': colors['text']
                },
                style_data_conditional=[{
                    'if': {'column_id': 'Scenario'},
                    'fontWeight': 'bold',
                    'backgroundColor': colors['paper'],
                    'color': colors['text']
                }],
                style_cell={
                    'fontFamily': 'Garamond',
                    'backgroundColor': '#FFFFFF',
                    'color': '#000000',
                    'textAlign': 'center'
                },
                css=[
                    {'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: #FFFFFF !important;'},
                    {'selector': 'td.cell--selected *, td.focused *', 'rule': 'color: #000000 !important;'}
                ]
            ),
        ],
            style={
                'width': '800px',
                'display': 'inline-block',
            }
        ),        
        html.H6(
            'Rolls Required for Success Chance',
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title'],
                'position': 'relative',
                'top': '10px'
            }
        ),
        html.Div(
            id='percentile-table',
            style={
                'width': '500px',
                'display': 'inline-block',
                'position': 'relative',
                'top': '-10px'
            }
        ),
        html.Div([
                dcc.Graph(
                    id='search-graph',
                    style={
                        'height': '450px',
                        'padding-bottom': '20px',
                        'backgroundColor': colors['paper']
                    },
                    config={
                        'displayModeBar': False
                    }
                )
            ],
            style={
                'width': '90%',
                'display': 'inline-block'
            }
        ),
    ],
    style={
        'backgroundColor': colors['background'],
        'textAlign': 'center'
    }
)


@app.callback(
    [Output('search-graph', 'figure'),
     Output('percentile-table', 'children')],
    [Input('search-input-table', 'data'),
     Input('search-input-table', 'columns')]
)
def update_graph(rows, columns):
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    pdf, cdf, percentile = iterate_calculations(df)
    graph = {
        'data': [
            go.Scatter(
                x=list(range(101)),
                y=pdf['1'],
                mode='lines',
                line={
                    'color': line_colors[0],
                    'shape': 'hv'
                },
                name='Scenario A',
                fill='tozeroy'
            ),
            go.Scatter(
                x=list(range(101)),
                y=pdf['2'],
                mode='lines',
                line={
                    'color': line_colors[1],
                    'shape': 'hv'
                },
                name='Scenario B',
                fill='tozeroy'
            ),
            go.Scatter(
                x=list(range(101)),
                y=cdf['1'],
                mode='lines',
                line={
                    'color': line_colors[0],
                    'shape': 'hv'
                },
                name='Scenario A Cumulative',
                fill='tozeroy',
                visible=False
            ),
            go.Scatter(
                x=list(range(101)),
                y=cdf['2'],
                mode='lines',
                line={
                    'color': line_colors[1],
                    'shape': 'hv'
                },
                name='Scenario B Cumulative',
                fill='tozeroy',
                visible=False
            )
        ],
        'layout': go.Layout(
            title=(
                f'Prob(Units Found) vs Rolls'
            ),
            titlefont={
                'color': colors['title'],
                'family': 'Bodoni',
            },
            xaxis={
                'title': 'Rolls',
                'showline': True,
                'linewidth': 2,
                'linecolor': colors['text'],
                'showgrid': True,
                'gridwidth': 1,
                'gridcolor': colors['text'],
                'range': [0, 100],
                'fixedrange': True
            },
            yaxis={
                'title': 'Probability all units found',
                'showline': True,
                'linewidth': 2,
                'linecolor': colors['text'],
                'showgrid': True,
                'gridwidth': 1,
                'gridcolor': colors['text'],
                'hoverformat': '.2f',
                'fixedrange': True
            },
            legend={
                'orientation': 'h',
                'y': 1.1,
                'x': 0
            },
            font={
                'color': colors['text'],
                'family': 'Garamond'
            },
            margin=go.layout.Margin(
                l=80,
                r=60,
                b=40,
                t=40,
                pad=3
            ),
            plot_bgcolor=colors['paper'],
            paper_bgcolor=colors['paper'],
            updatemenus=[
                go.layout.Updatemenu(
                    buttons=list([
                        dict(
                            args=[{"visible": [True] * 2 + [False] * 2}],
                            label="PDF",
                            method="update"
                        ),
                        dict(
                            args=[{"visible": [False] * 2 + [True] * 2}],
                            label="CDF",
                            method="update"
                        )
                    ]),
                    type="buttons",
                    direction="right",
                    x=1,
                    y=1
                )
            ]
        )
    }
    columns = ['Scenario', '10% (High Roll)', '50% (Median)', '90% (Low Roll)']
    table = dash_table.DataTable(
        columns=[
            {'name': f'{i}',
             'id': f'{i}',
             'editable': False}
            for i in columns
        ],
        data=[
            {
                'Scenario': 'A',
                '10% (High Roll)': percentile['1'][0],
                '50% (Median)': percentile['1'][1],
                '90% (Low Roll)': percentile['1'][2]
            },
            {
                'Scenario': 'B',
                '10% (High Roll)': percentile['2'][0],
                '50% (Median)': percentile['2'][1],
                '90% (Low Roll)': percentile['2'][2]
            }
        ],
        editable=False,
        style_header={
            'fontWeight': 'bold'
        },
        style_cell={
            'fontFamily': 'Garamond',
            'backgroundColor': colors['paper'],
            'color': colors['text'],
            'textAlign': 'center'
        },
        css=[
            {'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: #192A35 !important;'},
            {'selector': 'td.cell--selected *, td.focused *', 'rule': 'color: #FFFFFF !important;'}
        ]
    )
    return graph, table


if __name__ == '__main__':
    app.run_server()
