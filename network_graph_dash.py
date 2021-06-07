import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from textwrap import dedent as d
from network_graph_plotly import NetworkGraph

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Social Network"

# default filters
DAYS_SINCE_RELEASE = 0
FIRST_GAME_VER_LEFT = '0.11.0'
FIRST_GAME_VER_RIGHT = '0.12.0'

# variable definition
NODE_SIZE = 'play_time'
NODE_COLOR = 'network_name'
NODE = 'device_id'
EDGE_COLOR = 'connected'
EDGE_SIZE = None
HIGHLIGHT = {}

# locate raw data
DATA_NODES = 'data_nodes.csv'
DATA_EDGES = 'data_edges.csv'


def raw_data(data_nodes, data_edges):
    """
    :param data_nodes:
    :param data_edges:
    :return: an object NetworkGraph & other filters
    """
    df_nodes_raw = pd.read_csv(data_nodes)
    df_edges_raw = pd.read_csv(data_edges)

    a = NetworkGraph(df_nodes_raw, df_edges_raw)

    country = sorted(set(a.df_nodes_raw['country']))
    network = sorted(set(a.df_nodes_raw['network_name']))
    demographic = sorted(set(a.df_nodes_raw['demographic']))
    game_ver = a.df_nodes_raw[['first_game_ver', 'game_ver_num']] \
        .drop_duplicates() \
        .sort_values(by=['game_ver_num'])
    game_ver = game_ver['first_game_ver'].to_list()

    return {
        'raw_data_object': a,
        'country': country,
        'network': network,
        'demographic': demographic,
        'game_ver': game_ver

    }


graph_raw_data = raw_data(data_nodes=DATA_NODES,
                          data_edges=DATA_EDGES)


def network_graph(raw_data_object,
                  first_game_ver, days_since_release, node_size, node_color, node, edge_color, edge_size, highlight):
    a = raw_data_object
    a1 = a.data_filtered(first_game_ver, days_since_release)
    a1_networkx = a.graph_data_networkx(a1['df_nodes'], a1['df_edges'], node, node_size, node_color, edge_color,
                                        edge_size, highlight)
    a1_plotly = a.graph_data_plotly(a1_networkx, first_game_ver)

    return {
        'a1_plotly': a1_plotly,
    }


styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

title = "Social Network Graph"


# callback for my-graph
app.layout = html.Div([
    # Title
    html.Div([html.H1(title)],
             className="row",
             style={'textAlign': "left", 'fontColor': 'blue'}),

    # define the row
    html.Div(
        className="column",
        children=[
            # game version
            html.Div(
                className="two columns",
                children=[
                    dcc.Markdown(d("""**Game Version - Left**""")),
                    dcc.Dropdown(
                        id='dropdown-game-ver-left',
                        options=[{'label': x, 'value': x} for x in graph_raw_data['game_ver']],
                        value=FIRST_GAME_VER_LEFT
                    ),
                    dcc.Markdown(d("""**Game Version - Right**""")),
                    dcc.Dropdown(
                        id='dropdown-game-ver-right',
                        options=[{'label': x, 'value': x} for x in graph_raw_data['game_ver']],
                        value=FIRST_GAME_VER_RIGHT,
                        style={'marginBottom': '3em'}
                    ),
                ]
            ),
            # days since release
            html.Div(
                className="two columns",
                children=[
                    dcc.Markdown(d("""**Days Since Release**""")),
                    dcc.Slider(
                        id='my-range-slider',
                        min=0,
                        max=7,
                        value=DAYS_SINCE_RELEASE,
                        marks={i: '{}'.format(i) for i in range(8)},
                        included=False
                    )
                ]
            ),
            # country
            html.Div(
                className="two columns",
                children=[
                    dcc.Markdown(d("""**Highlight - Country**""")),
                    dcc.Dropdown(
                        id='dropdown-country',
                        options=[{'label': x, 'value': x} for x in graph_raw_data['country']],
                        multi=True
                    ),
                ]
            ),
            # channel
            html.Div(
                className="two columns",
                children=[
                    dcc.Markdown(d("""**Highlight - Acquisition Channel**""")),
                    dcc.Dropdown(
                        id='dropdown-network-name',
                        options=[{'label': x, 'value': x} for x in graph_raw_data['network']],
                        multi=True
                    ),
                ]
            ),
            # demographic
            html.Div(
                className="two columns",
                children=[
                    dcc.Markdown(d("""**Highlight - Demographic**""")),
                    dcc.Dropdown(
                        id='dropdown-demographic',
                        options=[{'label': x, 'value': x} for x in graph_raw_data['demographic']],
                        multi=True
                    ),
                ]
            ),
        ]),
    # graph
    html.Div(
        className="row",
        children=
        [
            html.Div(
                className="six columns",
                children=[dcc.Graph(id="my-graph",
                                    figure=network_graph(
                                        raw_data_object=graph_raw_data['raw_data_object'],
                                        first_game_ver=FIRST_GAME_VER_LEFT,
                                        days_since_release=DAYS_SINCE_RELEASE,
                                        node_size=NODE_SIZE,
                                        node_color=NODE_COLOR,
                                        node=NODE,
                                        edge_color=EDGE_COLOR,
                                        edge_size=EDGE_SIZE,
                                        highlight=HIGHLIGHT)['a1_plotly'])],
            ),
            html.Div(
                className="six columns",
                children=[dcc.Graph(id="my-graph1",
                                    figure=network_graph(
                                        raw_data_object=graph_raw_data['raw_data_object'],
                                        first_game_ver=FIRST_GAME_VER_RIGHT,
                                        days_since_release=DAYS_SINCE_RELEASE,
                                        node_size=NODE_SIZE,
                                        node_color=NODE_COLOR,
                                        node=NODE,
                                        edge_color=EDGE_COLOR,
                                        edge_size=EDGE_SIZE,
                                        highlight=HIGHLIGHT)['a1_plotly'])],
            ),
        ]
    )
])


@app.callback(
    dash.dependencies.Output('my-graph', 'figure'),
    [
        dash.dependencies.Input('my-range-slider', 'value'),
        dash.dependencies.Input('dropdown-game-ver-left', 'value'),
        dash.dependencies.Input('dropdown-country', 'value'),
        dash.dependencies.Input('dropdown-network-name', 'value'),
        dash.dependencies.Input('dropdown-demographic', 'value'),
    ])
def update_output(value, game_ver_left, country, network_name, demographic):
    DAYS_SINCE_RELEASE = value
    FIRST_GAME_VER_LEFT = game_ver_left
    HIGHLIGHT = {}
    if country:
        HIGHLIGHT['country'] = country
    if network_name:
        HIGHLIGHT['network_name'] = network_name
    if demographic:
        HIGHLIGHT['demographic'] = demographic
    return network_graph(raw_data_object=graph_raw_data['raw_data_object'],
                         first_game_ver=FIRST_GAME_VER_LEFT,
                         days_since_release=DAYS_SINCE_RELEASE,
                         node_size=NODE_SIZE,
                         node_color=NODE_COLOR,
                         node=NODE,
                         edge_color=EDGE_COLOR,
                         edge_size=EDGE_SIZE,
                         highlight=HIGHLIGHT
                         )['a1_plotly']


# callback for my-graph1
@app.callback(
    dash.dependencies.Output('my-graph1', 'figure'),
    [
        dash.dependencies.Input('my-range-slider', 'value'),
        dash.dependencies.Input('dropdown-game-ver-right', 'value'),
        dash.dependencies.Input('dropdown-country', 'value'),
        dash.dependencies.Input('dropdown-network-name', 'value'),
        dash.dependencies.Input('dropdown-demographic', 'value'),
    ])
def update_output(value, game_ver_right, country, network_name, demographic):
    DAYS_SINCE_RELEASE = value
    FIRST_GAME_VER_RIGHT = game_ver_right
    HIGHLIGHT=dict()
    if country:
        HIGHLIGHT['country'] = country
    if network_name:
        HIGHLIGHT['network_name'] = network_name
    if demographic:
        HIGHLIGHT['demographic'] = demographic
    return network_graph(raw_data_object=graph_raw_data['raw_data_object'],
                         first_game_ver=FIRST_GAME_VER_RIGHT,
                         days_since_release=DAYS_SINCE_RELEASE,
                         node_size=NODE_SIZE,
                         node_color=NODE_COLOR,
                         node=NODE,
                         edge_color=EDGE_COLOR,
                         edge_size=EDGE_SIZE,
                         highlight=HIGHLIGHT)['a1_plotly']


if __name__ == '__main__':
    app.run_server(debug=True, port=4455)
