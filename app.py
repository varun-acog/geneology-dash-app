import dash
from dash import dcc, html, Input, Output, callback, State, clientside_callback
from dash_echarts import DashECharts
import dash_ag_grid as dag
import pandas as pd
from Lineage import get_item_codes, get_lineage
from dash.exceptions import PreventUpdate
from dotenv import load_dotenv

load_dotenv()

# Function to create a level-based hierarchy for ECharts visualization
def csv_to_hierarchy_by_level(csv_data):
    """Create a level-based hierarchy where ProductPN at level N has IngredientPN children,
    and those IngredientPNs become ProductPNs at level N+1"""
    node_info = {}
    relationships = []
    
    # Collect unique nodes and their information
    for _, row in csv_data.iterrows():
        root_pn = row['root']
        root_itemcode = row.get('root_itemcode', '')
        product_pn = row['source']
        ingredient_pn = row['ingredient']
        level = row.get('level', 0)
        root_desc = row.get('root desc', '')
        source_desc = row.get('source desc', '')
        ingredient_desc = row.get('ingredient description', '')
        
        # Add root node (level 0)
        if root_pn not in node_info:
            node_info[root_pn] = {
                "name": root_itemcode if root_itemcode else root_pn,
                "description": root_desc,
                "level": 0,
                "type": "root"
            }
        
        # Add product node
        if product_pn not in node_info:
            node_info[product_pn] = {
                "name": product_pn,
                "description": source_desc,
                "level": level,
                "type": "product"
            }
        else:
            node_info[product_pn]["level"] = min(node_info[product_pn]["level"], level)
        
        # Add ingredient node
        if ingredient_pn not in node_info:
            node_info[ingredient_pn] = {
                "name": ingredient_pn,
                "description": ingredient_desc,
                "level": level + 1,
                "type": "ingredient"
            }
        else:
            node_info[ingredient_pn]["level"] = min(node_info[ingredient_pn]["level"], level + 1)
        
        relationships.append((product_pn, ingredient_pn, level))
    
    # Find root nodes
    all_children = set(child for parent, child, level in relationships)
    root_candidates = [node for node in node_info.keys() if node not in all_children or node_info[node]["type"] == "root"]
    
    if len(root_candidates) == 1:
        root_node = root_candidates[0]
    else:
        root_node = "Manufacturing Process"
        node_info[root_node] = {
            "name": root_node,
            "description": "Manufacturing Process Root",
            "level": -1,
            "type": "virtual_root"
        }
        for node, info in node_info.items():
            if info["level"] == 0:
                relationships.append((root_node, node, -1))
    
    # Build parent-to-children mapping
    parent_to_children = {}
    for parent, child, level in relationships:
        if parent not in parent_to_children:
            parent_to_children[parent] = []
        parent_to_children[parent].append(child)
    
    # Recursive function to build tree
    def build_tree_node(node_id, visited=None):
        if visited is None:
            visited = set()
        if node_id in visited:
            return None
        visited.add(node_id)
        
        node_data = {
            "name": node_info[node_id]["name"],
            "description": node_info[node_id]["description"],
            "children": [],
            "id": node_id,
            "level": node_info[node_id]["level"],
            "type": node_info[node_id]["type"]
        }
        
        if node_id in parent_to_children:
            for child_id in parent_to_children[node_id]:
                child_node = build_tree_node(child_id, visited.copy())
                if child_node:
                    node_data["children"].append(child_node)
        
        return node_data
    
    return build_tree_node(root_node)

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
        'marginBottom': '10px'
    },
    'sectionTitle': {
        'fontSize': '14px',
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
        'verticalAlign': 'top'
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
        'color': '#000000',
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
    "headerStyle": {"backgroundColor": "#2c3e50", "color": "#ffffff", "fontWeight": "600", "fontSize": "14px"}
}

# Define the layout
app.layout = html.Div([
    dcc.Download(id="download-all-data"),
    dcc.Download(id="download-filtered-data"),
    dcc.Store(id="all-data-store"),
    dcc.Store(id="filtered-data-store"),
    html.Div([
        html.Div([
            html.H1("Genealogy App", style=styles['headerText'])
        ], style=styles['header']),
        html.Div([
            html.Div([
                html.H4("Filters", style=styles['sectionTitle']),
                html.Div([
                    dcc.Dropdown(
                        id='item-codes-dropdown',
                        multi=True,
                        clearable=False,
                        placeholder='Select Item Codes',
                        style=styles['dropdown']
                    )
                ], style={'marginBottom': '15px'}),
                html.Div([
                    dcc.RadioItems(
                        id='gen-trc-radio',
                        options=[
                            {'label': 'Genealogy', 'value': 'gen'},
                            {'label': 'Traceability', 'value': 'trc'}
                        ],
                        value=None,
                        labelStyle={**styles['checkboxLabel'], 'margin': '5px'},
                        inputStyle=styles['checkbox']
                    )
                ], style={'marginBottom': '15px'}),
                html.Div([
                    html.Button("Submit", id="submit-button", style=styles['exportButton']),
                    html.Button("Clear", id="clear-button", style=styles['clearButton'])
                ], style={'textAlign': 'right', 'marginBottom': '10px'}),
            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '20px'}),
            html.Div([
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
                            options=[]
                        )
                    ])
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
            ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style=styles['section']),
        html.Div([
            html.Div([
                html.H4("Visualization", style=styles['sectionTitle']),
                html.Div([
                    html.Button("Export", id="export-visualization-button", style=styles['exportButton'], disabled=True)
                ], style={'textAlign': 'right', 'marginBottom': '10px'}),
                dcc.Loading(
                    id="loading-tree-chart",
                    type="default",
                    children=[
                        DashECharts(
                            id='tree-chart',
                            option={},
                            style={'height': '500px', 'border': '1px solid #ecf0f1', 'borderRadius': '4px'}
                        )
                    ]
                )
            ])
        ], style=styles['section']),
        html.Div([
            html.Div([
                html.H4("Data", style=styles['sectionTitle']),
                dcc.Loading(
                    id="loading-data-table",
                    type="default",
                    children=[
                        dag.AgGrid(
                            id='data-table',
                            columnDefs=columnDefs,
                            rowData=[],
                            defaultColDef=defaultColDef,
                            style={'height': '400px', 'width': '100%'},
                            dashGridOptions={
                                "pagination": True,
                                "paginationPageSize": 20,
                                "suppressExcelExport": False,
                                "suppressCsvExport": False,
                            },
                            className="ag-theme-alpine",
                            enableEnterpriseModules=False
                        )
                    ]
                )
            ], style={'width': '70%', 'display': 'inline-block', 'paddingRight': '20px'}),
            html.Div([
                html.Div([
                    html.Button("Export Genealogy", id="export-genealogy-button", style={**styles['primaryButton'], 'marginBottom': '10px'}),
                    html.Button("Export with Required Data", id="export-filtered-button", style=styles['primaryButton'])
                ])
            ], style={'width': '25%', 'display': 'inline-block', 'verticalAlign': 'top'})
        ], style=styles['section'])
    ], style=styles['container'])
])

# Callback to populate Unit Operation dropdown with ProductItemCode-ProductName and IngredientItemCode-IngredientName
@app.callback(
    Output('unit-operation-dropdown', 'options'),
    Input('all-data-store', 'data'),
    prevent_initial_call=True
)
def update_unit_operation_options(data):
    if not data:
        return []
    
    df = pd.DataFrame(data)
    product_map = {}
    ingredient_map = {}
    
    # Map product item codes to names
    for _, row in df[['ProductItemCode', 'ProductName']].dropna(subset=['ProductItemCode']).iterrows():
        code = str(row['ProductItemCode'])
        name = str(row['ProductName']) if pd.notnull(row['ProductName']) else 'Unknown'
        if code not in product_map:
            product_map[code] = name
    
    # Map ingredient item codes to names
    for _, row in df[['IngredientItemCode', 'IngredientName']].dropna(subset=['IngredientItemCode']).iterrows():
        code = str(row['IngredientItemCode'])
        name = str(row['IngredientName']) if pd.notnull(row['IngredientName']) else 'Unknown'
        if code not in ingredient_map:
            ingredient_map[code] = name
    
    # Create dropdown options
    options = []
    for code, name in product_map.items():
        options.append({'label': f"{code}-{name}", 'value': code})
    for code, name in ingredient_map.items():
        if code not in product_map:
            options.append({'label': f"{code}-{name}", 'value': code})
    
    return sorted(options, key=lambda x: x['label'])

# Callback to generate hierarchical data and update ECharts tree chart
@app.callback(
    Output('tree-chart', 'option'),
    Input('all-data-store', 'data'),
    prevent_initial_call=True
)
def update_tree_chart(data):
    if not data:
        print("No data provided to tree chart")
        return {}

    df = pd.DataFrame(data)
    filtered_df = df[
        ~df['ProductPN'].str.upper().str.startswith(('Z', 'B', 'M'), na=False) &
        ~df['IngredientPN'].str.upper().str.startswith(('Z', 'B', 'M'), na=False)
    ]
    
    hierarchy_data = pd.DataFrame({
        'root': filtered_df['ParentPN'],
        'root_itemcode': filtered_df['ParentItemCode'],
        'source': filtered_df['ProductPN'],
        'ingredient': filtered_df['IngredientPN'],
        'root desc': filtered_df['ParentName'],
        'source desc': filtered_df['ProductName'],
        'ingredient description': filtered_df['IngredientName'],
        'level': filtered_df['Level'],
    }).dropna(subset=['root', 'source', 'ingredient'])

    if hierarchy_data.empty:
        print("Hierarchy data is empty")
        return {}

    tree_data = csv_to_hierarchy_by_level(hierarchy_data)
    if not tree_data:
        print("No tree data generated")
        return {}
    
    return {
        "tooltip": {
            "trigger": "item",
            "triggerOn": "mousemove",
            "formatter": """
                function(params) {
                    var data = params.data;
                    return data.name + '<br/>' +
                           'Level: ' + data.level + '<br/>' +
                           'Type: ' + data.type + '<br/>' +
                           (data.description ? 'Description: ' + data.description : '');
                }
            """
        },
        "series": [
            {
                "type": "tree",
                "data": [tree_data],
                "top": "5%",
                "left": "7%",
                "bottom": "5%",
                "right": "20%",
                "symbolSize": 8,
                "label": {
                    "position": "left",
                    "verticalAlign": "middle",
                    "align": "right",
                    "fontSize": 10
                },
                "leaves": {
                    "label": {
                        "position": "right",
                        "verticalAlign": "middle",
                        "align": "left",
                        "fontSize": 10
                    }
                },
                "emphasis": {
                    "focus": "descendant"
                },
                "expandAndCollapse": True,
                "animationDuration": 550,
                "animationDurationUpdate": 750,
                "initialTreeDepth": 3,
                "layout": "orthogonal",
                "orient": "LR",
                "lineStyle": {
                    "curveness": 0.5,
                    "width": 2
                },
                "itemStyle": {
                    "color": "#3498db",
                    "borderColor": "#2c3e50",
                    "borderWidth": 1
                }
            }
        ]
    }

# Callback to enable/disable export visualization button
@app.callback(
    Output('export-visualization-button', 'disabled'),
    Input('tree-chart', 'option'),
    prevent_initial_call=True
)
def enable_export_button(chart_option):
    return not bool(chart_option)  # Enable button if chart_option is non-empty

# Callback to populate item-codes-dropdown
@app.callback(
    Output("item-codes-dropdown", "options"),
    Input("item-codes-dropdown", "search_value"),
    State("item-codes-dropdown", "value")
)
def update_item_codes_options(search_value, value):
    if not search_value:
        raise PreventUpdate
    return get_item_codes(search_value)

# Callback for interactive filtering
@app.callback(
    [
        Output('data-table', 'rowData'),
        Output('all-data-store', 'data'),
        Output('data-table', 'filterModel')
    ],
    [Input('submit-button', 'n_clicks')],
    [
        State('item-codes-dropdown', 'value'),
        State('unit-operation-dropdown', 'value'),
        State('attribute-dropdown', 'value'),
        State('gen-trc-radio', 'value')
    ],
    prevent_initial_call=True
)
def update_table(n_clicks, item_codes_val, unit_operation_val, attribute_val, gen_trc_val):
    if not n_clicks or not item_codes_val:
        return [], [], {}
    
    try:
        varTraceFor = None
        varTraceTarget = None
        
        if item_codes_val:
            varTraceFor = ", ".join(item_codes_val) if isinstance(item_codes_val, list) else str(item_codes_val)
            varTraceTarget = None
        
        GenOrTrc = gen_trc_val if gen_trc_val else "all"
        outputType = "polars"
        level = -99
        
        res = get_lineage(
            varTraceFor,
            varTraceTarget,
            outputType,
            GenOrTrc,
            level,
            outputcols="""type, root_parentlot, root_itemcode, product_parentlot as startnode, product_itemcode, ingredient_parentlot as endnode, ingredient_itemcode, level,
                          root_unit_op_name as ParentName, product_unit_op_name as ProductName, ingredient_unit_op_name as IngredientName,
                          root_description as ParentDescription, product_description as ProductDescription, ingredient_description as IngredientDescription,
                          COUNT(*) as CntRecs""",
        )
        
        print("Database result:", res)
        print("Columns:", res.columns if hasattr(res, 'columns') else 'No columns attribute')
        
        if res is not None and len(res) > 0:
            if hasattr(res, 'to_pandas'):
                df_result = res.to_pandas()
            else:
                df_result = res
            
            mapped_data = []
            for _, row in df_result.iterrows():
                mapped_data.append({
                    'ParentItemCode': row.get('root_itemcode', ''),
                    'ParentName': row.get('ParentDescription', ''),
                    'ParentPN': row.get('root_parentlot', ''),
                    'Level': row.get('Level', ''),
                    'ProductItemCode': row.get('product_itemcode', ''),
                    'ProductName': row.get('ProductDescription', ''),
                    'ProductPN': row.get('startnode', ''),
                    'IngredientItemCode': row.get('ingredient_itemcode', ''),
                    'IngredientName': row.get('IngredientDescription', ''),
                    'IngredientPN': row.get('endnode', ''),
                    'CntRecs': row.get('CntRecs', 0),
                })
            
            filtered_data = mapped_data
            if unit_operation_val:
                filtered_data = [
                    row for row in mapped_data
                    if (row['ProductItemCode'] in unit_operation_val or row['IngredientItemCode'] in unit_operation_val)
                ]
            
            return filtered_data, mapped_data, {}
        else:
            print("No data returned from database")
            return [], [], {}
            
    except Exception as e:
        print(f"Error getting lineage data: {e}")
        return [], [], {}

# Clientside callback to update filtered data
clientside_callback(
    """
    function(filterModel, rowData) {
        console.log('Filter model changed:', filterModel);
        console.log('Row data:', rowData);

        if (!rowData || rowData.length === 0) {
            console.log('No row data available, skipping filter processing');
            return window.dash_clientside.no_update;
        }

        if (!filterModel || Object.keys(filterModel).length === 0) {
            console.log('No filters applied, returning all data');
            return rowData;
        }

        let filteredData = rowData.filter(row => {
            let passesFilter = true;

            for (let column in filterModel) {
                if (!filterModel.hasOwnProperty(column)) continue;

                const filter = filterModel[column];
                const rowValue = row[column] != null ? row[column].toString() : '';

                if (filter.type === 'contains') {
                    const filterValue = filter.filter != null ? filter.filter.toString().toLowerCase() : '';
                    if (!rowValue.toLowerCase().includes(filterValue)) {
                        passesFilter = false;
                        break;
                    }
                }
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

# Clientside callback to download ECharts tree chart as PNG
clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks || n_clicks <= 0) {
            console.log('Export visualization button not clicked, skipping');
            return window.dash_clientside.no_update;
        }

        console.log('Export visualization button clicked, attempting to download PNG');

        // Check if ECharts is available
        if (!window.echarts) {
            console.error('ECharts library not loaded');
            return window.dash_clientside.no_update;
        }

        const chartElement = document.getElementById('tree-chart');
        if (!chartElement) {
            console.error('Could not find tree-chart element');
            return window.dash_clientside.no_update;
        }

        // Add a small delay to ensure chart is initialized
        return new Promise((resolve) => {
            setTimeout(() => {
                const echartsInstance = window.echarts.getInstanceByDom(chartElement);
                if (!echartsInstance) {
                    console.error('Could not find ECharts instance for tree-chart');
                    resolve(window.dash_clientside.no_update);
                    return;
                }

                const dataURL = echartsInstance.getDataURL({
                    type: 'png',
                    pixelRatio: 2,
                    backgroundColor: '#fff'
                });

                if (!dataURL) {
                    console.error('Failed to generate PNG data URL');
                    resolve(window.dash_clientside.no_update);
                    return;
                }

                const link = document.createElement('a');
                link.href = dataURL;
                link.download = 'genealogy_tree.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                console.log('PNG download triggered successfully');
                resolve(window.dash_clientside.no_update);
            }, 500); // 500ms delay to ensure chart is ready
        });
    }
    """,
    Output('tree-chart', 'id'),
    [Input('export-visualization-button', 'n_clicks')],
    prevent_initial_call=True
)

# Server-side callback for Export Genealogy
@app.callback(
    Output("download-all-data", "data"),
    [Input('export-genealogy-button', 'n_clicks')],
    [State('all-data-store', 'data')],
    prevent_initial_call=True
)
def export_all_data(n_clicks, all_data):
    if n_clicks and all_data:
        try:
            df = pd.DataFrame(all_data)
            return dict(content=df.to_csv(index=False), filename="genealogy_all_data.csv")
        except Exception as e:
            print(f"Export error: {e}")
            return dash.no_update
    return dash.no_update

# Server-side callback for Export with Required Data
@app.callback(
    Output("download-filtered-data", "data"),
    [Input('export-filtered-button', 'n_clicks')],
    [State('filtered-data-store', 'data')],
    prevent_initial_call=True
)
def export_filtered_data(n_clicks, filtered_data):
    if not n_clicks:
        return dash.no_update

    if filtered_data is not None and len(filtered_data) > 0:
        try:
            df = pd.DataFrame(filtered_data)
            print(f"Exporting {len(df)} filtered rows")
            return dict(content=df.to_csv(index=False), filename="genealogy_filtered_data.csv")
        except Exception as e:
            print(f"Filtered export error: {e}")
            return dash.no_update
    else:
        print("No filtered data available")
        return dash.no_update

# Callback for Clear button
@app.callback(
    [
        Output('item-codes-dropdown', 'value'),
        Output('data-table', 'rowData', allow_duplicate=True),
        Output('all-data-store', 'data', allow_duplicate=True),
        Output('filtered-data-store', 'data', allow_duplicate=True),
        Output('unit-operation-dropdown', 'value'),
        Output('attribute-dropdown', 'value'),
        Output('gen-trc-radio', 'value')
    ],
    [Input('clear-button', 'n_clicks')],
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    if n_clicks:
        return None, [], [], [], None, None, None
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run(debug=True, port=8051)
