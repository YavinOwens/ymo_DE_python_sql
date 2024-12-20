from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
from utils.data_loader import DataLoader
import dash
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
data_loader = DataLoader()

layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Configured Rules", className="mb-4"),
            
            # Tab selection
            dbc.Tabs([
                dbc.Tab(label="Configured Rules", tab_id="configured-rules"),
                dbc.Tab(label="Rule Templates", tab_id="rule-templates"),
            ], id="tabs", active_tab="configured-rules"),
            
            # Content div that will be updated based on tab selection
            html.Div(id="tab-content")
        ])
    ])
], fluid=True)

# Callback to update content based on tab selection
@dash.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "configured-rules":
        return html.Div([
            # Refresh button
            dbc.Button(
                "Refresh",
                id="refresh-configured-rules",
                color="primary",
                className="mb-3"
            ),
            
            # Configured rules table
            dash_table.DataTable(
                id='configured-rules-table',
                columns=[
                    {'name': 'R', 'id': 'rule_id'},
                    {'name': 'N', 'id': 'rule_name'},
                    {'name': 'Description', 'id': 'description'},
                    {'name': 'T', 'id': 'table_name'},
                    {'name': 'C', 'id': 'column_name'},
                    {'name': 'Validation Code', 'id': 'validation_code'},
                    {'name': 'L', 'id': 'last_updated'},
                    {'name': 'S', 'id': 'status'}
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
                    'fontWeight': 'bold',
                    'textAlign': 'left',
                    'padding': '10px'
                },
                style_cell_conditional=[
                    {'if': {'column_id': 'rule_id'}, 'width': '5%'},
                    {'if': {'column_id': 'rule_name'}, 'width': '5%'},
                    {'if': {'column_id': 'description'}, 'width': '25%'},
                    {'if': {'column_id': 'table_name'}, 'width': '5%'},
                    {'if': {'column_id': 'column_name'}, 'width': '5%'},
                    {'if': {'column_id': 'validation_code'}, 'width': '40%'},
                    {'if': {'column_id': 'last_updated'}, 'width': '5%'},
                    {'if': {'column_id': 'status'}, 'width': '10%'}
                ],
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '14px'
                },
                page_size=10,
                style_table={'overflowX': 'auto'}
            ),
            
            # Status message
            html.Div(id="configured-rules-status", 
                    className="mt-3",
                    style={'color': 'green'})
        ])
    
    elif active_tab == "rule-templates":
        return html.Div([
            # Rule templates table
            dash_table.DataTable(
                id='rule-templates-table',
                columns=[
                    {'name': 'ID', 'id': 'id'},
                    {'name': 'Name', 'id': 'name'},
                    {'name': 'Description', 'id': 'description'},
                    {'name': 'Category', 'id': 'category'},
                    {'name': 'Type', 'id': 'type'},
                    {'name': 'Severity', 'id': 'severity'},
                    {'name': 'Validation Code', 'id': 'validation_code'},
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
                    'fontWeight': 'bold',
                    'textAlign': 'left',
                    'padding': '10px'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'fontSize': '14px'
                },
                page_size=15,
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                style_table={'overflowX': 'auto'}
            )
        ])

# Add callback to populate rule templates table
@dash.callback(
    Output('rule-templates-table', 'data'),
    Input('tabs', 'active_tab')
)
def update_rule_templates(active_tab):
    if active_tab != "rule-templates":
        return []
    
    try:
        all_rules = data_loader.get_rules()
        template_data = []
        
        for category, rules in all_rules.items():
            if isinstance(rules, list):
                for rule in rules:
                    template_data.append({
                        'id': rule['id'],
                        'name': rule['name'],
                        'description': rule['description'],
                        'category': category.replace('_rules', '').title(),
                        'type': rule.get('type', ''),
                        'severity': rule.get('severity', ''),
                        'validation_code': rule.get('validation_code', ''),
                        'active': 'Active' if rule.get('active', False) else 'Inactive'
                    })
            elif isinstance(rules, dict):
                for table_name, table_rules in rules.items():
                    for rule in table_rules:
                        template_data.append({
                            'id': rule['id'],
                            'name': rule['name'],
                            'description': rule['description'],
                            'category': table_name.replace('_rules', '').title(),
                            'type': rule.get('type', ''),
                            'severity': rule.get('severity', ''),
                            'validation_code': rule.get('validation_code', ''),
                            'active': 'Active' if rule.get('active', False) else 'Inactive'
                        })
        
        return template_data
    except Exception as e:
        logger.error(f"Error loading rule templates: {str(e)}")
        return []