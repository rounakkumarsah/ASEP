"""
ASEP — Production Benchmarking
"""

import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class Benchmarker:
    """Measures pipeline throughput and latency."""

    @staticmethod
    async def measure_throughput(task_func, num_tasks: int = 100, concurrency: int = 10) -> dict:
        """Measures tasks per second."""
        logger.info(f"Starting benchmark: {num_tasks} tasks with concurrency {concurrency}")
        
        start_time = time.time()
        
        sem = asyncio.Semaphore(concurrency)
        
        async def run_task():
            async with sem:
                await task_func()
                
        tasks = [asyncio.create_task(run_task()) for _ in range(num_tasks)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        tps = num_tasks / duration if duration > 0 else 0
        
        logger.info(f"Benchmark completed: {tps:.2f} TPS over {duration:.2f}s")
        return {
            "num_tasks": num_tasks,
            "duration_sec": duration,
            "throughput_tps": tps
        }
