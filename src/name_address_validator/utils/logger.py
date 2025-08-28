import streamlit as st
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class AppLogger:
    """Enterprise application logger with performance tracking"""
    
    def __init__(self, max_logs: int = 1000):
        self.logs: List[Dict] = []
        self.performance_metrics: List[Dict] = []
        self.max_logs = max_logs
        self.max_metrics = 500
        self.enabled = True
    
    def log(self, message: str, category: str = "GENERAL", level: str = "INFO", **kwargs):
        """Log a message with metadata"""
        if not self.enabled:
            return
        
        log_entry = {
            'timestamp': datetime.now(),
            'level': level.upper(),
            'category': category.upper(),
            'message': message,
            'metadata': kwargs
        }
        
        self.logs.append(log_entry)
        
        # Maintain log size
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Console output for debugging
        timestamp_str = log_entry['timestamp'].strftime("%H:%M:%S")
        print(f"[{timestamp_str}] {level.upper()} {category}: {message}")
    
    def info(self, message: str, category: str = "GENERAL", **kwargs):
        """Log info message"""
        self.log(message, category, "INFO", **kwargs)
    
    def warning(self, message: str, category: str = "GENERAL", **kwargs):
        """Log warning message"""
        self.log(message, category, "WARNING", **kwargs)
    
    def error(self, message: str, category: str = "GENERAL", **kwargs):
        """Log error message"""
        self.log(message, category, "ERROR", **kwargs)
    
    def debug(self, message: str, category: str = "GENERAL", **kwargs):
        """Log debug message"""
        self.log(message, category, "DEBUG", **kwargs)
    
    def track_performance(self, operation: str, duration_ms: int, success: bool = True, **metadata):
        """Track performance metric"""
        metric = {
            'timestamp': datetime.now(),
            'operation': operation,
            'duration_ms': duration_ms,
            'success': success,
            'metadata': metadata
        }
        
        self.performance_metrics.append(metric)
        
        # Maintain metrics size
        if len(self.performance_metrics) > self.max_metrics:
            self.performance_metrics = self.performance_metrics[-self.max_metrics:]
        
        self.log(f"Performance: {operation} completed in {duration_ms}ms ({'success' if success else 'failure'})", 
                "PERFORMANCE", "DEBUG")
    
    def get_logs_by_level(self, level: str) -> List[Dict]:
        """Get logs by level"""
        return [log for log in self.logs if log['level'] == level.upper()]
    
    def get_logs_by_category(self, category: str) -> List[Dict]:
        """Get logs by category"""
        return [log for log in self.logs if log['category'] == category.upper()]
    
    def get_recent_logs(self, minutes: int = 5) -> List[Dict]:
        """Get recent logs"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [log for log in self.logs if log['timestamp'] > cutoff_time]
    
    def get_error_summary(self) -> Dict:
        """Get summary of recent errors"""
        errors = self.get_logs_by_level("ERROR")
        warnings = self.get_logs_by_level("WARNING")
        
        return {
            'error_count': len(errors),
            'warning_count': len(warnings),
            'recent_errors': errors[-5:],  # Last 5 errors
            'recent_warnings': warnings[-5:]  # Last 5 warnings
        }
    
    def export_logs(self, format: str = "json") -> str:
        """Export logs in specified format"""
        if format.lower() == "json":
            return json.dumps([
                {
                    'timestamp': log['timestamp'].isoformat(),
                    'level': log['level'],
                    'category': log['category'],
                    'message': log['message'],
                    'metadata': log.get('metadata', {})
                }
                for log in self.logs
            ], indent=2)
        
        elif format.lower() == "csv":
            import io
            import csv
            
            output = io.StringIO()
            if self.logs:
                writer = csv.writer(output)
                writer.writerow(['timestamp', 'level', 'category', 'message', 'metadata'])
                
                for log in self.logs:
                    writer.writerow([
                        log['timestamp'].isoformat(),
                        log['level'],
                        log['category'],
                        log['message'],
                        json.dumps(log.get('metadata', {}))
                    ])
            
            return output.getvalue()
        
        else:
            # Plain text format
            lines = []
            for log in self.logs:
                timestamp = log['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                line = f"[{timestamp}] {log['level']} {log['category']}: {log['message']}"
                if log.get('metadata'):
                    line += f" | {json.dumps(log['metadata'])}"
                lines.append(line)
            return '\n'.join(lines)
    
    def clear(self):
        """Clear all logs and metrics"""
        self.logs = []
        self.performance_metrics = []
        self.log("Logger cleared", "SYSTEM", "INFO")
    
    def disable(self):
        """Disable logging"""
        self.enabled = False
    
    def enable(self):
        """Enable logging"""
        self.enabled = True
        self.log("Logger enabled", "SYSTEM", "INFO")


# Global logger instance for easy import
app_logger = AppLogger()