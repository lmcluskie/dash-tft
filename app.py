import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
import numpy as np
import pandas as pd
import plotly.graph_objs as go

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
var_columns = ['Champ Copies Owned', 'Tier Copies Owned']
patch_current = '9.23'
patch_compare = '9.21'
levels = [1, 2, 3, 4, 5, 6, 7, 8, 9]
tiers = [1, 2, 3, 4, 5]

uniques = {
    patch_current: [12, 12, 12, 9, 6],
    patch_compare: [13, 13, 13, 10, 8]
}
copies = {
    patch_current: [29, 22, 16, 12, 10],
    patch_compare: [39, 26, 18, 13, 10]
}
weights = {
    patch_current:
        [[100, 0, 0, 0, 0], [100, 0, 0, 0, 0], [70, 25, 5, 0, 0],
         [50, 35, 15, 0, 0], [35, 35, 25, 5, 0], [25, 35, 30, 10, 0],
         [20, 30, 33, 15, 2], [15, 20, 35, 24, 6], [10, 15, 30, 30, 15]],
    patch_compare:
        [[100, 0, 0, 0, 0], [100, 0, 0, 0, 0], [70, 25, 5, 0, 0],
         [50, 35, 15, 0, 0], [35, 35, 25, 5, 0], [25, 35, 30, 10, 0],
         [20, 30, 33, 15, 2], [15, 20, 35, 22, 8], [10, 15, 30, 30, 15]]
}


def calculate_final_state(level, tier, goal, c_owned, t_owned, rolls, patch):
    """Take in scenario parameters to produce the final state vector"""
    try:
        # initial state vector
        start = np.zeros((1, goal + 1))
        start[0, 0] = 1
        # transition matrix on each slot
        m = np.zeros((goal + 1, goal + 1))
        base_prob = weights[patch][level - 1][tier - 1] / 100
        for i in range(goal):
            if copies[patch][tier - 1] - c_owned > i:
                prob = base_prob * (copies[patch][tier - 1] - c_owned - i) / (
                            copies[patch][tier - 1] * uniques[patch][tier - 1] - t_owned - i)
            else:
                prob = 0
            m[i, i] = 1 - prob
            m[i, i + 1] = prob
        m[goal, goal] = 1
        # full transition matrix
        full_transition_matrix = np.linalg.matrix_power(m, rolls * 5)
        # final state vector based on inital state and transition matrix
        final = np.matmul(start, full_transition_matrix)
        return final[0, -1]
    except TypeError:
        return 0


def iterate_calculations(df, patch):
    probabilities = {'1': [], '2': []}
    medians = {'1': [], '2': []}
    for scenario in range(2):
        try:
            for i in range(0, 101):
                prob = calculate_final_state(
                    df.Level[scenario], df.Tier[scenario], df['Copies Wanted'][scenario],
                    df['Champ Copies Owned'][scenario], df['Tier Copies Owned'][scenario], i, patch
                )
                probabilities[f'{scenario + 1}'].append(prob)
                if not medians[f'{scenario + 1}']:
                    if prob >= 0.5:
                        medians[f'{scenario + 1}'] = i
                    elif i == 100:
                        medians[f'{scenario + 1}'] = f'{round(prob*100, 2)}%'
        except IndexError:
            probabilities[f'{scenario + 1}'] = [0] * 100
    return probabilities, medians


# initiate
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = f'TFT Search Odds ({patch_current})'

# app
app.layout = html.Div([
        html.H1([
            f'TFT Search Odds ({patch_current})'
            ],
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title'],
                'padding-top': '20px'
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
                    {'Scenario': 'A', 'Level': 4, 'Tier': 1, 'Copies Wanted': 6,
                     'Champ Copies Owned': 3, 'Tier Copies Owned': 40
                     },
                    {'Scenario': 'B', 'Level': 4, 'Tier': 1, 'Copies Wanted': 6,
                     'Champ Copies Owned': 12, 'Tier Copies Owned': 40
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

        html.Div([
                daq.ToggleSwitch(
                    id='comparison-toggle',
                    label=f'Compare to Patch {patch_compare} (Set 1)',
                    labelPosition='top',
                    color=colors['cells'],
                    value=False
                )
            ],
            style={
                'fontFamily': 'Garamond',
                'width': '60%',
                'display': 'inline-block',
                'color': colors['text']
            }
        ),

        html.H6(
            'Median Rolls Required (will display chance of success at 100 rolls if median>100)',
            style={
                'fontFamily': 'Bodoni',
                'textAlign': 'center',
                'color': colors['title'],
                'position': 'relative',
                'top': '12px'
            }
        ),
        html.Div(
            id='median-table',
            style={
                'width': '500px',
                'display': 'inline-block',
            }
        ),
        html.Div([
                dcc.Graph(
                    id='search-graph',
                    style={
                        'height': '500px',
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
     Output('median-table', 'children')],
    [Input('search-input-table', 'data'),
     Input('search-input-table', 'columns'),
     Input('comparison-toggle', 'value')]
)
def update_graph(rows, columns, compare):
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    lines = {}
    results = {}
    lines[patch_current], results[patch_current] = iterate_calculations(df, patch_current)
    if compare:
        lines[patch_compare], results[patch_compare] = iterate_calculations(df, patch_compare)
    else:
        lines[patch_compare], results[patch_compare] = {'1': [0]*101, '2': [0]*101}, {'1': '-', '2': '-'}
    graph = {
        'data': [
            go.Scatter(
                x=list(range(101)),
                y=lines[patch_current]['1'],
                mode='lines',
                line={
                    'color': line_colors[0]
                },
                name='A'
            ),
            go.Scatter(
                x=list(range(101)),
                y=lines[patch_current]['2'],
                mode='lines',
                line={
                    'color': line_colors[1]
                },
                name='B'
            ),
            go.Scatter(
                x=list(range(101)),
                y=lines[patch_compare]['1'],
                mode='lines',
                line={
                    'color': line_colors[3]
                },
                name=f'{patch_compare} A',
                visible=compare
            ),
            go.Scatter(
                x=list(range(101)),
                y=lines[patch_compare]['2'],
                mode='lines',
                line={
                    'color': line_colors[4]
                },
                name=f'{patch_compare} B',
                visible=compare
            ),
        ],
        'layout': go.Layout(
            title=(
                f'Prob(Objective completed) vs Rolls '
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
                'title': 'Probability of objective completed',
                'showline': True,
                'linewidth': 2,
                'linecolor': colors['text'],
                'showgrid': True,
                'gridwidth': 1,
                'gridcolor': colors['text'],
                'range': [0, 1],
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
                b=60,
                t=80,
                pad=3
            ),
            plot_bgcolor=colors['paper'],
            paper_bgcolor=colors['paper']
        )
    }
    columns = ['Patch\Scenario', 'A', 'B']
    table = dash_table.DataTable(
        columns=[
            {'name': f'{i}',
             'id': f'{i}',
             'editable': False}
            for i in columns
        ],
        data=[
            {
                'Patch\Scenario': patch_current,
                'A': results[patch_current]['1'],
                'B': results[patch_current]['2']
            },
            {
                'Patch\Scenario': patch_compare,
                'A': results[patch_compare]['1'],
                'B': results[patch_compare]['2']
            },
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
        style_cell_conditional=[
            {'if': {'column_id': 'Patch\Scenario'},
             'width': '40%'}
        ],
        css=[
            {'selector': 'td.cell--selected, td.focused', 'rule': 'background-color: #192A35 !important;'},
            {'selector': 'td.cell--selected *, td.focused *', 'rule': 'color: #FFFFFF !important;'}
        ]
    )
    return graph, table


if __name__ == '__main__':
    app.run_server()
