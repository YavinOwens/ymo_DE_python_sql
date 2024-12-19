from dash import html, dcc, dash_table, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import dash
from utils.data_loader import DataLoader
import logging
import json
import os

data_loader = DataLoader()

def initialize_master_config():
    """Initialize the master config with default rule templates if it doesn't exist."""
    default_config = {
        'gdpr_rules': [
            {
                'name': 'Email Format Check',
                'description': 'Validates email format',
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'category': 'GDPR',
                'severity': 'High',
                'active': True
            }
        ],
        'data_quality_rules': [
            {
                'name': 'Not Null Check',
                'description': 'Ensures the field is not null',
                'pattern': 'NOT NULL',
                'category': 'Data Quality',
                'severity': 'High',
                'active': True
            }
        ],
        'validation_rules': [
            {
                'name': 'Date Format Check',
                'description': 'Validates date format',
                'pattern': 'YYYY-MM-DD',
                'category': 'Format',
                'severity': 'Medium',
                'active': True
            }
        ]
    }
    
    # Save default config to rule_templates.json if it doesn't exist
    rule_templates_path = 'BONUS/assets/data/rule_templates.json'
    os.makedirs(os.path.dirname(rule_templates_path), exist_ok=True)
    if not os.path.exists(rule_templates_path):
        with open(rule_templates_path, 'w') as f:
            json.dump(default_config, f, indent=4)
            
    return default_config

def layout():
    """Creates the main content for the Rule Management page with list view."""
    try:
        # Load rule templates from rule_templates.json
        rule_templates_path = 'BONUS/assets/data/rule_templates.json'
        
        if not os.path.exists(rule_templates_path):
            master_config = initialize_master_config()
        else:
            with open(rule_templates_path, 'r') as f:
                master_config = json.load(f)
        
        # Combine all rule types into a single list for display
        all_rules = []
        
        # Add rules from each category
        categories = ['gdpr_rules', 'data_quality_rules', 'validation_rules', 'business_rules', 'table_level_rules']
        for category in categories:
            rules = master_config.get(category, [])
            for rule in rules:
                rule['type'] = category.replace('_rules', '').replace('_', ' ').title()
                all_rules.append(rule)
        
        if not all_rules:
            return html.Div([
                html.H2("Rule Management", className="mb-4"),
                dbc.Alert(
                    "No rule templates found. Click 'Add New Rule' to create your first rule.",
                    color="info",
                    className="mb-3"
                ),
                dbc.Button(
                    [html.I(className="bi bi-plus-lg me-2"), "Add New Rule"],
                    id="add-rule-btn",
                    color="primary"
                )
            ])
        
        # Calculate stats
        total_rules = len(all_rules)
        active_rules = sum(1 for rule in all_rules if rule.get('active', True))
        critical_rules = sum(1 for rule in all_rules if rule.get('severity', '').lower() == 'critical')
        
        # Create rule items
        rule_items = []
        for i, rule in enumerate(all_rules):
            rule_item = html.Div([
                # Rule header with name and status
                html.Div([
                    html.Div([
                        html.H5(rule['name'], className="mb-0"),
                        html.Small(rule['type'], className="text-muted ms-2")
                    ], className="d-flex align-items-center"),
                    html.Div([
                        dbc.Badge(
                            "Active" if rule.get('active', True) else "Inactive",
                            color="success" if rule.get('active', True) else "danger",
                            className="me-2"
                        ),
                        dbc.Badge(
                            rule.get('severity', 'Medium'),
                            color="warning",
                            className="me-2"
                        ),
                        dbc.Switch(
                            id={'type': 'rule-toggle', 'index': i},
                            value=rule.get('active', True),
                            className="d-inline-block"
                        )
                    ])
                ], className="d-flex justify-content-between align-items-center mb-2"),
                
                # Rule description and details
                html.P(rule['description'], className="mb-2 text-muted"),
                html.Div([
                    html.Code(rule.get('pattern', 'N/A'), className="me-3"),
                    html.Small(f"Category: {rule.get('category', 'N/A')}", className="text-muted")
                ], className="mb-2"),
                
                # Rule actions
                html.Div([
                    dbc.Button(
                        "Edit",
                        id={'type': 'edit-rule-btn', 'index': i},
                        color="secondary",
                        size="sm",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Delete",
                        id={'type': 'delete-rule-btn', 'index': i},
                        color="danger",
                        size="sm"
                    )
                ], className="rule-actions")
            ], className="rule-list-item")
            rule_items.append(rule_item)

        return html.Div([
            # Header with stats and controls
            html.Div([
                html.Div([
                    html.H2("Rule Management", className="mb-0"),
                    html.Div([
                        html.Span(f"{total_rules} Rules", className="text-muted me-3"),
                        html.Span(f"{active_rules} Active", className="text-success me-3"),
                        html.Span(f"{critical_rules} Critical", className="text-danger")
                    ], className="rule-stats-inline")
                ]),
                dbc.Button(
                    [html.I(className="bi bi-plus-lg me-2"), "Add New Rule"],
                    id="add-rule-btn",
                    color="primary"
                )
            ], className="page-header d-flex justify-content-between align-items-center"),
            
            # Filter controls
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button("All Rules", id="filter-all", color="primary", active=True),
                    dbc.Button("Active", id="filter-active", color="primary", outline=True),
                    dbc.Button("Inactive", id="filter-inactive", color="primary", outline=True)
                ]),
                dbc.Input(
                    type="text",
                    placeholder="Search rules...",
                    id="rule-search",
                    className="ms-3",
                    style={"width": "300px"}
                )
            ], className="filter-controls mb-4"),
            
            # Rules list
            html.Div(rule_items, className="rule-list"),
            
            # Edit Rule Modal
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Edit Rule")),
                dbc.ModalBody([
                    dbc.Form([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Rule Name"),
                                dbc.Input(id="edit-rule-name", type="text", className="mb-3")
                            ])
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Description"),
                                dbc.Textarea(id="edit-rule-description", className="mb-3")
                            ])
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Category"),
                                dbc.Select(
                                    id="edit-rule-category",
                                    options=[
                                        {"label": "Data Quality", "value": "data_quality_rules"},
                                        {"label": "GDPR", "value": "gdpr_rules"},
                                        {"label": "Validation", "value": "validation_rules"},
                                        {"label": "Business", "value": "business_rules"},
                                        {"label": "Table Level", "value": "table_level_rules"}
                                    ],
                                    className="mb-3"
                                )
                            ])
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Severity"),
                                dbc.Select(
                                    id="edit-rule-severity",
                                    options=[
                                        {"label": "Low", "value": "low"},
                                        {"label": "Medium", "value": "medium"},
                                        {"label": "High", "value": "high"},
                                        {"label": "Critical", "value": "critical"}
                                    ],
                                    className="mb-3"
                                )
                            ])
                        ])
                    ])
                ]),
                dbc.ModalFooter([
                    dbc.Button("Cancel", id="edit-rule-cancel", className="me-2"),
                    dbc.Button("Save", id="edit-rule-save", color="primary")
                ])
            ], id="edit-rule-modal", is_open=False)
        ])
    except Exception as e:
        logging.error(f"Error in rule_management layout: {str(e)}")
        return html.Div([
            html.H2("Rule Management", className="mb-4"),
            dbc.Alert(
                [
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error loading rule management: {str(e)}"
                ],
                color="danger",
                className="error-state"
            )
        ])

# Callbacks for rule management functionality
def register_callbacks(app):
    @app.callback(
        Output("rule-management-content", "children"),
        [Input("filter-all", "n_clicks"),
         Input("filter-active", "n_clicks"),
         Input("filter-inactive", "n_clicks"),
         Input("rule-search", "value")]
    )
    def filter_rules(all_clicks, active_clicks, inactive_clicks, search_value):
        """Filter rules based on active status and search term."""
        ctx = dash.callback_context
        if not ctx.triggered:
            return layout()
        
        try:
            # Load rules
            rule_templates_path = 'BONUS/assets/data/rule_templates.json'
            with open(rule_templates_path, 'r') as f:
                master_config = json.load(f)
            
            # Combine all rule types into a single list
            all_rules = []
            categories = ['gdpr_rules', 'data_quality_rules', 'validation_rules', 'business_rules', 'table_level_rules']
            for category in categories:
                rules = master_config.get(category, [])
                for rule in rules:
                    rule['type'] = category.replace('_rules', '').replace('_', ' ').title()
                    all_rules.append(rule)
            
            # Apply filters
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            # Filter by status
            if button_id == "filter-active":
                filtered_rules = [rule for rule in all_rules if rule.get('active', True)]
            elif button_id == "filter-inactive":
                filtered_rules = [rule for rule in all_rules if not rule.get('active', True)]
            else:
                filtered_rules = all_rules
            
            # Apply search filter if provided
            if search_value:
                search_term = search_value.lower()
                filtered_rules = [
                    rule for rule in filtered_rules
                    if search_term in rule['name'].lower() or
                       search_term in rule['description'].lower() or
                       search_term in rule.get('category', '').lower() or
                       search_term in rule.get('type', '').lower()
                ]
            
            return layout()  # Re-render with filtered rules
        except Exception as e:
            logging.error(f"Error in filter_rules: {str(e)}")
            return html.Div([
                html.H2("Rule Management", className="mb-4"),
                dbc.Alert(
                    [
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                        f"Error filtering rules: {str(e)}"
                    ],
                    color="danger",
                    className="error-state"
                )
            ]) 