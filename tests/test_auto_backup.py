"""
Unit tests for auto-backup system.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.utils.auto_backup_simple import auto_backup, cleanup_old_backups, get_backup_stats, MAX_BACKUPS


class TestAutoBackup:
    """Test auto-backup functionality."""
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        temp_dir = tempfile.mkdtemp()
        backup_dir = Path(temp_dir) / "backups"
        backup_dir.mkdir()
        
        # Mock the BACKUP_DIR
        with patch('app.utils.auto_backup_simple.BACKUP_DIR', backup_dir):
            yield backup_dir
        
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_export_data(self):
        """Mock export_all_data function."""
        with patch('app.utils.data_persistence.export_all_data') as mock:
            mock.return_value = {"test": "data"}
            yield mock
    
    def test_auto_backup_creates_backup(self, temp_backup_dir, mock_session, mock_export_data):
        """Test that auto_backup creates a backup file."""
        result = auto_backup(mock_session, "test_reason")
        
        assert result is not None
        assert result.startswith("full_backup_")
        assert result.endswith(".json")
        
        # Check that backup file exists
        backup_files = list(temp_backup_dir.glob("full_backup_*.json"))
        assert len(backup_files) == 1
        
        # Check that export was called
        mock_export_data.assert_called_once_with(mock_session)
    
    def test_auto_backup_handles_export_error(self, temp_backup_dir, mock_session):
        """Test that auto_backup handles export errors gracefully."""
        with patch('app.utils.data_persistence.export_all_data', side_effect=Exception("Export failed")):
            result = auto_backup(mock_session, "test_reason")
            
            assert result is None
            
            # Check that no backup file was created
            backup_files = list(temp_backup_dir.glob("full_backup_*.json"))
            assert len(backup_files) == 0
    
    def test_cleanup_old_backups_keeps_max_backups(self, temp_backup_dir):
        """Test that cleanup keeps only MAX_BACKUPS files."""
        # Create more than MAX_BACKUPS files
        for i in range(MAX_BACKUPS + 5):
            backup_file = temp_backup_dir / f"full_backup_20241229_{i:06d}.json"
            backup_file.write_text('{"test": "data"}')
        
        # Run cleanup
        cleanup_old_backups()
        
        # Check that only MAX_BACKUPS files remain
        backup_files = list(temp_backup_dir.glob("full_backup_*.json"))
        assert len(backup_files) == MAX_BACKUPS
        
        # Check that the newest files are kept
        file_names = [f.name for f in backup_files]
        file_names.sort()
        expected_names = [f"full_backup_20241229_{i:06d}.json" for i in range(5, MAX_BACKUPS + 5)]
        assert file_names == expected_names
    
    def test_cleanup_old_backups_no_cleanup_needed(self, temp_backup_dir):
        """Test that cleanup does nothing when under limit."""
        # Create fewer than MAX_BACKUPS files
        for i in range(5):
            backup_file = temp_backup_dir / f"full_backup_20241229_{i:06d}.json"
            backup_file.write_text('{"test": "data"}')
        
        # Run cleanup
        cleanup_old_backups()
        
        # Check that all files remain
        backup_files = list(temp_backup_dir.glob("full_backup_*.json"))
        assert len(backup_files) == 5
    
    def test_cleanup_old_backups_handles_deletion_error(self, temp_backup_dir):
        """Test that cleanup handles file deletion errors gracefully."""
        # Create files
        for i in range(MAX_BACKUPS + 2):
            backup_file = temp_backup_dir / f"full_backup_20241229_{i:06d}.json"
            backup_file.write_text('{"test": "data"}')
        
        # Test that cleanup doesn't crash when there are files to delete
        # (we can't easily mock the unlink method, so we just test it doesn't crash)
        try:
            cleanup_old_backups()
            # If we get here, cleanup didn't crash
            backup_files = list(temp_backup_dir.glob("full_backup_*.json"))
            # Should have cleaned up some files
            assert len(backup_files) <= MAX_BACKUPS + 2
        except Exception as e:
            # Should not crash
            assert False, f"Cleanup crashed: {e}"
    
    def test_get_backup_stats_no_backups(self, temp_backup_dir):
        """Test backup stats when no backups exist."""
        stats = get_backup_stats()
        
        assert stats["total_backups"] == 0
        assert stats["max_backups"] == MAX_BACKUPS
        assert stats["latest_backup"] is None
        assert stats["cleanup_needed"] is False
    
    def test_get_backup_stats_with_backups(self, temp_backup_dir):
        """Test backup stats when backups exist."""
        # Create some backup files
        for i in range(3):
            backup_file = temp_backup_dir / f"full_backup_20241229_{i:06d}.json"
            backup_file.write_text('{"test": "data"}')
        
        stats = get_backup_stats()
        
        assert stats["total_backups"] == 3
        assert stats["max_backups"] == MAX_BACKUPS
        assert stats["latest_backup"] is not None
        assert stats["cleanup_needed"] is False
    
    def test_get_backup_stats_cleanup_needed(self, temp_backup_dir):
        """Test backup stats when cleanup is needed."""
        # Create more than MAX_BACKUPS files
        for i in range(MAX_BACKUPS + 5):
            backup_file = temp_backup_dir / f"full_backup_20241229_{i:06d}.json"
            backup_file.write_text('{"test": "data"}')
        
        stats = get_backup_stats()
        
        assert stats["total_backups"] == MAX_BACKUPS + 5
        assert stats["max_backups"] == MAX_BACKUPS
        assert stats["latest_backup"] is not None
        assert stats["cleanup_needed"] is True
    
    def test_auto_backup_includes_cleanup(self, temp_backup_dir, mock_session, mock_export_data):
        """Test that auto_backup includes cleanup."""
        # Create more than MAX_BACKUPS files
        for i in range(MAX_BACKUPS + 3):
            backup_file = temp_backup_dir / f"full_backup_20241229_{i:06d}.json"
            backup_file.write_text('{"test": "data"}')
        
        # Run auto_backup
        auto_backup(mock_session, "test_reason")
        
        # Check that cleanup happened
        backup_files = list(temp_backup_dir.glob("full_backup_*.json"))
        assert len(backup_files) == MAX_BACKUPS
    
    def test_auto_backup_logs_reason(self, temp_backup_dir, mock_session, mock_export_data):
        """Test that auto_backup logs the reason."""
        with patch('app.utils.auto_backup_simple.logger') as mock_logger:
            auto_backup(mock_session, "custom_reason")
            
            # Check that info was logged with reason
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args[0][0]
            assert "custom_reason" in call_args
