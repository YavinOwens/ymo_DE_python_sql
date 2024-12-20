from dash import Input, Output, State, callback_context, callback
import logging

logger = logging.getLogger(__name__)

@callback(
    [Output('column-selector', 'options', allow_duplicate=True),
     Output('column-selector', 'value', allow_duplicate=True)],
    [Input('table-selector', 'value')],
    prevent_initial_call=True
)
def update_column_selector(table_name):
    """Update column selector options and value based on table selection."""
    ctx = callback_context
    if not table_name:
        return [], None
    try:
        columns = data_loader.get_table_columns(table_name)
        options = [{'label': col, 'value': col} for col in columns]
        
        # For column analysis page, allow multiple selection
        if ctx.triggered_id and 'column-analysis' in ctx.triggered_id:
            return options, []
        # For quality page, single selection
        return options, None
        
    except Exception as e:
        logger.error(f"Error getting columns for table {table_name}: {str(e)}")
        return [], None 