import dash
from dash import dcc, html, Input, Output, callback, State, clientside_callback
from dash_echarts import DashECharts
import dash_ag_grid as dag
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
from Lineage import get_item_codes
from dash.exceptions import PreventUpdate
from Lineage import get_lineage

# Custom CSS for loading spinner
external_stylesheets = [
    {
        'href': 'https://use.fontawesome.com/releases/v5.8.1/css/all.css',
        'rel': 'stylesheet',
        'integrity': 'sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf',
        'crossorigin': 'anonymous'
    },
    """
    .dash-loading {
        display: flex;
        justify-content: center;
        align-items: center;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 9999;
        background: rgba(255, 255, 255, 0.5);  /* Semi-transparent overlay */
        width: 100%;
        height: 100%;
        pointer-events: none;  /* Allow interaction with elements underneath */
    }
    .dash-loading-callback {
        font-size: 24px;
    }
    """
]

# Initialize the Dash app with custom CSS
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Function to create a network visualization graph (currently unused, replaced by ECharts)
def create_network_graph():
    """Create a network visualization graph"""
    fig = go.Figure()
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

# Modified csv_to_hierarchy function to handle root_parentlot as the root and prevent cycles
def csv_to_hierarchy(csv_data):
    # Dictionary to track nodes with their metadata
    node_info = {}

    # Track all relationships
    relationships = []

    # First pass: create all nodes with their metadata
    for _, row in csv_data.iterrows():
        root = row['root']
        source = row['source']
        ingredient = row['ingredient']
        root_desc = row.get('root desc', '')
        source_desc = row.get('source desc', '')
        ingredient_desc = row.get('ingredient description', '')
        level = row.get('level', 0)

        # Add root node if it doesn't exist
        if root not in node_info:
            node_info[root] = {
                "name": root,
                "description": root_desc,
                "references": [],
                "level": 0,  # Root is at level 0
                "workforce": 0,
                "Quantity": 0
            }

        # Add source if it doesn't exist
        if source not in node_info:
            node_info[source] = {
            "name": source,
            "description": source_desc,
            "references": [],
            "level": 1,  # Source is at level 1
            "workforce": 0,
            "Quantity": 0
            }

        # Add ingredient if it doesn't exist
        if ingredient not in node_info:
            node_info[ingredient] = {
                "name": ingredient,
                "description": ingredient_desc,
                "references": [],
                "level": level,  # Use the Level from the data
                "workforce": 0,
                "Quantity": 0
            }

        # Track relationships: root -> source and source -> ingredient
        relationships.append((root, source))
        relationships.append((source, ingredient))
        node_info[source]["references"].append(root)
        node_info[ingredient]["references"].append(source)

    # Build the tree starting from unique root nodes
    unique_roots = csv_data['root'].unique()
    if len(unique_roots) > 1:
        # Create a virtual root if there are multiple root_parentlot values
        root_name = "All Processes"
        node_info[root_name] = {
            "name": root_name,
            "description": "All Manufacturing Processes",
            "references": [],
            "level": 0,
            "workforce": 0,
            "Quantity": 0
        }
        for root in unique_roots:
            relationships.append((root_name, root))
            node_info[root]["references"].append(root_name)
        root_name = root_name
    else:
        root_name = unique_roots[0]

    # Build the tree
    tree = {
        "name": node_info[root_name]["name"],
        "description": node_info[root_name]["description"],
        "children": [],
        "shared": False,
        "id": root_name,
        "level": node_info[root_name]["level"],
        "workforce": node_info[root_name]["workforce"],
        "Quantity": node_info[root_name]["Quantity"]
    }

    # Build a map of parent -> children
    parent_to_children = {}
    for parent, child in relationships:
        if parent not in parent_to_children:
            parent_to_children[parent] = []
        parent_to_children[parent].append(child)

    # Helper function to recursively build the tree with cycle detection
    def build_tree(node_id, parent_node, visited=None):
        if visited is None:
            visited = set()  # Initialize visited set on first call
        
        if node_id in visited:
            return  # Skip if node has already been visited (cycle detected)
        
        visited.add(node_id)  # Mark the current node as visited
        
        if node_id in parent_to_children:
            for child_id in parent_to_children[node_id]:
                child_node = {
                    "name": node_info[child_id]["name"],
                    "description": node_info[child_id]["description"],
                    "children": [],
                    "shared": len(node_info[child_id]["references"]) > 1,
                    "id": child_id,
                    "level": node_info[child_id]["level"],
                    "workforce": node_info[child_id]["workforce"],
                    "Quantity": node_info[child_id]["Quantity"]
                }
                parent_node["children"].append(child_node)
                build_tree(child_id, child_node, visited)  # Recursive call with visited set

    # Start building from the root
    build_tree(root_name, tree)

    return tree

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
    # Download components for file exports
    dcc.Download(id="download-all-data"),
    dcc.Download(id="download-filtered-data"),
    
    # Store components for data management
    dcc.Store(id="all-data-store"),
    dcc.Store(id="filtered-data-store"),
    
    # Main container
    html.Div([
        # Header
        html.Div([
            html.H1("Genealogy App", style=styles['headerText'])
        ], style=styles['header']),
        
        # Filters and controls section
        html.Div([
            # Left side controls (Filters) with loading state
            dcc.Loading(
                id="loading-filters",
                type="default",
                color="#3498db",
                children=[
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
                    ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '20px', 'position': 'relative'})
                ]
            ),
            
            # Right side - Data Required and Additional Filters (side by side)
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
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '4%'}),
                
                # Additional Filters (stacked vertically)
                html.Div([
                    html.H4("Additional Filters", style=styles['sectionTitle']),
                    html.Div([
                        dcc.Dropdown(
                            id='unit-operation-dropdown',
                            multi=True,
                            clearable=True,
                            placeholder='Unit Operation',
                            style=styles['dropdown']
                        ),
                        dcc.Dropdown(
                            id='attribute-dropdown',
                            multi=True,
                            clearable=True,
                            placeholder='Attribute',
                            style=styles['dropdown'],
                            options=[]  # Keep Attribute dropdown empty as requested
                        )
                    ])
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style=styles['section']),
        
        # Visualization section with ECharts tree chart
        html.Div([
            html.Div([
                html.H4("Visualization", style=styles['sectionTitle']),
                # Export button with an ID
                html.Div([
                    html.Button("Export", id="export-visualization-button", style=styles['exportButton'])
                ], style={'textAlign': 'right', 'marginBottom': '10px'}),
                # ECharts tree chart
                DashECharts(
                    id='tree-chart',
                    option={},
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
                    rowData=[],  # Set initial rowData to empty list to hide table
                    defaultColDef=defaultColDef,
                    style={'height': '400px', 'width': '100%'},
                    dashGridOptions={
                        "pagination": True,
                        "paginationPageSize": 20,
                        "suppressExcelExport": False,
                        "suppressCsvExport": False,
                    },
                    className="ag-theme-alpine",
                    enableEnterpriseModules=False,  # Use community features
                )
            ], style={'width': '70%', 'display': 'inline-block', 'paddingRight': '20px'}),
            
            # Export buttons
            html.Div([
                html.Div([
                    html.Button("Export Genealogy", id="export-genealogy-button", style={**styles['primaryButton'], 'marginBottom': '10px'}),
                    html.Button("Export with Required Data", id="export-filtered-button", style=styles['primaryButton'])
                ])
            ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style=styles['section'])
    ], style=styles['container'])
])

# Callback to populate Unit Operation dropdown with unique ProductItemCode and IngredientItemCode values
@app.callback(
    Output('unit-operation-dropdown', 'options'),
    Input('all-data-store', 'data'),
    prevent_initial_call=True
)
def update_unit_operation_options(data):
    if not data:
        return []
    
    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(data)
    
    # Extract unique values from ProductItemCode and IngredientItemCode
    product_item_codes = df['ProductItemCode'].dropna().unique()
    ingredient_item_codes = df['IngredientItemCode'].dropna().unique()
    
    # Combine and get unique values
    all_item_codes = set(product_item_codes).union(set(ingredient_item_codes))
    
    # Convert to dropdown options format
    options = [{'label': str(code), 'value': str(code)} for code in sorted(all_item_codes)]
    
    return options

# Callback to generate hierarchical data and update the ECharts tree chart
@app.callback(
    Output('tree-chart', 'option'),
    Input('all-data-store', 'data'),
    prevent_initial_call=True
)
def update_tree_chart(data):
    if not data:
        return {}

    # Convert the table data to a DataFrame
    df = pd.DataFrame(data)
    
    # Map columns to match csv_to_hierarchy expectations
    # Now including root_parentlot as the root
    hierarchy_data = pd.DataFrame({
        'root': df['ParentItemCode'],  # root_parentlot
        'source': df['ProductItemCode'],  # startnode
        'ingredient': df['IngredientItemCode'],  # endnode
        'root desc': df['ParentName'],  # root_parentlot (same as ParentItemCode)
        'source desc': df['ProductName'],  # startnode (same as ProductItemCode)
        'ingredient description': df['IngredientName'],  # endnode (same as IngredientItemCode)
        'level': df['Level'],  # Use Level to determine hierarchy depth
    })

    # Remove rows with NaN values in root, source, or ingredient to avoid errors
    hierarchy_data = hierarchy_data.dropna(subset=['root', 'source', 'ingredient'])

    if hierarchy_data.empty:
        return {}

    # Generate the hierarchical JSON
    tree_data = csv_to_hierarchy(hierarchy_data)

    # ECharts tree chart configuration
    option = {
        "tooltip": {
            "trigger": "item",
            "triggerOn": "mousemove",
            "formatter": "{b}<br/>"
        },
        "series": [
            {
                "type": "tree",
                "data": [tree_data],
                "top": "1%",
                "left": "7%",
                "bottom": "1%",
                "right": "20%",
                "symbolSize": 7,
                "label": {
                    "position": "left",
                    "verticalAlign": "middle",
                    "align": "right",
                    "fontSize": 9
                },
                "leaves": {
                    "label": {
                        "position": "right",
                        "verticalAlign": "middle",
                        "align": "left"
                    }
                },
                "emphasis": {
                    "focus": "descendant"
                },
                "expandAndCollapse": True,
                "animationDuration": 550,
                "animationDurationUpdate": 750,
                "initialTreeDepth": 2  # Limit initial depth for better visibility
            }
        ]
    }

    return option

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
    [Output('data-table', 'rowData'),
     Output('all-data-store', 'data')],
    [Input('submit-button', 'n_clicks')],
    [State('from-dropdown', 'value'),
     State('to-dropdown', 'value'),
     State('unit-operation-dropdown', 'value'),
     State('attribute-dropdown', 'value')]
)
def update_table(n_clicks, from_val, to_val, unit_operation_val, attribute_val):
    # Only process if Submit button was clicked and at least one value is provided
    if not n_clicks or (not from_val and not to_val):
        return [], []  # Return empty list to keep table hidden if no submission
    
    try:
        # Prepare parameters for get_lineage function
        varTraceFor = None
        varTraceTarget = None
        
        if from_val:
            varTraceFor = "', '".join(from_val) if isinstance(from_val, list) else str(from_val)
        
        if to_val:
            varTraceTarget = "', '".join(to_val) if isinstance(from_val, list) else str(to_val)
        
        # Get lineage data from database
        outputType = "polars"  # "polars" or "duckdb"
        GenOrTrc = "all"  # "trc", "gen", or "all"
        level = -99  # -99 for all levels, 1 for first level, etc.
        
        # Fetch data with the specified output columns
        res = get_lineage(varTraceFor, varTraceTarget, outputType, GenOrTrc, level, 
                         outputcols="""type, root_parentlot, root_itemcode, product_parentlot as startnode, product_itemcode, ingredient_parentlot as endnode, ingredient_itemcode, level,
                                        root_unit_op_name as ParentName, product_unit_op_name as ProductName, ingredient_unit_op_name as IngredientName,
                                        root_description as ParentDescription, product_description as ProductDescription, ingredient_description as IngredientDescription
                                        """)
        
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
            
            # Apply additional filtering based on Unit Operation
            filtered_data = mapped_data
            if unit_operation_val:  # If Unit Operation values are selected
                filtered_data = [
                    row for row in mapped_data
                    if (row['ProductItemCode'] in unit_operation_val or row['IngredientItemCode'] in unit_operation_val)
                ]
            
            # For now, Attribute dropdown is empty, so no filtering based on attribute_val
            # If attribute_val is used in the future, add similar filtering logic here
            
            return filtered_data, mapped_data  # Return filtered data for table, original data for store
        else:
            print("No data returned from database")
            return [], []  # Return empty list to keep table hidden if no results
            
    except Exception as e:
        print(f"Error getting lineage data: {e}")
        return [], []  # Return empty list on error to keep table hidden

# Clientside callback to update filtered data whenever the filter changes
clientside_callback(
    """
    function(filterModel, rowData) {
        console.log('Filter model changed:', filterModel);
        console.log('Row data:', rowData);

        // If rowData is undefined, null, or empty, return no_update
        if (!rowData || rowData.length === 0) {
            console.log('No row data available, skipping filter processing');
            return window.dash_clientside.no_update;
        }

        // If no filters are applied, return all data
        if (!filterModel || Object.keys(filterModel).length === 0) {
            console.log('No filters applied, returning all data');
            return rowData;
        }

        // Apply filters manually in JavaScript
        let filteredData = rowData.filter(row => {
            let passesFilter = true;

            // Loop through each filter in the filterModel
            for (let column in filterModel) {
                if (!filterModel.hasOwnProperty(column)) continue;

                const filter = filterModel[column];
                const rowValue = row[column] != null ? row[column].toString() : '';

                // Handle "contains" filter type for text columns
                if (filter.type === 'contains') {
                    const filterValue = filter.filter != null ? filter.filter.toString().toLowerCase() : '';
                    if (!rowValue.toLowerCase().includes(filterValue)) {
                        passesFilter = false;
                        break;
                    }
                }
                // Handle "equals" filter type for numeric columns
                else if (filter.type === 'equals') {
                    const rowNum = parseFloat(rowValue);
                    const filterNum = parseFloat(filter.filter);
                    if (isNaN(rowNum) || rowNum !== filterNum) {
                        passesFilter = false;
                        break;
                    }
                }
            }

            return passesFilter;
        });

        console.log('Filtered data length:', filteredData.length);
        return filteredData;
    }
    """,
    Output('filtered-data-store', 'data'),
    [Input('data-table', 'filterModel')],
    [State('data-table', 'rowData')],
    prevent_initial_call=True
)

# Server-side callback for Export Genealogy (all data)
@app.callback(
    Output("download-all-data", "data"),
    [Input('export-genealogy-button', 'n_clicks')],
    [State('all-data-store', 'data')],
    prevent_initial_call=True
)
def export_all_data(n_clicks, all_data):
    if n_clicks and all_data:
        try:
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            
            # Return data for download using dict format
            return dict(content=df.to_csv(index=False), filename="genealogy_all_data.csv")
        except Exception as e:
            print(f"Export error: {e}")
            return dash.no_update
    return dash.no_update

# Server-side callback for Export with Required Data (filtered data)
@app.callback(
    Output("download-filtered-data", "data"),
    [Input('export-filtered-button', 'n_clicks')],
    [State('filtered-data-store', 'data')],
    prevent_initial_call=True
)
def export_filtered_data(n_clicks, filtered_data):
    if not n_clicks:  # Only proceed if the button was clicked
        return dash.no_update

    if filtered_data is not None and len(filtered_data) > 0:
        try:
            # Convert to DataFrame
            df = pd.DataFrame(filtered_data)
            
            print(f"Exporting {len(df)} filtered rows")
            
            # Return filtered data for download
            return dict(content=df.to_csv(index=False), filename="genealogy_filtered_data.csv")
        except Exception as e:
            print(f"Filtered export error: {e}")
            return dash.no_update
    else:
        print("No filtered data available")
        return dash.no_update

# Callback for Clear button
@app.callback(
    [Output('from-dropdown', 'value'),
     Output('to-dropdown', 'value'),
     Output('data-table', 'rowData', allow_duplicate=True),
     Output('all-data-store', 'data', allow_duplicate=True),
     Output('filtered-data-store', 'data', allow_duplicate=True),
     Output('unit-operation-dropdown', 'value'),
     Output('attribute-dropdown', 'value')],
    [Input('clear-button', 'n_clicks')],
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    if n_clicks:
        return None, None, [], [], [], None, None  # Reset everything to empty
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

# Clientside callback to download the ECharts tree chart as PNG
clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks || n_clicks <= 0) {
            console.log('Export visualization button not clicked, skipping');
            return window.dash_clientside.no_update;
        }

        console.log('Export visualization button clicked, attempting to download PNG');

        // Get the ECharts component DOM element
        const chartElement = document.getElementById('tree-chart');
        if (!chartElement) {
            console.error('Could not find tree-chart element');
            return window.dash_clientside.no_update;
        }

        // Get the ECharts instance
        const echartsInstance = window.echarts.getInstanceByDom(chartElement);
        if (!echartsInstance) {
            console.error('Could not find ECharts instance for tree-chart');
            return window.dash_clientside.no_update;
        }

        // Generate the PNG data URL
        const dataURL = echartsInstance.getDataURL({
            type: 'png',
            pixelRatio: 2,  // Increase resolution for better quality
            backgroundColor: '#fff'  // White background for the PNG
        });

        if (!dataURL) {
            console.error('Failed to generate PNG data URL');
            return window.dash_clientside.no_update;
        }

        // Create a temporary link element to trigger the download
        const link = document.createElement('a');
        link.href = dataURL;
        link.download = 'genealogy_tree.png';  // File name for the download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        console.log('PNG download triggered successfully');
        return window.dash_clientside.no_update;
    }
    """,
    Output('tree-chart', 'id'),  # Dummy output to satisfy Dash callback requirement
    [Input('export-visualization-button', 'n_clicks')],
    prevent_initial_call=True
)

if __name__ == '__main__':
    app.run(debug=True)
