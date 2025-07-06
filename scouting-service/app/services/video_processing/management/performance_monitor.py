#!/usr/bin/env python3
"""
Performance monitoring for basketball court detection system.

This module provides comprehensive performance tracking including:
- Processing time measurement and analysis
- Accuracy tracking over time
- System resource monitoring
- Bottleneck identification
- Performance trend analysis

Part of Phase 3: Temporal Consistency implementation.
"""

import time
import psutil
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, field
import threading
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Data class for storing performance metrics."""
    timestamp: float
    processing_time_ms: float
    confidence_score: float
    detection_method: str
    frame_number: int
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    roi_used: bool = False
    frame_skipped: bool = False
    outlier_detected: bool = False


class PerformanceMonitor:
    """
    Comprehensive performance monitoring for court detection system.
    
    This class tracks processing times, accuracy trends, system resources,
    and provides analysis tools for performance optimization.
    """

    def __init__(self, max_history: int = 1000, save_interval: int = 100):
        """
        Initialize performance monitor.

        Args:
            max_history: Maximum number of metrics to keep in memory
            save_interval: Number of frames between saving metrics to disk
        """
        self.max_history = max_history
        self.save_interval = save_interval
        
        # Metrics storage
        self.metrics_history: deque = deque(maxlen=max_history)
        self.method_stats: Dict[str, List[float]] = defaultdict(list)
        
        # Timing contexts
        self.timing_contexts: Dict[str, float] = {}
        self.timing_lock = threading.Lock()
        
        # Performance tracking
        self.frame_count = 0
        self.total_processing_time = 0.0
        self.accuracy_history: deque = deque(maxlen=max_history)
        
        # System monitoring
        self.process = psutil.Process()
        self.system_stats: deque = deque(maxlen=100)
        
        # Bottleneck detection
        self.bottleneck_thresholds = {
            'processing_time_ms': 50.0,  # 50ms threshold
            'cpu_usage': 80.0,           # 80% CPU usage
            'memory_usage_mb': 500.0     # 500MB memory usage
        }
        
        # File paths for persistent storage
        self.metrics_file = Path("performance_metrics.json")
        self.stats_file = Path("performance_stats.json")
        
        logger.debug(f"PerformanceMonitor initialized: max_history={max_history}")

    def start_timing(self, context_name: str):
        """
        Start timing a specific operation.

        Args:
            context_name: Name of the operation being timed
        """
        try:
            with self.timing_lock:
                self.timing_contexts[context_name] = time.perf_counter()
                
        except Exception as e:
            logger.error(f"Error starting timing for '{context_name}': {str(e)}")

    def end_timing(self, context_name: str) -> float:
        """
        End timing and return elapsed time.

        Args:
            context_name: Name of the operation being timed

        Returns:
            Elapsed time in milliseconds
        """
        try:
            with self.timing_lock:
                if context_name in self.timing_contexts:
                    start_time = self.timing_contexts.pop(context_name)
                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    return elapsed_ms
                else:
                    logger.warning(f"No timing context found for '{context_name}'")
                    return 0.0
                    
        except Exception as e:
            logger.error(f"Error ending timing for '{context_name}': {str(e)}")
            return 0.0

    def record_frame_metrics(self, confidence_score: float, detection_method: str,
                           processing_time_ms: float, frame_number: int,
                           roi_used: bool = False, frame_skipped: bool = False,
                           outlier_detected: bool = False):
        """
        Record metrics for a processed frame.

        Args:
            confidence_score: Detection confidence (0-1)
            detection_method: Method used for detection
            processing_time_ms: Processing time in milliseconds
            frame_number: Frame number
            roi_used: Whether ROI optimization was used
            frame_skipped: Whether frame was skipped
            outlier_detected: Whether outlier was detected
        """
        try:
            # Get system metrics
            cpu_usage = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_usage_mb = memory_info.rss / (1024 * 1024)  # Convert to MB

            # Create metrics object
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                processing_time_ms=processing_time_ms,
                confidence_score=confidence_score,
                detection_method=detection_method,
                frame_number=frame_number,
                cpu_usage=cpu_usage,
                memory_usage_mb=memory_usage_mb,
                roi_used=roi_used,
                frame_skipped=frame_skipped,
                outlier_detected=outlier_detected
            )

            # Store metrics
            self.metrics_history.append(metrics)
            self.method_stats[detection_method].append(processing_time_ms)
            self.accuracy_history.append(confidence_score)
            
            # Update counters
            self.frame_count += 1
            self.total_processing_time += processing_time_ms

            # Store system stats
            self.system_stats.append({
                'timestamp': metrics.timestamp,
                'cpu_usage': cpu_usage,
                'memory_usage_mb': memory_usage_mb
            })

            # Check for bottlenecks
            self._check_bottlenecks(metrics)

            # Periodic save to disk
            if self.frame_count % self.save_interval == 0:
                self._save_metrics_to_disk()

            logger.debug(f"Frame {frame_number}: {processing_time_ms:.1f}ms, "
                        f"confidence={confidence_score:.3f}, method={detection_method}")

        except Exception as e:
            logger.error(f"Error recording frame metrics: {str(e)}")

    def _check_bottlenecks(self, metrics: PerformanceMetrics):
        """Check for performance bottlenecks and log warnings."""
        try:
            bottlenecks = []

            if metrics.processing_time_ms > self.bottleneck_thresholds['processing_time_ms']:
                bottlenecks.append(f"High processing time: {metrics.processing_time_ms:.1f}ms")

            if metrics.cpu_usage > self.bottleneck_thresholds['cpu_usage']:
                bottlenecks.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")

            if metrics.memory_usage_mb > self.bottleneck_thresholds['memory_usage_mb']:
                bottlenecks.append(f"High memory usage: {metrics.memory_usage_mb:.1f}MB")

            if bottlenecks:
                logger.warning(f"Performance bottlenecks detected: {', '.join(bottlenecks)}")

        except Exception as e:
            logger.error(f"Error checking bottlenecks: {str(e)}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.

        Returns:
            Dictionary with performance statistics
        """
        try:
            if not self.metrics_history:
                return {'error': 'No metrics available'}

            # Calculate basic statistics
            processing_times = [m.processing_time_ms for m in self.metrics_history]
            confidence_scores = [m.confidence_score for m in self.metrics_history]
            
            avg_processing_time = np.mean(processing_times)
            std_processing_time = np.std(processing_times)
            avg_confidence = np.mean(confidence_scores)
            std_confidence = np.std(confidence_scores)

            # Method-specific statistics
            method_stats = {}
            for method, times in self.method_stats.items():
                if times:
                    method_stats[method] = {
                        'avg_time_ms': np.mean(times),
                        'std_time_ms': np.std(times),
                        'count': len(times),
                        'min_time_ms': np.min(times),
                        'max_time_ms': np.max(times)
                    }

            # System resource statistics
            if self.system_stats:
                cpu_usages = [s['cpu_usage'] for s in self.system_stats]
                memory_usages = [s['memory_usage_mb'] for s in self.system_stats]
                
                system_summary = {
                    'avg_cpu_usage': np.mean(cpu_usages),
                    'max_cpu_usage': np.max(cpu_usages),
                    'avg_memory_mb': np.mean(memory_usages),
                    'max_memory_mb': np.max(memory_usages)
                }
            else:
                system_summary = {}

            # Optimization statistics
            roi_frames = sum(1 for m in self.metrics_history if m.roi_used)
            skipped_frames = sum(1 for m in self.metrics_history if m.frame_skipped)
            outlier_frames = sum(1 for m in self.metrics_history if m.outlier_detected)

            return {
                'total_frames': self.frame_count,
                'avg_processing_time_ms': avg_processing_time,
                'std_processing_time_ms': std_processing_time,
                'avg_confidence': avg_confidence,
                'std_confidence': std_confidence,
                'method_statistics': method_stats,
                'system_resources': system_summary,
                'optimization_stats': {
                    'roi_frames': roi_frames,
                    'skipped_frames': skipped_frames,
                    'outlier_frames': outlier_frames,
                    'roi_rate': roi_frames / len(self.metrics_history) if self.metrics_history else 0,
                    'skip_rate': skipped_frames / len(self.metrics_history) if self.metrics_history else 0,
                    'outlier_rate': outlier_frames / len(self.metrics_history) if self.metrics_history else 0
                },
                'performance_trends': self._calculate_trends()
            }

        except Exception as e:
            logger.error(f"Error getting performance summary: {str(e)}")
            return {'error': str(e)}

    def _calculate_trends(self) -> Dict[str, float]:
        """Calculate performance trends over time."""
        try:
            if len(self.metrics_history) < 10:
                return {}

            # Get recent metrics for trend analysis
            recent_metrics = list(self.metrics_history)[-50:]  # Last 50 frames
            
            # Calculate trends
            processing_times = [m.processing_time_ms for m in recent_metrics]
            confidence_scores = [m.confidence_score for m in recent_metrics]
            
            # Linear regression for trends
            x = np.arange(len(processing_times))
            
            # Processing time trend
            if len(processing_times) > 1:
                time_trend = np.polyfit(x, processing_times, 1)[0]
            else:
                time_trend = 0.0
                
            # Confidence trend
            if len(confidence_scores) > 1:
                confidence_trend = np.polyfit(x, confidence_scores, 1)[0]
            else:
                confidence_trend = 0.0

            return {
                'processing_time_trend': time_trend,  # ms per frame
                'confidence_trend': confidence_trend,  # confidence per frame
                'frames_analyzed': len(recent_metrics)
            }

        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return {}

    def get_method_comparison(self) -> Dict[str, Dict[str, float]]:
        """
        Compare performance across different detection methods.

        Returns:
            Dictionary with method comparison statistics
        """
        try:
            comparison = {}
            
            for method, times in self.method_stats.items():
                if len(times) > 0:
                    # Get confidence scores for this method
                    method_confidences = [
                        m.confidence_score for m in self.metrics_history 
                        if m.detection_method == method
                    ]
                    
                    comparison[method] = {
                        'avg_time_ms': np.mean(times),
                        'std_time_ms': np.std(times),
                        'min_time_ms': np.min(times),
                        'max_time_ms': np.max(times),
                        'avg_confidence': np.mean(method_confidences) if method_confidences else 0.0,
                        'frame_count': len(times),
                        'efficiency_score': np.mean(method_confidences) / np.mean(times) if method_confidences and np.mean(times) > 0 else 0.0
                    }

            return comparison

        except Exception as e:
            logger.error(f"Error getting method comparison: {str(e)}")
            return {}

    def _save_metrics_to_disk(self):
        """Save metrics to disk for persistence."""
        try:
            # Save recent metrics
            recent_metrics = list(self.metrics_history)[-100:]  # Last 100 frames
            metrics_data = []
            
            for m in recent_metrics:
                metrics_data.append({
                    'timestamp': m.timestamp,
                    'processing_time_ms': m.processing_time_ms,
                    'confidence_score': m.confidence_score,
                    'detection_method': m.detection_method,
                    'frame_number': m.frame_number,
                    'cpu_usage': m.cpu_usage,
                    'memory_usage_mb': m.memory_usage_mb,
                    'roi_used': m.roi_used,
                    'frame_skipped': m.frame_skipped,
                    'outlier_detected': m.outlier_detected
                })

            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)

            # Save performance summary
            summary = self.get_performance_summary()
            with open(self.stats_file, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.debug(f"Saved {len(metrics_data)} metrics to disk")

        except Exception as e:
            logger.error(f"Error saving metrics to disk: {str(e)}")

    def reset_metrics(self):
        """Reset all metrics and statistics."""
        try:
            self.metrics_history.clear()
            self.method_stats.clear()
            self.accuracy_history.clear()
            self.system_stats.clear()
            self.timing_contexts.clear()
            
            self.frame_count = 0
            self.total_processing_time = 0.0
            
            logger.debug("Performance metrics reset")

        except Exception as e:
            logger.error(f"Error resetting metrics: {str(e)}")

    def export_metrics(self, filepath: str) -> bool:
        """
        Export all metrics to a file.

        Args:
            filepath: Path to export file

        Returns:
            True if export successful, False otherwise
        """
        try:
            export_data = {
                'summary': self.get_performance_summary(),
                'method_comparison': self.get_method_comparison(),
                'raw_metrics': [
                    {
                        'timestamp': m.timestamp,
                        'processing_time_ms': m.processing_time_ms,
                        'confidence_score': m.confidence_score,
                        'detection_method': m.detection_method,
                        'frame_number': m.frame_number,
                        'cpu_usage': m.cpu_usage,
                        'memory_usage_mb': m.memory_usage_mb,
                        'roi_used': m.roi_used,
                        'frame_skipped': m.frame_skipped,
                        'outlier_detected': m.outlier_detected
                    }
                    for m in self.metrics_history
                ]
            }

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Metrics exported to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting metrics: {str(e)}")
            return False
