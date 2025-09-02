"""Debug logging service for capturing and forwarding debug information to the frontend."""

import logging
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading

@dataclass
class DebugLogEntry:
    """Represents a single debug log entry."""
    timestamp: str
    level: str
    message: str
    category: str
    data: Optional[Dict[str, Any]] = None
    tenant_id: Optional[int] = None
    brief: Optional[str] = None

class DebugLogCapture:
    """Captures debug logs and makes them available for frontend consumption."""
    
    def __init__(self):
        self.logs: List[DebugLogEntry] = []
        self.current_session: Optional[str] = None
        self.current_brief: Optional[str] = None
        self.current_tenant_id: Optional[int] = None
        self.lock = threading.Lock()
        
        # Set up custom log handlers
        self.setup_log_handlers()
    
    def setup_log_handlers(self):
        """Set up custom log handlers to capture debug information."""
        # Create a custom handler for our debug logger
        self.handler = DebugLogHandler(self)
        
        # Get the loggers we want to capture
        loggers_to_capture = [
            'rag_operations',
            'app.services.product_rag',
            'app.services.mcp_rpc_handlers',
            'app.services.web_context_google',
            'app.services.ai_client',
            'app.utils.env',
            'app.services.orchestrator',
            'app.services._orchestrator_agents'
        ]
        
        for logger_name in loggers_to_capture:
            logger = logging.getLogger(logger_name)
            logger.addHandler(self.handler)
            logger.setLevel(logging.INFO)
    
    def start_session(self, brief: str, tenant_id: Optional[int] = None):
        """Start a new debug logging session."""
        with self.lock:
            self.current_session = f"session_{int(time.time())}"
            self.current_brief = brief
            self.current_tenant_id = tenant_id
            self.logs.clear()
            self.log(f"🔍 Debug session started for brief: '{brief}'", "info", "session")
    
    def log(self, message: str, level: str = "info", category: str = "general", 
            data: Optional[Dict[str, Any]] = None):
        """Log a debug message."""
        with self.lock:
            entry = DebugLogEntry(
                timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                level=level,
                message=message,
                category=category,
                data=data,
                tenant_id=self.current_tenant_id,
                brief=self.current_brief
            )
            self.logs.append(entry)
    
    def get_logs(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get captured logs, optionally filtered by category."""
        with self.lock:
            if category:
                filtered_logs = [log for log in self.logs if log.category == category]
            else:
                filtered_logs = self.logs
            
            return [asdict(log) for log in filtered_logs]
    
    def get_formatted_logs(self) -> List[str]:
        """Get logs formatted for display."""
        with self.lock:
            formatted = []
            for log in self.logs:
                # Format based on category and content
                if log.category == "rag_search":
                    formatted.append(f"🔍 {log.message}")
                elif log.category == "web_grounding":
                    formatted.append(f"🌐 {log.message}")
                elif log.category == "ai_ranking":
                    formatted.append(f"🤖 {log.message}")
                elif log.category == "strategy":
                    formatted.append(f"🎯 {log.message}")
                elif log.category == "results":
                    formatted.append(f"📊 {log.message}")
                else:
                    formatted.append(log.message)
            return formatted
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the debug session."""
        with self.lock:
            categories = {}
            for log in self.logs:
                cat = log.category
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
            
            return {
                "session_id": self.current_session,
                "brief": self.current_brief,
                "tenant_id": self.current_tenant_id,
                "total_logs": len(self.logs),
                "categories": categories,
                "start_time": self.logs[0].timestamp if self.logs else None,
                "end_time": self.logs[-1].timestamp if self.logs else None
            }

class DebugLogHandler(logging.Handler):
    """Custom log handler that captures debug information."""
    
    def __init__(self, capture: DebugLogCapture):
        super().__init__()
        self.capture = capture
    
    def emit(self, record):
        """Emit a log record."""
        try:
            # Determine category based on logger name and message content
            category = self.determine_category(record)
            
            # Extract additional data if available
            data = self.extract_data(record)
            
            # Log to our capture system
            self.capture.log(record.getMessage(), record.levelname.lower(), category, data)
            
        except Exception:
            # Don't let logging errors break the system
            pass
    
    def determine_category(self, record) -> str:
        """Determine the category of a log message."""
        message = record.getMessage()
        logger_name = record.name
        
        if "RAG SEARCH STARTED" in message:
            return "rag_search"
        elif "Strategy:" in message:
            return "strategy"
        elif "Query Expansion:" in message:
            return "strategy"
        elif "SEMANTIC SEARCH" in message:
            return "rag_search"
        elif "FTS SEARCH" in message:
            return "rag_search"
        elif "SEARCH RESULTS SUMMARY" in message:
            return "results"
        elif "TOP RESULTS" in message:
            return "results"
        elif "WEB_DEBUG:" in message:
            return "web_grounding"
        elif "AI_DEBUG:" in message:
            return "ai_ranking"
        elif "RAG_DEBUG:" in message:
            return "rag_search"
        elif "Processing product" in message:
            return "web_grounding"
        elif "snippet:" in message:
            return "web_grounding"
        elif "Web grounding per product successful" in message:
            return "web_grounding"
        elif "AI ranking completed" in message:
            return "ai_ranking"
        elif "RAG SEARCH COMPLETED" in message:
            return "rag_search"
        elif "rag_operations" in logger_name:
            return "rag_search"
        elif "product_rag" in logger_name:
            return "rag_search"
        elif "web_context" in logger_name:
            return "web_grounding"
        elif "ai_client" in logger_name:
            return "ai_ranking"
        elif "mcp_rpc_handlers" in logger_name:
            return "mcp_handling"
        else:
            return "general"
    
    def extract_data(self, record) -> Optional[Dict[str, Any]]:
        """Extract additional data from the log record."""
        data = {}
        
        # Extract any extra fields from the record
        if hasattr(record, 'tenant_id'):
            data['tenant_id'] = record.tenant_id
        if hasattr(record, 'brief'):
            data['brief'] = record.brief
        if hasattr(record, 'product_id'):
            data['product_id'] = record.product_id
        if hasattr(record, 'strategy'):
            data['strategy'] = record.strategy
        
        return data if data else None

# Global debug capture instance
debug_capture = DebugLogCapture()

def get_debug_capture() -> DebugLogCapture:
    """Get the global debug capture instance."""
    return debug_capture

def start_debug_session(brief: str, tenant_id: Optional[int] = None):
    """Start a new debug session."""
    debug_capture.start_session(brief, tenant_id)

def log_debug(message: str, level: str = "info", category: str = "general", 
              data: Optional[Dict[str, Any]] = None):
    """Log a debug message."""
    debug_capture.log(message, level, category, data)

def get_debug_logs(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get captured debug logs."""
    return debug_capture.get_logs(category)

def get_formatted_debug_logs() -> List[str]:
    """Get formatted debug logs for display."""
    return debug_capture.get_formatted_logs()

def get_debug_summary() -> Dict[str, Any]:
    """Get debug session summary."""
    return debug_capture.get_summary()

