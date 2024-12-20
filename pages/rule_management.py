from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import dash
import logging

logger = logging.getLogger(__name__)
data_loader = DataLoader()

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Rule Management", className="mb-4"),
            
            # Category selector
            dbc.Row([
                dbc.Col([
                    html.Label("Select Rule Category:"),
                    dcc.Dropdown(
                        id='rule-category-dropdown',
                        options=[
                            {'label': cat.replace('_', ' ').title(), 'value': cat}
                            for cat in data_loader.get_rule_categories()
                        ],
                        value=data_loader.get_rule_categories()[0] if data_loader.get_rule_categories() else None,
                        className="mb-3"
                    )
                ])
            ]),
            
            # Rules table
            dash_table.DataTable(
                id='rules-table',
                columns=[
                    {'name': 'Rule ID', 'id': 'id'},
                    {'name': 'Name', 'id': 'name'},
                    {'name': 'Description', 'id': 'description'},
                    {'name': 'Severity', 'id': 'severity'},
                    {'name': 'Status', 'id': 'active'}
                ],
                data=[],
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            ),
            
            # Refresh button
            dbc.Button(
                "Refresh Rules",
                id="refresh-rules-button",
                color="primary",
                className="mt-3"
            )
        ])
    ])
])

# Callback to update rules table based on category selection
@dash.callback(
    Output('rules-table', 'data'),
    [Input('rule-category-dropdown', 'value'),
     Input('refresh-rules-button', 'n_clicks')]
)
def update_rules_table(category, n_clicks):
    if not category:
        return []
    
    try:
        # Get all rules
        rules = data_loader.get_rules()
        
        # Filter rules by matching the category from the dropdown
        filtered_rules = []
        for rule in rules:
            # For table specific rules, check if the rule is in any of the table rule lists
            if category == 'table_specific_rules':
                if rule.get('type') in ['Table Specific', 'Data Quality', 'Format', 'Business Logic']:
                    filtered_rules.append(rule)
            # For other categories, match the category name
            elif category.replace('_rules', '') in [
                rule.get('category', '').lower(),
                rule.get('type', '').lower().replace(' ', '_')
            ]:
                filtered_rules.append(rule)
        
        # Transform the rules data for display
        table_data = [{
            'id': rule['id'],
            'name': rule['name'],
            'description': rule['description'],
            'severity': rule['severity'],
            'active': 'Active' if rule.get('active', False) else 'Inactive'
        } for rule in filtered_rules]
        
        logger.debug(f"Found {len(table_data)} rules for category {category}")
        return table_data
    except Exception as e:
        logger.error(f"Error updating rules table: {str(e)}")
        return [] 