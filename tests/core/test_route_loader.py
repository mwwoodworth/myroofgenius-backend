"""
Test the route loader mechanism
"""
import os
import sys
import pytest
from fastapi import FastAPI
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from routes.route_loader import load_all_routes

def test_route_loader_skips_archive_and_non_py():
    app = FastAPI()

    # Mock os.listdir to return a mix of files
    with patch('os.environ', {}), \
         patch('os.listdir') as mock_listdir, \
         patch('os.path.isdir') as mock_isdir, \
         patch('importlib.import_module') as mock_import:
        
        # Setup mock file system
        mock_listdir.return_value = ['valid_route.py', 'archive', '__init__.py', 'random.txt']
        
        def isdir_side_effect(path):
            return path.endswith('archive')
        mock_isdir.side_effect = isdir_side_effect
        
        # Mock valid route module
        mock_module = MagicMock()
        mock_router = MagicMock()
        mock_router.prefix = "/api/v1/valid"
        mock_module.router = mock_router
        mock_import.return_value = mock_module
        
        loaded, failed = load_all_routes(app)
        
        # Should only load valid_route.py
        assert loaded == 1
        assert failed == 0
        
        # Verify what was imported
        mock_import.assert_called_with("routes.valid_route")
        
        # Verify router inclusion
        # We can't easily check app.include_router without more complex mocking, 
        # but the counts tell us enough.

def test_route_loader_handles_exceptions_gracefully():
    app = FastAPI()

    with patch('os.environ', {}), \
         patch('os.listdir') as mock_listdir, \
         patch('os.path.isdir') as mock_isdir, \
         patch('importlib.import_module') as mock_import:
        
        mock_listdir.return_value = ['broken_route.py']
        mock_isdir.return_value = False
        
        # Simulate import error
        mock_import.side_effect = ImportError("Broken module")
        
        loaded, failed = load_all_routes(app)
        
        assert loaded == 0
        assert failed == 1
