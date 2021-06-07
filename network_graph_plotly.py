import networkx as nx
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import random


class NetworkGraph:
    def __init__(self, df_nodes_raw, df_edges_raw):
        self.df_nodes_raw = df_nodes_raw
        self.df_edges_raw = df_edges_raw

    def data_filtered(self, first_game_ver, days_since_release):
        """

        :param first_game_ver:
        :param days_since_release:
        :return:
        """
        # nodes - filter by kwargs
        df_nodes = self.df_nodes_raw.loc[
            (
                    self.df_nodes_raw['first_game_ver'] == first_game_ver
            ) & (
                    self.df_nodes_raw['days_since_release'] == days_since_release
            )]
        playerSet = set(df_nodes['device_id'])
        # edges - filter by kwargs
        df_edges = self.df_edges_raw.loc[
            (
                    self.df_edges_raw['days_since_release'] == days_since_release
            ) & (
                self.df_edges_raw['source_device_id'].isin(playerSet)
            ) & (
                self.df_edges_raw['target_device_id'].isin(playerSet)
            )]

        return {'df_nodes': df_nodes, 'df_edges': df_edges}

    def node_color_map(self, node_color):
        """

        :param node_color: field name as node color, eg network_name
        :return: a pd df of mapping ef network_name & node_color (randomly generated) :  Organic & #DD234A
        """
        # node_color
        node_color_unique = sorted(set(self.df_nodes_raw[node_color]))
        number_of_colors = len(node_color_unique)
        # generate colors
        random.seed(20)
        color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                 for i in range(number_of_colors)]
        # map color -> node_color
        node_color_map = dict(zip(node_color_unique, color))
        node_color_map = pd.DataFrame.from_dict(node_color_map, orient='index').reset_index().rename(
            columns={0: 'node_color', 'index': node_color})

        return node_color_map

    def edge_color_map(self, edge_color):
        # generate colors
        color = ['#303773', '#FF2B95']
        # map color -> node_color
        color_map = dict(zip([1, 2], color))
        color_map = pd.DataFrame.from_dict(color_map, orient='index').reset_index().rename(
            columns={0: 'edge_color', 'index': edge_color})

        return color_map

    def graph_data_networkx(self, df_nodes, df_edges, node, node_size, node_color, edge_color, edge_size=None,
                            highlight={}
                            ):
        """

        :param df_nodes:
        :param df_edges:
        :param node:
        :param node_size:
        :param node_color:
        :param edge_color:
        :param edge_size:
        :param highlight: a dict eg {'demographic': ['unknown'], 'country':['GB','AU'], 'network_name':['Organic','Facebook']}
        :return:
        """
        try:
            # node
            df_nodes['node'] = df_nodes[node]
            # node_size
            df_nodes['node_size_raw'] = df_nodes[node_size]
            df_nodes['node_size'] = df_nodes[node_size]
            df_nodes['node_size'] = df_nodes['node_size'] / (
                    df_nodes['node_size'].max() - df_nodes['node_size'].min()) * 30

            # node_color
            node_color_map = self.node_color_map(node_color)
            df_nodes = pd.merge(
                df_nodes,
                node_color_map,
                on=node_color
            )

            # node color - grey out nodes by filters
            if len(highlight.keys()) > 0:
                for index, value in highlight.items():
                    df_nodes['node_color'] = np.where(
                        df_nodes[index].isin(value),
                        df_nodes['node_color'],
                        '#F9F6F6 '
                    )

            # edge_color
            edge_color_map = self.edge_color_map(edge_color)
            df_edges = pd.merge(
                df_edges,
                edge_color_map,
                on=edge_color
            )

            # edge_size
            if edge_size:
                df_edges['edge_size'] = df_edges[edge_size]

            # networkx graph
            # add nodes & edges
            G = nx.MultiGraph()

            # nodes - add nodes [node_size, node_color]
            G.add_nodes_from(
                [
                    (
                        row.node,
                        dict(node_size_raw=row.node_size_raw,
                             node_size=row.node_size,
                             node_color=row.node_color,
                             country=row.country,
                             days_since_release=row.days_since_release,
                             network_name=row.network_name,
                             first_game_ver=row.first_game_ver,
                             demographic=row.demographic
                             )
                    ) for row in df_nodes.itertuples()
                ]
            )

            # edges - add edges [edge_size]
            G.add_edges_from(
                [
                    (
                        row.source_device_id,
                        row.target_device_id,
                        {
                            'weight': row.edge_size if 'edge_size' in df_edges.columns else 0,
                            'edge_color': row.edge_color
                        }
                    ) for row in df_edges.itertuples()
                ], weight='weight'
            )

            # get position for nodes
            pos = nx.spring_layout(G, k=0.5, iterations=50, weight=None, seed=42)
            for n, p in pos.items():
                G.nodes[n]['pos'] = p

            return {
                'G': G,
                'node': node, 'node_size': node_size, 'node_color': node_color,
                'edge_color': edge_color, 'edge_size': edge_size
            }

        except:
            raise

    @staticmethod
    def graph_data_plotly(networkx_data, title):
        G = networkx_data['G']
        # create edges
        edge_trace = []
        for edge in G.edges(data=True):
            x0, y0 = G.nodes[edge[0]]['pos']
            x1, y1 = G.nodes[edge[1]]['pos']
            color = edge[2]['edge_color']
            if networkx_data['edge_size']:
                weight = edge[2]['weight']
            else:
                weight = 0.7
            trace = go.Scatter(x=tuple([x0, x1, None]), y=tuple([y0, y1, None]),
                               mode='lines',
                               line={'width': weight, 'color': color},
                               line_shape='spline')
            edge_trace.append(trace)

        # create nodes
        node_trace = []
        for node in G.nodes():
            x, y = G.nodes[node]['pos']
            size = G.nodes[node]['node_size']
            node_size_label = G.nodes[node]['node_size_raw']
            color = G.nodes[node]['node_color']
            hovertext = "<br>" + "Country: " + str(G.nodes[node]['country']) + \
                        "<br>" + "Channel: " + str(G.nodes[node]['network_name']) + \
                        "<br>" + "Demo: " + str(G.nodes[node]['demographic']) + \
                        "<br>" + networkx_data['node_size'] + ": " + str("{0:.2f}".format(node_size_label))
            trace = go.Scatter(x=tuple([x]),
                               y=tuple([y]),
                               hovertext=hovertext,
                               hoverinfo="text",
                               marker={'size': size, 'color': color}
                               )
            node_trace.append(trace)

        traces = edge_trace + node_trace

        figure = {
            "data": traces,
            "layout": go.Layout(title=title,
                                showlegend=False, hovermode='closest',
                                margin={'b': 40, 'l': 40, 'r': 40, 't': 40},
                                xaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                yaxis={'showgrid': False, 'zeroline': False, 'showticklabels': False},
                                height=600,
                                clickmode='event+select',
                                )}

        return figure

