"""Unit tests for preflight metrics and status calculation."""

import pytest
from unittest.mock import patch, MagicMock


def test_tenant_prompt_metrics():
    """Test tenant prompt metrics calculation."""
    from app.routes.preflight import _get_tenant_prompt_metrics
    
    mock_session = MagicMock()
    
    # Mock PRAGMA table_info result showing custom_prompt column exists
    mock_pragma_result = MagicMock()
    mock_pragma_result.fetchall.return_value = [
        (0, "id", "INTEGER", 0, None, 0),
        (1, "slug", "TEXT", 0, None, 0),
        (2, "custom_prompt", "TEXT", 0, None, 0),
    ]
    
    # Mock count queries
    mock_count_with_prompt = MagicMock()
    mock_count_with_prompt.scalar.return_value = 2
    
    mock_count_total = MagicMock()
    mock_count_total.scalar.return_value = 5
    
    mock_session.execute.side_effect = [
        mock_pragma_result,
        mock_count_with_prompt,
        mock_count_total
    ]
    
    with_custom, using_default = _get_tenant_prompt_metrics(mock_session)
    
    assert with_custom == 2
    assert using_default == 3


def test_tenant_prompt_metrics_no_column():
    """Test tenant prompt metrics when custom_prompt column doesn't exist."""
    from app.routes.preflight import _get_tenant_prompt_metrics
    
    mock_session = MagicMock()
    
    # Mock PRAGMA table_info result showing custom_prompt column doesn't exist
    mock_pragma_result = MagicMock()
    mock_pragma_result.fetchall.return_value = [
        (0, "id", "INTEGER", 0, None, 0),
        (1, "slug", "TEXT", 0, None, 0),
    ]
    
    mock_session.execute.return_value = mock_pragma_result
    
    with_custom, using_default = _get_tenant_prompt_metrics(mock_session)
    
    assert with_custom == 0
    assert using_default == 0


def test_preflight_overall_status_calculation():
    """Test preflight overall status calculation."""
    from app.routes.preflight import _get_preflight_data
    
    mock_session = MagicMock()
    
    # Mock all the helper functions
    with patch('app.routes.preflight._check_db_writeable', return_value=(True, "")):
        with patch('app.routes.preflight._check_mcp_routes_mounted', return_value=True):
            with patch('app.routes.preflight._check_external_agents_schema', return_value=(True, True)):
                with patch('app.routes.preflight._get_tenant_prompt_metrics', return_value=(0, 1)):
                    with patch('app.routes.preflight.list_tenants', return_value=([MagicMock()], 1)):
                        with patch('app.routes.preflight.list_external_agents', return_value=[]):
                            with patch('app.routes.preflight.get_salesagent_commit', return_value="abc1234"):
                                with patch('app.routes.preflight.get_signalsagent_commit', return_value="def5678"):
                                    with patch('os.path.exists', return_value=True):
                                        data = _get_preflight_data(mock_session)
                                        
                                        # Should be ok when all checks pass
                                        assert data["ok"] is True


def test_preflight_overall_status_failure():
    """Test preflight overall status when checks fail."""
    from app.routes.preflight import _get_preflight_data
    
    mock_session = MagicMock()
    
    # Mock helper functions to simulate failures
    with patch('app.routes.preflight._check_db_writeable', return_value=(False, "DB error")):
        with patch('app.routes.preflight._check_mcp_routes_mounted', return_value=True):
            with patch('app.routes.preflight._check_external_agents_schema', return_value=(True, True)):
                with patch('app.routes.preflight._get_tenant_prompt_metrics', return_value=(0, 1)):
                    with patch('app.routes.preflight.list_tenants', return_value=([MagicMock()], 1)):
                        with patch('app.routes.preflight.list_external_agents', return_value=[]):
                            with patch('app.routes.preflight.get_salesagent_commit', return_value="abc1234"):
                                with patch('app.routes.preflight.get_signalsagent_commit', return_value="def5678"):
                                    with patch('os.path.exists', return_value=True):
                                        data = _get_preflight_data(mock_session)
                                        
                                        # Should not be ok when db_writeable fails
                                        assert data["ok"] is False
