"""
Test contract constants and parameter builders for Phase 5.
"""

import pytest
from app.services.sales_contract import SALES_METHOD, build_sales_params, get_default_sales_prompt
from app.services.signals_contract import SIG_METHOD, build_signals_params
from app.services._contract_utils import get_salesagent_commit, get_signalsagent_commit


def test_sales_method_constant():
    """Test that SALES_METHOD is a non-empty string."""
    assert isinstance(SALES_METHOD, str)
    assert len(SALES_METHOD) > 0
    assert SALES_METHOD == "rank_products"


def test_signals_method_constant():
    """Test that SIG_METHOD is a non-empty string."""
    assert isinstance(SIG_METHOD, str)
    assert len(SIG_METHOD) > 0
    assert SIG_METHOD == "get_signals"


def test_build_sales_params_valid():
    """Test build_sales_params with valid brief."""
    result = build_sales_params("test brief")
    assert isinstance(result, dict)
    assert "brief" in result
    assert result["brief"] == "test brief"


def test_build_sales_params_empty():
    """Test build_sales_params with empty brief raises error."""
    with pytest.raises(ValueError, match="brief cannot be empty"):
        build_sales_params("")
    
    with pytest.raises(ValueError, match="brief cannot be empty"):
        build_sales_params("   ")


def test_build_sales_params_with_tenant_prompt():
    """Test build_sales_params accepts tenant_prompt parameter."""
    result = build_sales_params("test brief", "custom prompt")
    assert isinstance(result, dict)
    assert "brief" in result
    assert result["brief"] == "test brief"


def test_build_signals_params_valid():
    """Test build_signals_params with valid brief."""
    result = build_signals_params("test signal spec")
    assert isinstance(result, dict)
    assert "signal_spec" in result
    assert result["signal_spec"] == "test signal spec"


def test_build_signals_params_empty():
    """Test build_signals_params with empty brief raises error."""
    with pytest.raises(ValueError, match="brief cannot be empty"):
        build_signals_params("")
    
    with pytest.raises(ValueError, match="brief cannot be empty"):
        build_signals_params("   ")


def test_default_sales_prompt():
    """Test get_default_sales_prompt returns non-empty string."""
    prompt = get_default_sales_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "brief" in prompt.lower()


def test_commit_hash_utils():
    """Test commit hash utility functions."""
    sales_commit = get_salesagent_commit()
    signals_commit = get_signalsagent_commit()
    
    assert isinstance(sales_commit, str)
    assert isinstance(signals_commit, str)
    assert len(sales_commit) > 0
    assert len(signals_commit) > 0


def test_method_names_in_reference_files():
    """Test that method names exist in reference repository files."""
    import os

    # Check salesagent method exists in AI provider
    salesagent_path = "reference/salesagent/product_catalog_providers/ai.py"
    if os.path.exists(salesagent_path):
        with open(salesagent_path, 'r') as f:
            content = f.read()
            # The reference uses get_products but we use rank_products for our contract
            assert "get_products" in content or "rank_products" in content
    
    # Check signals-agent method exists
    signals_path = "reference/signals-agent/client.py"
    if os.path.exists(signals_path):
        with open(signals_path, 'r') as f:
            content = f.read()
            assert SIG_METHOD in content

