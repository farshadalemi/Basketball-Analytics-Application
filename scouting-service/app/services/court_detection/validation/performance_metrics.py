"""
Performance benchmarking tools for basketball court detection validation.

This module provides comprehensive performance metrics including processing time,
memory usage, CPU utilization, and throughput measurements.
"""

import time
import psutil
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
import threading
import gc

logger = logging.getLogger(__name__)

@dataclass
class PerformanceResult:
    """Container for performance measurement results."""
    method_name: str
    processing_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    peak_memory_mb: float
    throughput_fps: float
    frame_count: int
    success_rate: float
    additional_metrics: Dict[str, float] = field(default_factory=dict)

class PerformanceBenchmark:
    """
    Comprehensive performance benchmarking tools for court detection validation.
    
    This class provides detailed performance analysis including timing,
    memory usage, CPU utilization, and system resource monitoring.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize performance benchmark.
        
        Args:
            config: Configuration dictionary with benchmark parameters
        """
        self.config = config or {}
        
        # Benchmark settings
        self.sample_interval = self.config.get('sample_interval', 0.1)  # seconds
        self.memory_tracking = self.config.get('memory_tracking', True)
        self.cpu_tracking = self.config.get('cpu_tracking', True)
        
        # Performance tracking
        self.benchmark_history = []
        self.current_benchmark = None
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # System baseline
        self.baseline_memory = psutil.virtual_memory().used / (1024**2)  # MB
        self.baseline_cpu = psutil.cpu_percent(interval=1)
        
        logger.info("PerformanceBenchmark initialized successfully")
    
    def benchmark_method(self, method_func: Callable, method_name: str, 
                        test_data: List[Any], *args, **kwargs) -> PerformanceResult:
        """
        Benchmark a detection method with comprehensive performance metrics.
        
        Args:
            method_func: Method to benchmark
            method_name: Name of the method
            test_data: List of test frames/data
            *args, **kwargs: Additional arguments for the method
            
        Returns:
            PerformanceResult with comprehensive metrics
        """
        try:
            logger.info(f"Starting benchmark for method: {method_name}")
            
            # Initialize monitoring
            self._start_monitoring()
            
            # Performance tracking variables
            processing_times = []
            memory_samples = []
            cpu_samples = []
            successful_detections = 0
            
            start_time = time.perf_counter()
            
            # Process test data
            for i, test_frame in enumerate(test_data):
                try:
                    # Measure processing time for this frame
                    frame_start = time.perf_counter()
                    result = method_func(test_frame, *args, **kwargs)
                    frame_end = time.perf_counter()
                    
                    frame_time_ms = (frame_end - frame_start) * 1000
                    processing_times.append(frame_time_ms)
                    
                    # Check if detection was successful
                    if self._is_detection_successful(result):
                        successful_detections += 1
                    
                    # Sample system resources periodically
                    if i % 10 == 0:  # Sample every 10 frames
                        memory_samples.append(psutil.virtual_memory().used / (1024**2))
                        cpu_samples.append(psutil.cpu_percent())
                    
                except Exception as e:
                    logger.error(f"Error processing frame {i} in benchmark: {str(e)}")
                    processing_times.append(0.0)
            
            total_time = time.perf_counter() - start_time
            
            # Stop monitoring
            self._stop_monitoring()
            
            # Calculate metrics
            avg_processing_time = np.mean(processing_times) if processing_times else 0.0
            peak_memory = max(memory_samples) if memory_samples else self.baseline_memory
            avg_cpu = np.mean(cpu_samples) if cpu_samples else 0.0
            throughput_fps = len(test_data) / total_time if total_time > 0 else 0.0
            success_rate = successful_detections / len(test_data) if test_data else 0.0
            
            # Additional metrics
            additional_metrics = {
                'total_time_seconds': total_time,
                'min_processing_time_ms': min(processing_times) if processing_times else 0.0,
                'max_processing_time_ms': max(processing_times) if processing_times else 0.0,
                'std_processing_time_ms': np.std(processing_times) if processing_times else 0.0,
                'memory_overhead_mb': peak_memory - self.baseline_memory,
                'cpu_overhead_percent': avg_cpu - self.baseline_cpu
            }
            
            result = PerformanceResult(
                method_name=method_name,
                processing_time_ms=avg_processing_time,
                memory_usage_mb=peak_memory,
                cpu_usage_percent=avg_cpu,
                peak_memory_mb=peak_memory,
                throughput_fps=throughput_fps,
                frame_count=len(test_data),
                success_rate=success_rate,
                additional_metrics=additional_metrics
            )
            
            # Store in history
            self.benchmark_history.append(result)
            
            logger.info(f"Benchmark completed for {method_name}: "
                       f"avg_time={avg_processing_time:.2f}ms, "
                       f"throughput={throughput_fps:.1f}fps, "
                       f"success_rate={success_rate:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in benchmark for {method_name}: {str(e)}")
            return PerformanceResult(
                method_name=method_name,
                processing_time_ms=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                peak_memory_mb=0.0,
                throughput_fps=0.0,
                frame_count=0,
                success_rate=0.0
            )
    
    def compare_methods(self, methods: List[Tuple[str, Callable]], 
                       test_data: List[Any], *args, **kwargs) -> Dict[str, PerformanceResult]:
        """
        Compare performance of multiple detection methods.
        
        Args:
            methods: List of (method_name, method_function) tuples
            test_data: Test data for benchmarking
            *args, **kwargs: Additional arguments for methods
            
        Returns:
            Dictionary mapping method names to performance results
        """
        try:
            results = {}
            
            for method_name, method_func in methods:
                logger.info(f"Benchmarking method: {method_name}")
                
                # Force garbage collection before each benchmark
                gc.collect()
                
                result = self.benchmark_method(method_func, method_name, test_data, *args, **kwargs)
                results[method_name] = result
                
                # Brief pause between benchmarks
                time.sleep(1.0)
            
            # Generate comparison summary
            self._log_comparison_summary(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error comparing methods: {str(e)}")
            return {}
    
    def benchmark_phase_comparison(self, phase_configs: Dict[str, Dict[str, Any]], 
                                  test_data: List[Any]) -> Dict[str, PerformanceResult]:
        """
        Benchmark different phases of court detection development.
        
        Args:
            phase_configs: Dictionary mapping phase names to configuration
            test_data: Test data for benchmarking
            
        Returns:
            Dictionary mapping phase names to performance results
        """
        try:
            from ..court_detector import CourtDetector
            
            results = {}
            
            for phase_name, config in phase_configs.items():
                logger.info(f"Benchmarking phase: {phase_name}")
                
                # Create detector with phase-specific configuration
                detector = CourtDetector(config)
                
                # Benchmark the detection method
                result = self.benchmark_method(
                    detector.detect_court, 
                    f"phase_{phase_name}", 
                    test_data
                )
                
                results[phase_name] = result
                
                # Cleanup
                if hasattr(detector, 'cleanup_all_components'):
                    detector.cleanup_all_components()
                
                gc.collect()
                time.sleep(2.0)  # Longer pause between phases
            
            return results
            
        except Exception as e:
            logger.error(f"Error in phase comparison benchmark: {str(e)}")
            return {}
    
    def _start_monitoring(self):
        """Start system resource monitoring."""
        try:
            self.monitoring_active = True
            self.resource_samples = {
                'memory': deque(maxlen=1000),
                'cpu': deque(maxlen=1000),
                'timestamps': deque(maxlen=1000)
            }
            
            def monitor_resources():
                while self.monitoring_active:
                    try:
                        self.resource_samples['memory'].append(
                            psutil.virtual_memory().used / (1024**2)
                        )
                        self.resource_samples['cpu'].append(psutil.cpu_percent())
                        self.resource_samples['timestamps'].append(time.time())
                        
                        time.sleep(self.sample_interval)
                    except Exception as e:
                        logger.error(f"Error in resource monitoring: {str(e)}")
                        break
            
            self.monitoring_thread = threading.Thread(target=monitor_resources, daemon=True)
            self.monitoring_thread.start()
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {str(e)}")
    
    def _stop_monitoring(self):
        """Stop system resource monitoring."""
        try:
            self.monitoring_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=1.0)
        except Exception as e:
            logger.error(f"Error stopping monitoring: {str(e)}")
    
    def _is_detection_successful(self, result) -> bool:
        """Check if detection result indicates success."""
        try:
            if hasattr(result, 'confidence_score'):
                return result.confidence_score > 0.3
            elif hasattr(result, 'corners') and result.corners:
                return len(result.corners) >= 4
            else:
                return result is not None
        except Exception:
            return False
    
    def _log_comparison_summary(self, results: Dict[str, PerformanceResult]):
        """Log comparison summary of benchmark results."""
        try:
            logger.info("=== Performance Comparison Summary ===")
            
            # Sort by throughput (descending)
            sorted_results = sorted(results.items(), 
                                  key=lambda x: x[1].throughput_fps, reverse=True)
            
            for method_name, result in sorted_results:
                logger.info(f"{method_name:20s}: "
                           f"{result.processing_time_ms:6.2f}ms, "
                           f"{result.throughput_fps:6.1f}fps, "
                           f"{result.memory_usage_mb:6.1f}MB, "
                           f"{result.success_rate:5.3f} success")
            
        except Exception as e:
            logger.error(f"Error logging comparison summary: {str(e)}")
    
    def get_benchmark_statistics(self) -> Dict[str, Any]:
        """Get comprehensive benchmark statistics."""
        try:
            if not self.benchmark_history:
                return {'error': 'No benchmark data available'}
            
            # Aggregate statistics across all benchmarks
            processing_times = [r.processing_time_ms for r in self.benchmark_history]
            throughputs = [r.throughput_fps for r in self.benchmark_history]
            memory_usage = [r.memory_usage_mb for r in self.benchmark_history]
            success_rates = [r.success_rate for r in self.benchmark_history]
            
            stats = {
                'total_benchmarks': len(self.benchmark_history),
                'processing_time_statistics': {
                    'mean_ms': np.mean(processing_times),
                    'std_ms': np.std(processing_times),
                    'min_ms': np.min(processing_times),
                    'max_ms': np.max(processing_times),
                    'median_ms': np.median(processing_times)
                },
                'throughput_statistics': {
                    'mean_fps': np.mean(throughputs),
                    'std_fps': np.std(throughputs),
                    'min_fps': np.min(throughputs),
                    'max_fps': np.max(throughputs),
                    'median_fps': np.median(throughputs)
                },
                'memory_statistics': {
                    'mean_mb': np.mean(memory_usage),
                    'std_mb': np.std(memory_usage),
                    'min_mb': np.min(memory_usage),
                    'max_mb': np.max(memory_usage),
                    'median_mb': np.median(memory_usage)
                },
                'success_rate_statistics': {
                    'mean': np.mean(success_rates),
                    'std': np.std(success_rates),
                    'min': np.min(success_rates),
                    'max': np.max(success_rates),
                    'median': np.median(success_rates)
                },
                'method_breakdown': {r.method_name: {
                    'processing_time_ms': r.processing_time_ms,
                    'throughput_fps': r.throughput_fps,
                    'memory_mb': r.memory_usage_mb,
                    'success_rate': r.success_rate
                } for r in self.benchmark_history}
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting benchmark statistics: {str(e)}")
            return {'error': str(e)}
    
    def export_benchmark_results(self, filepath: str) -> bool:
        """Export benchmark results to file."""
        try:
            import json
            
            # Convert results to serializable format
            serializable_results = []
            for result in self.benchmark_history:
                serializable_result = {
                    'method_name': result.method_name,
                    'processing_time_ms': result.processing_time_ms,
                    'memory_usage_mb': result.memory_usage_mb,
                    'cpu_usage_percent': result.cpu_usage_percent,
                    'peak_memory_mb': result.peak_memory_mb,
                    'throughput_fps': result.throughput_fps,
                    'frame_count': result.frame_count,
                    'success_rate': result.success_rate,
                    'additional_metrics': result.additional_metrics
                }
                serializable_results.append(serializable_result)
            
            export_data = {
                'benchmark_results': serializable_results,
                'statistics': self.get_benchmark_statistics(),
                'system_info': {
                    'baseline_memory_mb': self.baseline_memory,
                    'baseline_cpu_percent': self.baseline_cpu
                }
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Benchmark results exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting benchmark results: {str(e)}")
            return False
    
    def reset_history(self):
        """Reset benchmark history."""
        self.benchmark_history = []
        logger.info("Benchmark history reset")
