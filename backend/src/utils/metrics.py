import time
import os
import psutil
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class MetricsStore:
    request_count: int = 0
    request_latency_sum: float = 0.0
    error_count: int = 0
    agent_executions: int = 0
    
    # Store request paths count/latencies
    path_counts: Dict[str, int] = field(default_factory=dict)
    path_latencies: Dict[str, float] = field(default_factory=dict)

    def record_request(self, path: str, latency: float, status_code: int) -> None:
        self.request_count += 1
        self.request_latency_sum += latency
        self.path_counts[path] = self.path_counts.get(path, 0) + 1
        self.path_latencies[path] = self.path_latencies.get(path, 0.0) + latency
        
        if status_code >= 500:
            self.error_count += 1

    def record_agent_execution(self) -> None:
        self.agent_executions += 1

    def get_system_metrics(self) -> Dict[str, Any]:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return {
            "process_memory_rss_bytes": mem_info.rss,
            "process_memory_vms_bytes": mem_info.vms,
            "process_cpu_percent": process.cpu_percent(),
        }

metrics_store = MetricsStore()
