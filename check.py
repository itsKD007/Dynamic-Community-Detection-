from bokeh.plotting import figure, show
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.io import curdoc
from bokeh.layouts import column
from bokeh.models import Slider
import networkx as nx
import pandas as pd
from networkx.algorithms import community
from bokeh.palettes import Category20_20

# Read CSV file
csv_file = 'hcw_edges.csv'
df = pd.read_csv(csv_file)

# Create a directed graph to represent temporal edges
G = nx.DiGraph()

# Create Bokeh plot
plot = figure(title="Community Structure", tools="pan,wheel_zoom,save,reset, tap", active_scroll='wheel_zoom')

# Initialize empty data sources for edges and nodes
edge_source = ColumnDataSource(data={'x0': [], 'y0': [], 'x1': [], 'y1': []})
node_source = ColumnDataSource(data={'x': [], 'y': [], 'index': [], 'community': [], 'fill_color': [], 'size': []})

# Add edges and nodes for each timestep
def update_plot(attrname, old_range, new_range):
    timestep = slider.value
    G_timestep = nx.DiGraph()
    # Add time-stamped edges to the graph for the current timestep
    for index, row in df.iterrows():
        if row['time_start'] <= timestep <= row['time_end']:
            G_timestep.add_edge(row['Source'], row['Target'])

    # Perform community detection (Louvain method)
    communities = community.greedy_modularity_communities(G_timestep.to_undirected())

    # Extract community information for each node
    node_community_dict = {node: i for i, comm in enumerate(communities) for node in comm}

    # Use Kamada-Kawai for the graph layout
    pos = nx.kamada_kawai_layout(G_timestep)

    # Get node degrees (influence) and normalize for node size
    node_degrees = dict(G_timestep.degree())
    max_degree = max(node_degrees.values())
    node_sizes = {node: 10 + 15 * (node_degrees[node] / max_degree) for node in G_timestep.nodes()}

    # Update edge data source
    edge_source.data = {'x0': [], 'y0': [], 'x1': [], 'y1': []}
    for edge in G_timestep.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_source.data['x0'].append(x0)
        edge_source.data['y0'].append(y0)
        edge_source.data['x1'].append(x1)
        edge_source.data['y1'].append(y1)

    # Update node data source
    node_source.data = {'x': [], 'y': [], 'index': [], 'community': [], 'fill_color': [], 'size': []}

    for node in G_timestep.nodes():
        x, y = pos[node]
        community_color = Category20_20[node_community_dict[node] % len(Category20_20)]
        node_source.data['x'].append(x)
        node_source.data['y'].append(y)
        node_source.data['index'].append(node)
        node_source.data['community'].append(node_community_dict[node])
        node_source.data['fill_color'].append(community_color)
        node_source.data['size'].append(node_sizes[node])

    
    # Add edges to the plot
    edge_renderer = plot.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=edge_source,
                                line_width=1, line_color="gray", line_alpha=0.6)

    # Add nodes to the plot with community-specific colors, influence-based size, and hover
    node_renderer = plot.circle(x='x', y='y', size='size', source=node_source, line_color='black',
                                fill_color='fill_color', legend_field='community')

    # Add hover for nodes
    hover_nodes = HoverTool(renderers=[node_renderer],
                            tooltips=[("Node", "@index"), ("Community", "@community")])

    plot.add_tools(hover_nodes)


slider = Slider(start=df['time_start'].min(), end=df['time_end'].max(),
                value=df['time_start'].min(), step=1, title="Timestep")
slider.on_change('value', update_plot)

# Create layout
layout = column(slider, plot)

# Set up the document
curdoc().add_root(layout)
curdoc().title = "Temporal Community Structure"

# Show the plot
show(layout)
