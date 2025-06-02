Now in this dash app, Create hirearchical data structure using csv_to_hirearchy function -> use the json output to render echarts tree chart on visualization.
MY the csv_to_hierarchy function:
def csv_to_hierarchy(csv_data):
    # Dictionary to track nodes with their metadata
    node_info = {}
    
    # Track all relationships
    relationships = []
    
    # First pass: create all nodes with their descriptions
    for _, row in csv_data.iterrows():
        source = row['source']
        ingredient = row['ingredient']
        source_desc = row.get('source desc', '')
        ingredient_desc = row.get('ingredient description', '')
        
        
        # Get workforce and cost data (you'll need to add these columns to your CSV)
        # If columns don't exist, use default values
        source_workforce = row.get('source_workforce', 0)
        source_cost = row.get('source_cost', 0)
        ingredient_workforce = row.get('ingredient_workforce', 0)
        ingredient_cost = row.get('ingredient_cost', 0)
        
        # Add source if it doesn't exist
        if source not in node_info:
            node_info[source] = {
                "name": source,
                "description": source_desc,
                "references": [],  # Track which nodes reference this one
                "workforce": source_workforce,
                "Quantity": source_cost
            }
        
        # Add ingredient if it doesn't exist
        if ingredient not in node_info:
            node_info[ingredient] = {
                "name": ingredient, 
                "description": ingredient_desc,
                "references": [],  # Track which nodes reference this one
                "workforce": ingredient_workforce,
                "Quantity": ingredient_cost
            }
        
        # Track this relationship
        relationships.append((source, ingredient))
        # Add reference to the ingredient
        node_info[ingredient]["references"].append(source)
    
    # Find root nodes (nodes not used as ingredients)
    all_ingredients = set(csv_data['ingredient'].unique())
    all_sources = set(csv_data['source'].unique())
    root_candidates = all_sources - all_ingredients
    
    # Get or create a root node
    if not root_candidates:
        root_name = "Start"
        if root_name not in node_info:
            node_info[root_name] = {
                "name": root_name,
                "description": "Complete manufacturing workflow",
                "references": [],
                "workforce": 0,  # Default values
                "Quantity": 0
            }
        
        # Connect root to major nodes (nodes with multiple children)
        source_counts = csv_data['source'].value_counts()
        major_nodes = source_counts[source_counts > 1].index.tolist()
        
        for node in major_nodes or all_sources:
            relationships.append((root_name, node))
            node_info[node]["references"].append(root_name)
    elif len(root_candidates) > 1:
        # Multiple roots - create a virtual root
        root_name = "Manufacturing Process"
        if root_name not in node_info:
            node_info[root_name] = {
                "name": root_name,
                "description": "Complete manufacturing workflow",
                "references": [],
                "workforce": 0,  # Default values
                "Quantity": 0
            }
        
        for node in root_candidates:
            relationships.append((root_name, node))
            node_info[node]["references"].append(root_name)
    else:
        # Use the single root
        root_name = list(root_candidates)[0]
    
    # Build the tree with each node appearing every time it's referenced
    tree = {
        "name": node_info[root_name]["name"],
        "description": node_info[root_name]["description"],
        "children": [],
        "shared": False,
        "id": root_name,
        "workforce": node_info[root_name]["workforce"],
        "Quantity": node_info[root_name]["Quantity"]
    }
    
    # Build a map of parent -> children
    parent_to_children = {}
    for parent, child in relationships:
        if parent not in parent_to_children:
            parent_to_children[parent] = []
        parent_to_children[parent].append(child)
    
    # Helper function to recursively build the tree
    def build_tree(node_id, parent_node):
        if node_id in parent_to_children:
            for child_id in parent_to_children[node_id]:
                # Create the node every time it appears
                child_node = {
                    "name": node_info[child_id]["name"],
                    "description": node_info[child_id]["description"],
                    "children": [],
                    "shared": len(node_info[child_id]["references"]) > 1,
                    "id": child_id,
                    "workforce": node_info[child_id]["workforce"],
                    "Quantity": node_info[child_id]["Quantity"]
                }
                parent_node["children"].append(child_node)
                
                # Recursively add its children
                build_tree(child_id, child_node)
    
    # Start building from the root
    build_tree(root_name, tree)
    
    # print(tree)
   
    return tree

echarts example(this is the onw I want to use with the real json generated by csv_to_hierarchy function):
import * as echarts from 'echarts';
var ROOT_PATH = 'https://echarts.apache.org/examples';
var chartDom = document.getElementById('main');
var myChart = echarts.init(chartDom);
var option;
myChart.showLoading();
$.get(ROOT_PATH + '/data/asset/data/flare.json', function (data) {
  myChart.hideLoading();
  data.children.forEach(function (datum, index) {
    index % 2 === 0 && (datum.collapsed = true);
  });
  myChart.setOption(
    (option = {
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove'
      },
      series: [
        {
          type: 'tree',
          data: [data],
          top: '1%',
          left: '7%',
          bottom: '1%',
          right: '20%',
          symbolSize: 7,
          label: {
            position: 'left',
            verticalAlign: 'middle',
            align: 'right',
            fontSize: 9
          },
          leaves: {
            label: {
              position: 'right',
              verticalAlign: 'middle',
              align: 'left'
            }
          },
          emphasis: {
            focus: 'descendant'
          },
          expandAndCollapse: true,
          animationDuration: 550,
          animationDurationUpdate: 750
        }
      ]
    })
  );
});
option && myChart.setOption(option);

To this I want to use my real json

Traceback (most recent call last):
  File "/home/users/pr912591/Lineage/Lineage/app2.py", line 3, in <module>
    from dash_echarts import EChart  # Import EChart component
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'dash_echarts'
