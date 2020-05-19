import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
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
patch_current = '10.10'
levels = [1, 2, 3, 4, 5, 6, 7, 8, 9]
tiers = [1, 2, 3, 4, 5]

uniques = {
    patch_current: [12, 12, 12, 9, 7]
}
copies = {
    patch_current: [29, 22, 16, 12, 10]
}
weights = {
    patch_current:
        [[100, 0, 0, 0, 0], [100, 0, 0, 0, 0], [75, 25, 0, 0, 0],
         [60, 30, 10, 0, 0], [40, 35, 20, 5, 0], [25, 35, 30, 10, 0],
         [19, 30, 35, 15, 1], [14, 20, 35, 25, 6], [10, 15, 25, 35, 15]],
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
        # full transition matrix on each roll
        roll_transition_matrix = np.linalg.matrix_power(m, rolls * 5)
        # final state vector based on inital state and transition matrix
        final = np.matmul(start, roll_transition_matrix)
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
                        medians[f'{scenario + 1}'] = '>100'
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
                    {'Scenario': 'A', 'Level': 4, 'Tier': 1, 'Copies Wanted': 5,
                     'Champ Copies Owned': 6, 'Tier Copies Owned': 80
                     },
                    {'Scenario': 'B', 'Level': 4, 'Tier': 1, 'Copies Wanted': 5,
                     'Champ Copies Owned': 13, 'Tier Copies Owned': 80
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
            'Median Rolls Required',
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
     Input('search-input-table', 'columns')]
)
def update_graph(rows, columns):
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    lines = {}
    results = {}
    lines[patch_current], results[patch_current] = iterate_calculations(df, patch_current)
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
    columns = ['Scenario', 'Rolls']
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
                'Rolls': results[patch_current]['1']
            },
            {
                'Scenario': 'B',
                'Rolls': results[patch_current]['2']
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
