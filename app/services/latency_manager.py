from typing import List
import logging

logger = logging.getLogger("app.services.latency_manager")

class LatencyManager:
    def __init__(self):
        self.history: List[float] = []
        self.threshold_ms: float = 2000.0
        
    def record_latency(self, latency_ms: float):
        self.history.append(latency_ms)
        if len(self.history) > 20:
            self.history.pop(0)
            
    def get_average(self) -> float:
        if not self.history:
            return 0.0
        return sum(self.history) / len(self.history)
        
    def optimize_required(self) -> bool:
        avg = self.get_average()
        if avg > self.threshold_ms:
            logger.warning(f"Latency threshold exceeded (Avg: {avg}ms). Optimization required.")
            return True
        return False
        
    def adapt_quality(self) -> str:
        if self.optimize_required():
            return "low_latency_mode"
        return "high_quality_mode"
