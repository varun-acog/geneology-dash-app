import dash
from dash import dcc, html, Input, Output, callback, State, clientside_callback
import dash_ag_grid as dag
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from Lineage import get_item_codes
from dash.exceptions import PreventUpdate
from Lineage import get_lineage

# Generate dummy data for the table
np.random.seed(42)
n_rows = 50

dummy_data = {
    'ParentItemCode': [f'CT17{i:02d}' for i in range(1, n_rows + 1)],
    'ParentName': [f'CT17{i}-1780' for i in range(1, n_rows + 1)],
    'ParentPN': [f'CT17{i}-1780' for i in range(1, n_rows + 1)],
    'Level': np.random.choice([3, 4, 5], n_rows),
    'ProductItemCode': [f'PT17{i:02d}' for i in range(100, 100 + n_rows)],
    'ProductName': [f'PT17{i}-1780' for i in range(100, 100 + n_rows)],
    'ProductPN': [f'PT17{i}-1780' for i in range(100, 100 + n_rows)],
    'IngredientItemCode': [f'CT1{i:02d}' for i in range(200, 200 + n_rows)],
    'IngredientName': [f'CT1N-{i:04d}' for i in range(1780, 1780 + n_rows)]
}

df = pd.DataFrame(dummy_data)

# Generate dummy network data for visualization
network_nodes = []
network_edges = []

# Create nodes
for i in range(20):
    network_nodes.append({
        'id': f'node_{i}',
        'label': f'Item {i}',
        'x': np.random.uniform(-2, 2),
        'y': np.random.uniform(-2, 2),
        'size': np.random.uniform(10, 30)
    })

# Create edges
for i in range(15):
    source = np.random.randint(0, 10)
    target = np.random.randint(10, 20)
    network_edges.append({
        'source': source,
        'target': target
    })

def create_network_graph():
    """Create a network visualization graph"""
    fig = go.Figure()
    
    # Add edges
    edge_x = []
    edge_y = []
    for edge in network_edges:
        source_node = network_nodes[edge['source']]
        target_node = network_nodes[edge['target']]
        edge_x.extend([source_node['x'], target_node['x'], None])
        edge_y.extend([source_node['y'], target_node['y'], None])
    
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    ))
    
    # Add nodes
    node_x = [node['x'] for node in network_nodes]
    node_y = [node['y'] for node in network_nodes]
    node_text = [node['label'] for node in network_nodes]
    
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="middle center",
        textfont=dict(size=10, color='#ffffff'),
        hoverinfo='text',
        marker=dict(
            size=[node['size'] for node in network_nodes],
            color='#4682b4',
            line=dict(width=2, color='#2f4f4f')
        )
    ))
    
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Initialize the Dash app
app = dash.Dash(__name__)

# Define custom styles
styles = {
    'container': {
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '20px',
        'fontFamily': '"Segoe UI", "Helvetica Neue", Arial, sans-serif',
        'backgroundColor': '#f5f7fa',
        'minHeight': '100vh',
        'boxSizing': 'border-box'
    },
    'header': {
        'backgroundColor': '#2c3e50',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginBottom': '20px'
    },
    'headerText': {
        'color': '#ffffff',
        'textAlign': 'center',
        'fontSize': '32px',
        'fontWeight': '600',
        'margin': '0'
    },
    'section': {
        'backgroundColor': '#ffffff',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
        'padding': '20px',
        'marginBottom': '20px'
    },
    'sectionTitle': {
        'fontSize': '18px',
        'fontWeight': '600',
        'color': '#2c3e50',
        'marginBottom': '15px',
        'borderLeft': '4px solid #3498db',
        'paddingLeft': '10px'
    },
    'dropdown': {
        'width': '100%',
        'fontSize': '14px',
        'borderRadius': '4px',
        'marginBottom': '10px'
    },
    'input': {
        'width': '100%',
        'height': '38px',
        'fontSize': '14px',
        'border': '1px solid #d1d5db',
        'borderRadius': '4px',
        'padding': '0 10px',
        'boxSizing': 'border-box'
    },
    'button': {
        'padding': '8px 16px',
        'fontSize': '14px',
        'border': 'none',
        'borderRadius': '4px',
        'cursor': 'pointer',
        'transition': 'background-color 0.2s'
    },
    'primaryButton': {
        'backgroundColor': '#3498db',
        'color': '#ffffff',
        'padding': '10px 20px',
        'fontSize': '14px',
        'border': 'none',
        'borderRadius': '4px',
        'cursor': 'pointer',
        'transition': 'background-color 0.2s',
        'width': '100%'
    },
    'checkboxLabel': {
        'fontSize': '14px',
        'marginRight': '15px',
        'display': 'inline-block',
        'verticalAlign': 'middle'
    },
    'checkbox': {
        'marginRight': '5px',
        'verticalAlign': 'middle'
    },
    'exportButton': {
        'backgroundColor': '#3498db',
        'color': '#ffffff',
        'padding': '8px 24px',
        'fontSize': '14px',
        'border': 'none',
        'borderRadius': '4px',
        'cursor': 'pointer',
        'transition': 'background-color 0.2s'
    },
    'clearButton': {
        'backgroundColor': '#E2EAF4',
        'color': '#3498db',
        'padding': '8px 24px',
        'fontSize': '14px',
        'border': 'none',
        'borderRadius': '4px',
        'cursor': 'pointer',
        'transition': 'background-color 0.2s'
    }
}

# AG Grid column definitions with filtering enabled
columnDefs = [
    {"field": "ParentItemCode", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "ParentName", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "ParentPN", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "Level", "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["equals"], "suppressAndOrCondition": True}},
    {"field": "ProductItemCode", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "ProductName", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "ProductPN", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "IngredientItemCode", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "IngredientName", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "IngredientPN", "filter": "agTextColumnFilter", "filterParams": {"filterOptions": ["contains"], "suppressAndOrCondition": True}},
    {"field": "CntRecs", "filter": "agNumberColumnFilter", "filterParams": {"filterOptions": ["equals"], "suppressAndOrCondition": True}}
]

# AG Grid default column properties
defaultColDef = {
    "sortable": True,
    "filter": True,
    "resizable": True,
    "editable": False,
    "minWidth": 100,
    "headerStyle": {"backgroundColor": "#2c3e50", "color": "#ffffff", "fontWeight": "600", "fontSize": "13px"}
}

# Define the layout
app.layout = html.Div([
    # Main container
    html.Div([
        # Header
        html.Div([
            html.H1("Genealogy App", style=styles['headerText'])
        ], style=styles['header']),
        
        # Filters and controls section
        html.Div([
            # Left side controls (Filters)
            html.Div([
                html.H4("Filters", style=styles['sectionTitle']),
                
                # FROM and TO inputs
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='from-dropdown',
                            multi=True,
                            clearable=False,
                            placeholder='FROM',
                            style=styles['dropdown']
                        )
                    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),
                    html.Div([
                        dcc.Dropdown(
                            id='to-dropdown',
                            placeholder='TO',
                            multi=True,
                            clearable=False,
                            style=styles['dropdown']
                        )
                    ], style={'width': '48%', 'display': 'inline-block'})
                ], style={'marginBottom': '15px'}),
            
                # Level checkboxes (replacing buttons)
                html.Div([
                    dcc.Checklist(
                        id='lot-level-check',
                        options=[{'label': 'Lot Level', 'value': 'lot'}],
                        value=['lot'],  # Set Lot Level as checked by default
                        style={'display': 'inline-block'},
                        labelStyle=styles['checkboxLabel'],
                        inputStyle=styles['checkbox']
                    ),
                    dcc.Checklist(
                        id='bag-level-check',
                        options=[{'label': 'Bag Level', 'value': 'bag'}],
                        value=[],
                        style={'display': 'inline-block'},
                        labelStyle=styles['checkboxLabel'],
                        inputStyle=styles['checkbox']
                    ),
                    html.Div([
                        html.Button("Submit", id="submit-button", style=styles['exportButton']),
                        html.Button("Clear", id="clear-button", style=styles['clearButton'])
                    ], style={'textAlign': 'right', 'marginBottom': '10px'}),
                ])
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '20px'}),
            
            # Right side - Data Required
            html.Div([
                # Data Required
                html.Div([
                    html.H4("Data Required", style=styles['sectionTitle']),
                    html.Div([
                        dcc.Checklist(
                            id='data-required-check',
                            options=[
                                {'label': 'PI', 'value': 'pi'},
                                {'label': 'DISCO', 'value': 'disco'},
                                {'label': 'SAP', 'value': 'sap'},
                                {'label': 'LIMS', 'value': 'lims'},
                                {'label': 'MES', 'value': 'mes'},
                                {'label': 'EBS', 'value': 'ebs'}
                            ],
                            value=[],
                            labelStyle={**styles['checkboxLabel'], 'margin': '5px'},
                            inputStyle=styles['checkbox']
                        )
                    ])
                ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style=styles['section']),
        
        # Visualization section
        html.Div([
            html.Div([
                html.H4("Visualization", style=styles['sectionTitle']),
                # Export button in a separate div, aligned to the right
                html.Div([
                    html.Button("Export", style=styles['exportButton'])
                ], style={'textAlign': 'right', 'marginBottom': '10px'}),
                # Graph
                dcc.Graph(
                    id='network-graph',
                    figure=create_network_graph(),
                    style={'height': '500px', 'border': '1px solid #ecf0f1', 'borderRadius': '4px'}
                )
            ])
        ], style=styles['section']),
        
        # Data section
        html.Div([
            html.Div([
                html.H4("Data", style=styles['sectionTitle']),
                dag.AgGrid(
                    id='data-table',
                    columnDefs=columnDefs,
                    rowData=df.to_dict('records'),
                    defaultColDef=defaultColDef,
                    style={'height': '400px', 'width': '100%'},
                    dashGridOptions={
                        "pagination": True,
                        "paginationPageSize": 20,
                        # Removed domLayout="autoHeight" to fix pagination
                    },
                    className="ag-theme-alpine"
                )
            ], style={'width': '70%', 'display': 'inline-block', 'paddingRight': '20px'}),
            
            # Export buttons
            html.Div([
                html.Div([
                    html.Button("Export Genealogy", id="export-genealogy-button", style={**styles['primaryButton'], 'marginBottom': '10px'}),
                    html.Button("Export with Required Data", style=styles['primaryButton'])
                ])
            ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style=styles['section'])
    ], style=styles['container'])
])

# Clientside callback for Export Genealogy button to export all data
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            const grid = document.querySelector('#data-table .ag-root-wrapper');
            if (grid && grid.__gridApi) {
                const gridApi = grid.__gridApi;
                gridApi.exportDataAsCsv({
                    fileName: 'genealogy_data.csv',
                    allColumns: true,
                    onlySelected: false,
                    suppressQuotes: false,
                    columnSeparator: ','
                });
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('data-table', 'id'),  # Dummy output to satisfy callback requirement
    Input('export-genealogy-button', 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    Output("from-dropdown", "options"),
    Input("from-dropdown", "search_value"),
    State("from-dropdown", "value")
)
def update_multi_options(search_value, value):
    if not search_value:
        raise PreventUpdate
    return get_item_codes(search_value)

@callback(
    Output("to-dropdown", "options"),
    Input("to-dropdown", "search_value"),
    State("to-dropdown", "value")
)
def update_multi_options(search_value, value):
    if not search_value:
        raise PreventUpdate
    return get_item_codes(search_value)

# Callback for interactive filtering - triggered by Submit button
@app.callback(
    Output('data-table', 'rowData'),
    [Input('submit-button', 'n_clicks')],
    [State('from-dropdown', 'value'),
     State('to-dropdown', 'value')]
)
def update_table(n_clicks, from_val, to_val):
    # Only process if Submit button was clicked and at least one value is provided
    if not n_clicks or (not from_val and not to_val):
        return df.to_dict('records')  # Return dummy data if no submission
    
    try:
        # Prepare parameters for get_lineage function
        varTraceFor = None
        varTraceTarget = None
        
        if from_val:
            varTraceFor = "', '".join(from_val) if isinstance(from_val, list) else str(from_val)
        
        if to_val:
            varTraceTarget = "', '".join(to_val) if isinstance(to_val, list) else str(to_val)
        
        # Get lineage data from database
        outputType = "polars"  # "polars" or "duckdb"
        GenOrTrc = "all"  # "trc", "gen", or "all"
        level = -99  # -99 for all levels, 1 for first level, etc.
        
        # Fetch data with the specified output columns
        res = get_lineage(varTraceFor, varTraceTarget, outputType, GenOrTrc, level, 
                         outputcols="type, root_parentlot, product_parentlot as startnode, ingredient_parentlot as endnode, level")
        
        print("Database result:", res)
        print("Columns:", res.columns if hasattr(res, 'columns') else 'No columns attribute')
        
        # Convert polars DataFrame to list of dictionaries and map columns
        if res is not None and len(res) > 0:
            # Convert to pandas if it's a polars DataFrame
            if hasattr(res, 'to_pandas'):
                df_result = res.to_pandas()
            else:
                df_result = res
            
            # Map database columns to display columns as specified
            mapped_data = []
            for _, row in df_result.iterrows():
                mapped_row = {
                    'ParentItemCode': row.get('root_parentlot', ''),
                    'ParentName': row.get('root_parentlot', ''),
                    'ParentPN': row.get('root_parentlot', ''),
                    'Level': row.get('Level', ''),
                    'ProductItemCode': row.get('startnode', ''),
                    'ProductName': row.get('startnode', ''),
                    'ProductPN': row.get('startnode', ''),
                    'IngredientItemCode': row.get('endnode', ''),
                    'IngredientName': row.get('endnode', ''),
                    'IngredientPN': row.get('endnode', ''),
                    'CntRecs': row.get('CntRecs', '')
                }
                mapped_data.append(mapped_row)
            
            return mapped_data
        else[ res.to_dict('records')  # Return dummy data if no results
            
    except Exception as e:
        print(f"Error getting lineage data: {e}")
        return df.to_dict('records')  # Return dummy data on error

# Callback for Clear button
@app.callback(
    [Output('from-dropdown', 'value'),
     Output('to-dropdown', 'value'),
     Output('data-table', 'rowData', allow_duplicate=True)],
    [Input('clear-button', 'n_clicks')],
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    if n_clicks:
        return None, None, df.to_dict('records')  # Reset to dummy data
    return dash.no_update, dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run(debug=True)