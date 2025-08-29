"""Unit tests for preflight metrics functions."""

import pytest
from unittest.mock import patch, MagicMock


def test_tenant_prompt_metrics():
    """Test tenant prompt metrics calculation."""
    from app.routes.preflight.metrics import get_tenant_prompt_metrics
    
    mock_session = MagicMock()
    
    # Mock table info query - custom_prompt column exists
    mock_table_info = MagicMock()
    mock_table_info.fetchall.return_value = [
        (0, "id", "INTEGER", 0, None, 0),
        (1, "name", "TEXT", 0, None, 0),
        (2, "custom_prompt", "TEXT", 0, None, 0),
    ]
    
    # Mock count queries
    mock_custom_count = MagicMock()
    mock_custom_count.scalar.return_value = 3
    
    mock_total_count = MagicMock()
    mock_total_count.scalar.return_value = 10
    
    mock_session.execute.side_effect = [
        mock_table_info,  # PRAGMA table_info
        mock_custom_count,  # COUNT with custom prompt
        mock_total_count,   # COUNT total
    ]
    
    with_custom, using_default = get_tenant_prompt_metrics(mock_session)
    
    assert with_custom == 3
    assert using_default == 7


def test_tenant_prompt_metrics_no_column():
    """Test tenant prompt metrics when custom_prompt column doesn't exist."""
    from app.routes.preflight.metrics import get_tenant_prompt_metrics
    
    mock_session = MagicMock()
    
    # Mock table info query - custom_prompt column missing
    mock_table_info = MagicMock()
    mock_table_info.fetchall.return_value = [
        (0, "id", "INTEGER", 0, None, 0),
        (1, "name", "TEXT", 0, None, 0),
    ]
    
    mock_session.execute.return_value = mock_table_info
    
    with_custom, using_default = get_tenant_prompt_metrics(mock_session)
    
    assert with_custom == 0
    assert using_default == 0


def test_preflight_overall_status_calculation():
    """Test overall preflight status calculation."""
    from app.routes.preflight.endpoints import get_preflight_data
    
    with patch('app.routes.preflight.endpoints.check_paths') as mock_check_paths, \
         patch('app.routes.preflight.endpoints.get_reference_data') as mock_get_ref, \
         patch('app.routes.preflight.endpoints.check_external_agents_schema') as mock_check_schema, \
         patch('app.routes.preflight.endpoints.get_agent_metrics') as mock_get_agents, \
         patch('app.routes.preflight.endpoints.get_tenant_count') as mock_get_tenants, \
         patch('app.routes.preflight.endpoints.get_tenant_prompt_metrics') as mock_get_prompts:
        
        # Mock all checks to return True/success
        mock_check_paths.return_value = {
            "data_dir_exists": True,
            "db_file_exists": True,
            "db_writeable": True,
            "mcp_routes_mounted": True
        }
        mock_get_ref.return_value = {"present": True}
        mock_check_schema.return_value = (True, True)
        mock_get_agents.return_value = {"enabled_sales": {}, "enabled_signals": {}}
        mock_get_tenants.return_value = 5
        mock_get_prompts.return_value = (2, 3)
        
        data = get_preflight_data(None)  # Pass None to avoid DB dependency
        
        # When no session is provided, has_agent_type and has_protocol are False
        # So the overall status will be False
        assert data["ok"] is False


def test_preflight_overall_status_failure():
    """Test overall preflight status when some checks fail."""
    from app.routes.preflight.endpoints import get_preflight_data
    
    with patch('app.routes.preflight.endpoints.check_paths') as mock_check_paths, \
         patch('app.routes.preflight.endpoints.get_reference_data') as mock_get_ref, \
         patch('app.routes.preflight.endpoints.check_external_agents_schema') as mock_check_schema:
        
        # Mock some checks to return False/failure
        mock_check_paths.return_value = {
            "data_dir_exists": True,
            "db_file_exists": True,
            "db_writeable": False,  # This fails
            "mcp_routes_mounted": True
        }
        mock_get_ref.return_value = {"present": True}
        mock_check_schema.return_value = (True, True)
        
        data = get_preflight_data()
        
        # Should be ok when all checks pass
        assert data["ok"] is False
