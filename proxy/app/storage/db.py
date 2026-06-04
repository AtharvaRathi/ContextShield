"""
Database Management.
Handles simple local storage for telemetry and token savings metrics.
Uses a thread-safe in-memory state for fast proxy routing.
"""
import threading
from collections import deque
from datetime import datetime

class MetricsDatabase:
    """Logs and retrieves token usage and savings metrics in a thread-safe manner."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.total_original_chars = 0
        self.total_optimized_chars = 0
        self.requests_processed = 0
        
        # Maintain a rolling window of the last 20 intercepts
        self.recent_history = deque(maxlen=20)
        self.lock = threading.Lock()
        
    def log_request(self, original_chars: int, optimized_chars: int):
        """Records character/token savings for a request."""
        with self.lock:
            self.total_original_chars += original_chars
            self.total_optimized_chars += optimized_chars
            self.requests_processed += 1
            
            # Record individual request details
            timestamp = datetime.now().strftime("%H:%M:%S")
            savings_pct = 0
            if original_chars > 0:
                savings_pct = round(((original_chars - optimized_chars) / original_chars) * 100, 1)
                
            self.recent_history.appendleft({
                "id": self.requests_processed,
                "time": timestamp,
                "original": original_chars,
                "optimized": optimized_chars,
                "saved_pct": savings_pct
            })
            
    def get_savings_stats(self) -> dict:
        """Retrieves aggregated token savings statistics."""
        with self.lock:
            # Estimate roughly 4 characters per token
            original_tokens = self.total_original_chars // 4
            optimized_tokens = self.total_optimized_chars // 4
            saved_tokens = original_tokens - optimized_tokens
            
            # Estimate generic cloud pricing of ~$2.00 per 1M tokens ($0.002 per 1k)
            money_saved = (max(0, saved_tokens) / 1000) * 0.002
            
            return {
                "original_tokens": original_tokens,
                "optimized_tokens": optimized_tokens,
                "money_saved": round(money_saved, 4),
                "requests_processed": self.requests_processed,
                "total_saved_tokens": saved_tokens,
                "recent_history": list(self.recent_history)
            }

# Global thread-safe instance
metrics_db = MetricsDatabase()
