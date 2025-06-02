import dash
from dash import dcc, html, Input, Output, callback, State, clientside_callback
import dash_ag_grid as dag
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
from Lineage import get_item_codes
from dash.exceptions import PreventUpdate
from Lineage import get_lineage

# Function to create a network visualization graph (currently using static data)
def create_network_graph():
    """Create a network visualization graph"""
    fig = go.Figure()
    
    # Placeholder for network visualization (can be updated later to use real data)
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
     State('to-dropdown', 'value')]
)
def update_table(n_clicks, from_val, to_val):
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
            
            return mapped_data, mapped_data  # Return same data for both table and store
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
                const rowValue = row[column] ? row[column].toString().toLowerCase() : '';
                const filterValue = filter.filter ? filter.filter.toLowerCase() : '';

                // Currently supporting "contains" filter type (as defined in columnDefs)
                if (filter.type === 'contains') {
                    if (!rowValue.includes(filterValue)) {
                        passesFilter = false;
                        break;
                    }
                }
                // Add support for "equals" filter type for numeric columns (e.g., Level, CntRecs)
                else if (filter.type === 'equals') {
                    const rowNum = parseFloat(rowValue);
                    const filterNum = parseFloat(filterValue);
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

# Clientside callback to trigger the server-side download callback
clientside_callback(
    """
    function(n_clicks, filteredData) {
        if (!n_clicks || n_clicks <= 0) {
            console.log('Export button not clicked, skipping');
            return window.dash_clientside.no_update;
        }

        if (!filteredData || filteredData.length === 0) {
            console.log('No filtered data available to export, skipping');
            return window.dash_clientside.no_update;
        }

        console.log('Export filtered button clicked, triggering download with', filteredData.length, 'rows');
        return n_clicks;
    }
    """,
    Output('filtered-data-store', 'modified_timestamp'),
    [Input('export-filtered-button', 'n_clicks'),
     State('filtered-data-store', 'data')],
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
    [Input('filtered-data-store', 'modified_timestamp')],
    [State('filtered-data-store', 'data')],
    prevent_initial_call=True
)
def export_filtered_data(timestamp, filtered_data):
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
     Output('filtered-data-store', 'data', allow_duplicate=True)],
    [Input('clear-button', 'n_clicks')],
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    if n_clicks:
        return None, None, [], [], []  # Reset everything to empty
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run(debug=True)
