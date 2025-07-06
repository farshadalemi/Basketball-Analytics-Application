"""
Validation framework for basketball court detection.

This package provides comprehensive validation tools for testing and benchmarking
court detection algorithms across different phases of development.

Modules:
- accuracy_metrics: IoU, corner accuracy, and geometric validation metrics
- performance_metrics: Processing time, memory usage, and throughput benchmarks
- test_suite: Comprehensive test cases for all detection phases
- dataset_manager: Test dataset management and ground truth handling
"""

from .accuracy_metrics import AccuracyMetrics
from .performance_metrics import PerformanceBenchmark
from .test_suite import CourtDetectionTestSuite

__all__ = [
    'AccuracyMetrics',
    'PerformanceBenchmark', 
    'CourtDetectionTestSuite'
]
