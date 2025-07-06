#!/usr/bin/env python3
"""
Performance optimization for real-time basketball court detection.

This module implements performance optimization strategies including:
- Intelligent frame skipping based on confidence and processing time
- ROI-based processing to focus on court regions
- Memory pool optimization for common operations
- Multi-threading support for parallel detection methods

Part of Phase 3: Temporal Consistency implementation.
"""

import numpy as np
import time
import logging
import os
import psutil
import platform
from typing import Optional, Dict, List, Tuple, Any
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    Performance optimization strategies for real-time court detection.
    
    This class provides intelligent frame processing decisions, ROI optimization,
    and memory management to achieve real-time performance while maintaining
    detection accuracy.
    """

    def __init__(self, target_fps: float = 30.0):
        """
        Initialize performance optimizer with Phase 4 hardware-specific optimizations.

        Args:
            target_fps: Target frames per second for processing
        """
        self.target_fps = target_fps
        self.max_processing_time = 1000.0 / target_fps  # ms per frame

        # Phase 4: Hardware detection and optimization
        self.hardware_info = self._detect_hardware_capabilities()
        self.cpu_optimization = self._configure_cpu_optimization()

        # Frame skipping state
        self.frame_skip_counter = 0
        self.confidence_history = deque(maxlen=10)
        self.processing_times = deque(maxlen=10)

        # ROI state
        self.roi_established = False
        self.current_roi: Optional[Tuple[int, int, int, int]] = None
        self.roi_confidence_threshold = 0.7
        self.roi_expansion_factor = 0.2

        # Phase 4: Enhanced memory pool with hardware-specific sizing
        self.memory_pool = self._initialize_memory_pool_enhanced()

        # Phase 4: Advanced threading with hardware-aware configuration
        self.max_workers = self._calculate_optimal_workers()
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.thread_affinity_enabled = self.hardware_info.get('supports_affinity', False)

        # Performance tracking
        self.total_frames = 0
        self.skipped_frames = 0
        self.roi_frames = 0
        self.hardware_optimized_frames = 0

        logger.info(f"PerformanceOptimizer initialized with Phase 4 enhancements:")
        logger.info(f"  Target FPS: {target_fps}, Max processing time: {self.max_processing_time:.1f}ms")
        logger.info(f"  CPU cores: {self.hardware_info['cpu_cores']}, Optimal workers: {self.max_workers}")
        logger.info(f"  Available memory: {self.hardware_info['available_memory_gb']:.1f}GB")
        logger.info(f"  CPU optimization: {self.cpu_optimization['strategy']}")

    def should_process_frame(self, frame_number: int, last_confidence: float, 
                           processing_time_ms: float) -> bool:
        """
        Determine frame processing strategy based on performance and confidence.

        Args:
            frame_number: Current frame number
            last_confidence: Confidence score from last detection
            processing_time_ms: Processing time of last frame in milliseconds

        Returns:
            True if frame should be fully processed, False to skip
        """
        try:
            self.total_frames += 1
            
            # Always process initial frames for initialization
            if frame_number < 30:
                return True

            # Store metrics in history
            self.confidence_history.append(last_confidence)
            self.processing_times.append(processing_time_ms)

            # Calculate averages
            avg_confidence = np.mean(self.confidence_history) if self.confidence_history else 0.0
            avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0.0

            # Determine skip strategy based on performance and confidence
            skip_rate = self._calculate_skip_rate(avg_confidence, avg_processing_time)

            # Apply frame skipping
            self.frame_skip_counter += 1
            should_process = (self.frame_skip_counter % skip_rate) == 0

            if not should_process:
                self.skipped_frames += 1

            logger.debug(f"Frame {frame_number}: confidence={avg_confidence:.3f}, "
                        f"time={avg_processing_time:.1f}ms, skip_rate={skip_rate}, "
                        f"process={should_process}")

            return should_process

        except Exception as e:
            logger.error(f"Error in frame processing decision: {str(e)}")
            return True  # Default to processing on error

    def _calculate_skip_rate(self, avg_confidence: float, avg_processing_time: float) -> int:
        """
        Calculate frame skip rate based on confidence and processing time.

        Args:
            avg_confidence: Average confidence over recent frames
            avg_processing_time: Average processing time in milliseconds

        Returns:
            Skip rate (1 = process every frame, 2 = skip every other frame, etc.)
        """
        try:
            # Base skip rate
            skip_rate = 1

            # High confidence and fast processing - can skip more frames
            if avg_confidence > 0.8 and avg_processing_time < self.max_processing_time * 0.5:
                skip_rate = 3  # Process every 3rd frame
            elif avg_confidence > 0.7 and avg_processing_time < self.max_processing_time * 0.7:
                skip_rate = 2  # Process every 2nd frame
            elif avg_confidence > 0.6:
                skip_rate = 1  # Process every frame
            else:
                # Low confidence - process every frame
                skip_rate = 1

            # Adjust for processing time pressure
            if avg_processing_time > self.max_processing_time:
                skip_rate = max(skip_rate, 2)  # Force skipping if too slow
            elif avg_processing_time > self.max_processing_time * 1.5:
                skip_rate = max(skip_rate, 3)  # More aggressive skipping

            return skip_rate

        except Exception as e:
            logger.error(f"Error calculating skip rate: {str(e)}")
            return 1

    def get_processing_roi(self, frame_shape: Tuple[int, int], last_detection: Any, 
                          confidence: float) -> Optional[Tuple[int, int, int, int]]:
        """
        Calculate Region of Interest for focused processing.

        Args:
            frame_shape: (height, width) of frame
            last_detection: Previous detection results with corners attribute
            confidence: Confidence of last detection

        Returns:
            ROI coordinates (x, y, width, height) or None for full frame
        """
        try:
            # Reset ROI if confidence drops significantly
            if confidence < self.roi_confidence_threshold * 0.7:
                self.roi_established = False
                self.current_roi = None
                return None

            # Use full frame if no previous detection or low confidence
            if last_detection is None or confidence < self.roi_confidence_threshold:
                return None

            # Check if detection has valid corners
            if not hasattr(last_detection, 'corners') or not last_detection.corners or len(last_detection.corners) < 4:
                return None

            # Calculate bounding box of last detection
            corners = last_detection.corners
            x_coords = [c[0] for c in corners]
            y_coords = [c[1] for c in corners]

            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)

            # Expand by margin
            width = max_x - min_x
            height = max_y - min_y
            margin_x = width * self.roi_expansion_factor
            margin_y = height * self.roi_expansion_factor

            # Calculate ROI with margins
            roi_x = max(0, int(min_x - margin_x))
            roi_y = max(0, int(min_y - margin_y))
            roi_width = min(frame_shape[1] - roi_x, int(width + 2 * margin_x))
            roi_height = min(frame_shape[0] - roi_y, int(height + 2 * margin_y))

            # Only use ROI if it's significantly smaller than full frame
            roi_area = roi_width * roi_height
            full_area = frame_shape[0] * frame_shape[1]

            if roi_area < full_area * 0.8:  # ROI is at least 20% smaller
                self.current_roi = (roi_x, roi_y, roi_width, roi_height)
                self.roi_established = True
                self.roi_frames += 1
                
                logger.debug(f"ROI established: ({roi_x}, {roi_y}, {roi_width}, {roi_height}), "
                           f"reduction={1.0 - roi_area/full_area:.2f}")
                
                return self.current_roi
            else:
                return None  # Use full frame

        except Exception as e:
            logger.error(f"Error calculating processing ROI: {str(e)}")
            return None

    def _initialize_memory_pool(self) -> Dict[str, Any]:
        """
        Pre-allocate memory for common operations.

        Returns:
            Dictionary with pre-allocated memory objects
        """
        try:
            memory_pool = {
                # Common image sizes for intermediate processing
                'temp_gray_720p': np.zeros((720, 1280), dtype=np.uint8),
                'temp_gray_480p': np.zeros((480, 640), dtype=np.uint8),
                'temp_edges': np.zeros((720, 1280), dtype=np.uint8),
                
                # Arrays for corner detection
                'corner_buffer': np.zeros((1000, 2), dtype=np.float32),
                'line_buffer': np.zeros((500, 4), dtype=np.float32),
                
                # Homography computation
                'homography_src': np.zeros((4, 2), dtype=np.float32),
                'homography_dst': np.zeros((4, 2), dtype=np.float32),
                
                # Temporary matrices
                'temp_matrix_3x3': np.zeros((3, 3), dtype=np.float32),
                'temp_vector_9': np.zeros(9, dtype=np.float32),
            }
            
            logger.debug(f"Memory pool initialized with {len(memory_pool)} objects")
            return memory_pool

        except Exception as e:
            logger.error(f"Error initializing memory pool: {str(e)}")
            return {}

    def get_temp_array(self, key: str, shape: Optional[Tuple[int, ...]] = None, 
                      dtype: np.dtype = np.uint8) -> np.ndarray:
        """
        Get temporary array from memory pool or create new one.

        Args:
            key: Key for the array in memory pool
            shape: Required shape (if different from pool)
            dtype: Required data type

        Returns:
            Temporary array for use
        """
        try:
            if key in self.memory_pool:
                array = self.memory_pool[key]
                if shape is None or array.shape == shape:
                    array.fill(0)  # Clear the array
                    return array

            # Create new array if not in pool or wrong shape
            if shape is not None:
                return np.zeros(shape, dtype=dtype)
            else:
                logger.warning(f"No array found for key '{key}' and no shape provided")
                return np.zeros((100, 100), dtype=dtype)

        except Exception as e:
            logger.error(f"Error getting temp array: {str(e)}")
            return np.zeros((100, 100), dtype=dtype)

    def parallel_detection(self, detection_methods: List[Tuple[str, callable]], 
                          frame: np.ndarray, *args, **kwargs) -> List[Tuple[str, Any]]:
        """
        Execute detection methods in parallel.

        Args:
            detection_methods: List of (method_name, method_function) tuples
            frame: Input frame for detection
            *args, **kwargs: Additional arguments for detection methods

        Returns:
            List of (method_name, result) tuples
        """
        try:
            if len(detection_methods) <= 1:
                # No benefit from parallelization
                results = []
                for method_name, method_func in detection_methods:
                    result = method_func(frame, *args, **kwargs)
                    results.append((method_name, result))
                return results

            # Use thread pool for parallel execution
            if self.thread_pool is None:
                self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

            # Submit all detection methods
            future_to_method = {}
            for method_name, method_func in detection_methods:
                future = self.thread_pool.submit(method_func, frame, *args, **kwargs)
                future_to_method[future] = method_name

            # Collect results
            results = []
            for future in as_completed(future_to_method, timeout=5.0):  # 5 second timeout
                method_name = future_to_method[future]
                try:
                    result = future.result()
                    results.append((method_name, result))
                except Exception as e:
                    logger.error(f"Error in parallel detection method '{method_name}': {str(e)}")
                    results.append((method_name, None))

            return results

        except Exception as e:
            logger.error(f"Error in parallel detection: {str(e)}")
            # Fallback to sequential execution
            results = []
            for method_name, method_func in detection_methods:
                try:
                    result = method_func(frame, *args, **kwargs)
                    results.append((method_name, result))
                except Exception as method_error:
                    logger.error(f"Error in method '{method_name}': {str(method_error)}")
                    results.append((method_name, None))
            return results

    # Phase 4: Hardware-Aware Parallel Processing Enhancements

    def parallel_detection_enhanced(self, detection_methods: List[Tuple[str, callable]],
                                  frame: np.ndarray, *args, **kwargs) -> List[Tuple[str, Any]]:
        """
        Enhanced parallel detection with Phase 4 hardware optimizations.
        """
        try:
            # Check if parallel processing is beneficial
            if (len(detection_methods) <= 1 or
                not self.cpu_optimization['enable_parallel_preprocessing'] or
                self.hardware_info['cpu_cores'] < 2):
                return self._execute_sequential(detection_methods, frame, *args, **kwargs)

            # Hardware-aware thread pool initialization
            if self.thread_pool is None:
                self.thread_pool = ThreadPoolExecutor(
                    max_workers=self.max_workers,
                    thread_name_prefix="court_detection"
                )

            # Prioritize methods based on hardware performance
            prioritized_methods = self._prioritize_detection_methods(detection_methods)

            # Submit with hardware-aware scheduling
            future_to_method = {}
            for priority, (method_name, method_func) in enumerate(prioritized_methods):
                future = self.thread_pool.submit(
                    self._hardware_optimized_wrapper,
                    method_func, frame, method_name, priority, *args, **kwargs
                )
                future_to_method[future] = method_name

            # Collect results with adaptive timeout
            timeout = self._calculate_adaptive_timeout(len(detection_methods))
            results = []

            for future in as_completed(future_to_method, timeout=timeout):
                method_name = future_to_method[future]
                try:
                    result = future.result()
                    results.append((method_name, result))
                    self.hardware_optimized_frames += 1
                except Exception as e:
                    logger.error(f"Error in enhanced parallel detection '{method_name}': {str(e)}")
                    results.append((method_name, None))

            return results

        except Exception as e:
            logger.error(f"Error in enhanced parallel detection: {str(e)}")
            return self._execute_sequential(detection_methods, frame, *args, **kwargs)

    def _execute_sequential(self, detection_methods: List[Tuple[str, callable]],
                           frame: np.ndarray, *args, **kwargs) -> List[Tuple[str, Any]]:
        """Execute detection methods sequentially."""
        results = []
        for method_name, method_func in detection_methods:
            try:
                result = method_func(frame, *args, **kwargs)
                results.append((method_name, result))
            except Exception as e:
                logger.error(f"Error in sequential detection '{method_name}': {str(e)}")
                results.append((method_name, None))
        return results

    def _prioritize_detection_methods(self, detection_methods: List[Tuple[str, callable]]) -> List[Tuple[str, callable]]:
        """Prioritize detection methods based on hardware performance."""
        method_priorities = {
            'line_detection': 1,
            'keypoint_detection': 2,
            'color_detection': 3,
            'template_matching': 4
        }

        return sorted(detection_methods, key=lambda x: method_priorities.get(x[0], 5))

    def _hardware_optimized_wrapper(self, method_func: callable, frame: np.ndarray,
                                   method_name: str, priority: int, *args, **kwargs) -> Any:
        """Wrapper for detection methods with hardware optimizations."""
        try:
            start_time = time.perf_counter()
            result = method_func(frame, *args, **kwargs)
            execution_time = (time.perf_counter() - start_time) * 1000

            logger.debug(f"Method '{method_name}' completed in {execution_time:.2f}ms")
            return result

        except Exception as e:
            logger.error(f"Error in hardware wrapper for '{method_name}': {str(e)}")
            raise

    def _calculate_adaptive_timeout(self, num_methods: int) -> float:
        """Calculate adaptive timeout based on hardware performance."""
        base_timeout = 2.0
        performance_multiplier = 2.0 - self.hardware_info['overall_performance_score']
        total_timeout = num_methods * base_timeout * performance_multiplier
        return max(5.0, min(total_timeout, 30.0))

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance optimization statistics.

        Returns:
            Dictionary with performance metrics
        """
        try:
            skip_rate = self.skipped_frames / self.total_frames if self.total_frames > 0 else 0.0
            roi_rate = self.roi_frames / self.total_frames if self.total_frames > 0 else 0.0
            hardware_optimized_rate = self.hardware_optimized_frames / self.total_frames if self.total_frames > 0 else 0.0

            avg_processing_time = np.mean(self.processing_times) if self.processing_times else 0.0
            avg_confidence = np.mean(self.confidence_history) if self.confidence_history else 0.0

            stats = {
                # Basic performance metrics
                'total_frames': self.total_frames,
                'skipped_frames': self.skipped_frames,
                'roi_frames': self.roi_frames,
                'skip_rate': skip_rate,
                'roi_rate': roi_rate,
                'avg_processing_time_ms': avg_processing_time,
                'avg_confidence': avg_confidence,
                'target_fps': self.target_fps,
                'max_processing_time_ms': self.max_processing_time,
                'roi_established': self.roi_established,

                # Phase 4: Hardware optimization metrics
                'hardware_optimized_frames': self.hardware_optimized_frames,
                'hardware_optimized_rate': hardware_optimized_rate,
                'hardware_info': self.hardware_info,
                'cpu_optimization': self.cpu_optimization,
                'optimal_workers': self.max_workers,
                'memory_strategy': self.memory_pool.get('memory_strategy', 'unknown'),
                'thread_pool_active': self.thread_pool is not None
            }

            # Add memory pool statistics if available
            if 'usage_counters' in self.memory_pool:
                stats['memory_pool_usage'] = self.memory_pool['usage_counters']

            return stats

        except Exception as e:
            logger.error(f"Error getting performance stats: {str(e)}")
            return {'error': str(e)}

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.thread_pool is not None:
                self.thread_pool.shutdown(wait=True)
                self.thread_pool = None
            
            logger.debug("PerformanceOptimizer cleaned up")

        except Exception as e:
            logger.error(f"Error cleaning up PerformanceOptimizer: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()

    # Phase 4: Hardware-Specific Optimization Methods

    def _detect_hardware_capabilities(self) -> Dict[str, Any]:
        """
        Detect hardware capabilities for optimization.

        Returns:
            Dictionary with hardware information
        """
        try:
            # CPU information
            cpu_count = multiprocessing.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Memory information
            memory = psutil.virtual_memory()
            available_memory_gb = memory.available / (1024**3)
            total_memory_gb = memory.total / (1024**3)

            # Platform information
            system = platform.system()
            machine = platform.machine()
            processor = platform.processor()

            # CPU features detection
            supports_affinity = hasattr(os, 'sched_setaffinity') if system == 'Linux' else False

            # Performance characteristics estimation
            cpu_performance_score = self._estimate_cpu_performance(cpu_count, cpu_freq)
            memory_performance_score = min(1.0, available_memory_gb / 8.0)  # Normalize to 8GB

            hardware_info = {
                'cpu_cores': cpu_count,
                'cpu_freq_current': cpu_freq.current if cpu_freq else 0,
                'cpu_freq_max': cpu_freq.max if cpu_freq else 0,
                'available_memory_gb': available_memory_gb,
                'total_memory_gb': total_memory_gb,
                'memory_usage_percent': memory.percent,
                'system': system,
                'machine': machine,
                'processor': processor,
                'supports_affinity': supports_affinity,
                'cpu_performance_score': cpu_performance_score,
                'memory_performance_score': memory_performance_score,
                'overall_performance_score': (cpu_performance_score + memory_performance_score) / 2
            }

            logger.debug(f"Hardware capabilities detected: {hardware_info}")
            return hardware_info

        except Exception as e:
            logger.error(f"Error detecting hardware capabilities: {str(e)}")
            # Return safe defaults
            return {
                'cpu_cores': 4,
                'cpu_freq_current': 2000,
                'cpu_freq_max': 2000,
                'available_memory_gb': 4.0,
                'total_memory_gb': 8.0,
                'memory_usage_percent': 50.0,
                'system': 'Unknown',
                'machine': 'Unknown',
                'processor': 'Unknown',
                'supports_affinity': False,
                'cpu_performance_score': 0.5,
                'memory_performance_score': 0.5,
                'overall_performance_score': 0.5
            }

    def _estimate_cpu_performance(self, cpu_count: int, cpu_freq) -> float:
        """
        Estimate CPU performance score.

        Args:
            cpu_count: Number of CPU cores
            cpu_freq: CPU frequency information

        Returns:
            Performance score between 0.0 and 1.0
        """
        try:
            # Base score from core count (normalize to 8 cores)
            core_score = min(1.0, cpu_count / 8.0)

            # Frequency score (normalize to 3GHz)
            if cpu_freq and cpu_freq.current:
                freq_score = min(1.0, cpu_freq.current / 3000.0)
            else:
                freq_score = 0.5  # Default assumption

            # Combined score with core count weighted more heavily
            performance_score = 0.7 * core_score + 0.3 * freq_score

            return performance_score

        except Exception as e:
            logger.error(f"Error estimating CPU performance: {str(e)}")
            return 0.5

    def _configure_cpu_optimization(self) -> Dict[str, Any]:
        """
        Configure CPU-specific optimizations.

        Returns:
            Dictionary with CPU optimization configuration
        """
        try:
            cpu_cores = self.hardware_info['cpu_cores']
            performance_score = self.hardware_info['overall_performance_score']

            # Determine optimization strategy based on hardware
            if cpu_cores >= 8 and performance_score > 0.7:
                strategy = "high_performance"
                thread_multiplier = 1.5
                memory_aggressive = True
                enable_parallel_preprocessing = True
            elif cpu_cores >= 4 and performance_score > 0.5:
                strategy = "balanced"
                thread_multiplier = 1.2
                memory_aggressive = False
                enable_parallel_preprocessing = True
            else:
                strategy = "conservative"
                thread_multiplier = 1.0
                memory_aggressive = False
                enable_parallel_preprocessing = False

            config = {
                'strategy': strategy,
                'thread_multiplier': thread_multiplier,
                'memory_aggressive': memory_aggressive,
                'enable_parallel_preprocessing': enable_parallel_preprocessing,
                'enable_cpu_affinity': self.hardware_info['supports_affinity'] and cpu_cores >= 4
            }

            logger.debug(f"CPU optimization configured: {config}")
            return config

        except Exception as e:
            logger.error(f"Error configuring CPU optimization: {str(e)}")
            return {
                'strategy': 'conservative',
                'thread_multiplier': 1.0,
                'memory_aggressive': False,
                'enable_parallel_preprocessing': False,
                'enable_cpu_affinity': False
            }

    def _calculate_optimal_workers(self) -> int:
        """
        Calculate optimal number of worker threads based on hardware.

        Returns:
            Optimal number of worker threads
        """
        try:
            cpu_cores = self.hardware_info['cpu_cores']
            thread_multiplier = self.cpu_optimization['thread_multiplier']

            # Base calculation: use most cores but leave some for system
            base_workers = max(1, cpu_cores - 1)

            # Apply hardware-specific multiplier
            optimal_workers = int(base_workers * thread_multiplier)

            # Ensure reasonable bounds
            optimal_workers = max(1, min(optimal_workers, cpu_cores * 2))

            logger.debug(f"Calculated optimal workers: {optimal_workers} (cores: {cpu_cores}, multiplier: {thread_multiplier})")
            return optimal_workers

        except Exception as e:
            logger.error(f"Error calculating optimal workers: {str(e)}")
            return 4  # Safe default

    def _initialize_memory_pool_enhanced(self) -> Dict[str, Any]:
        """
        Initialize enhanced memory pool with hardware-specific sizing.

        Returns:
            Dictionary containing pre-allocated memory objects
        """
        try:
            available_memory_gb = self.hardware_info['available_memory_gb']
            memory_aggressive = self.cpu_optimization['memory_aggressive']

            # Calculate pool sizes based on available memory
            if memory_aggressive and available_memory_gb > 8.0:
                pool_sizes = {
                    'small_arrays': 50,
                    'medium_arrays': 30,
                    'large_arrays': 10,
                    'temp_buffers': 20
                }
            elif available_memory_gb > 4.0:
                pool_sizes = {
                    'small_arrays': 30,
                    'medium_arrays': 20,
                    'large_arrays': 5,
                    'temp_buffers': 15
                }
            else:
                pool_sizes = {
                    'small_arrays': 20,
                    'medium_arrays': 10,
                    'large_arrays': 3,
                    'temp_buffers': 10
                }

            # Pre-allocate memory pools
            memory_pool = {
                'small_arrays': [np.zeros((100, 100), dtype=np.uint8) for _ in range(pool_sizes['small_arrays'])],
                'medium_arrays': [np.zeros((500, 500), dtype=np.uint8) for _ in range(pool_sizes['medium_arrays'])],
                'large_arrays': [np.zeros((1000, 1000), dtype=np.uint8) for _ in range(pool_sizes['large_arrays'])],
                'temp_buffers': [np.zeros(10000, dtype=np.float32) for _ in range(pool_sizes['temp_buffers'])],
                'usage_counters': {key: 0 for key in pool_sizes.keys()},
                'pool_sizes': pool_sizes,
                'memory_strategy': 'aggressive' if memory_aggressive else 'conservative'
            }

            total_memory_mb = sum(
                sum(array.nbytes for array in arrays)
                for arrays in memory_pool.values()
                if isinstance(arrays, list)
            ) / (1024 * 1024)

            logger.info(f"Enhanced memory pool initialized: {total_memory_mb:.1f}MB allocated")
            return memory_pool

        except Exception as e:
            logger.error(f"Error initializing enhanced memory pool: {str(e)}")
            return {'memory_strategy': 'basic'}

    def _initialize_memory_pool_enhanced(self) -> Dict[str, Any]:
        """
        Initialize enhanced memory pool with hardware-specific sizing.

        Returns:
            Dictionary containing pre-allocated memory objects
        """
        try:
            available_memory_gb = self.hardware_info['available_memory_gb']
            memory_aggressive = self.cpu_optimization['memory_aggressive']

            # Calculate pool sizes based on available memory
            if memory_aggressive and available_memory_gb > 8.0:
                # Large memory pools for high-performance systems
                pool_sizes = {
                    'small_arrays': 50,    # 100x100 arrays
                    'medium_arrays': 30,   # 500x500 arrays
                    'large_arrays': 10,    # 1000x1000 arrays
                    'temp_buffers': 20,    # Various temporary buffers
                    'line_arrays': 100,    # Line detection arrays
                    'corner_arrays': 50    # Corner detection arrays
                }
            elif available_memory_gb > 4.0:
                # Balanced memory pools
                pool_sizes = {
                    'small_arrays': 30,
                    'medium_arrays': 20,
                    'large_arrays': 5,
                    'temp_buffers': 15,
                    'line_arrays': 50,
                    'corner_arrays': 30
                }
            else:
                # Conservative memory pools for limited systems
                pool_sizes = {
                    'small_arrays': 20,
                    'medium_arrays': 10,
                    'large_arrays': 3,
                    'temp_buffers': 10,
                    'line_arrays': 30,
                    'corner_arrays': 20
                }

            # Pre-allocate memory pools
            memory_pool = {
                'small_arrays': [np.zeros((100, 100), dtype=np.uint8) for _ in range(pool_sizes['small_arrays'])],
                'medium_arrays': [np.zeros((500, 500), dtype=np.uint8) for _ in range(pool_sizes['medium_arrays'])],
                'large_arrays': [np.zeros((1000, 1000), dtype=np.uint8) for _ in range(pool_sizes['large_arrays'])],
                'temp_buffers': [np.zeros(10000, dtype=np.float32) for _ in range(pool_sizes['temp_buffers'])],
                'line_arrays': [np.zeros((4, 1000), dtype=np.int32) for _ in range(pool_sizes['line_arrays'])],
                'corner_arrays': [np.zeros((100, 2), dtype=np.float32) for _ in range(pool_sizes['corner_arrays'])],
                'usage_counters': {key: 0 for key in pool_sizes.keys()},
                'pool_sizes': pool_sizes,
                'memory_strategy': 'aggressive' if memory_aggressive else 'conservative'
            }

            total_memory_mb = self._calculate_pool_memory_usage(memory_pool)
            logger.info(f"Enhanced memory pool initialized: {total_memory_mb:.1f}MB allocated")
            logger.debug(f"Pool sizes: {pool_sizes}")

            return memory_pool

        except Exception as e:
            logger.error(f"Error initializing enhanced memory pool: {str(e)}")
            # Fallback to basic memory pool
            return self._initialize_memory_pool_basic()

    def _calculate_pool_memory_usage(self, memory_pool: Dict[str, Any]) -> float:
        """Calculate total memory usage of the pool in MB."""
        try:
            total_bytes = 0

            for pool_name, arrays in memory_pool.items():
                if isinstance(arrays, list) and arrays:
                    for array in arrays:
                        if hasattr(array, 'nbytes'):
                            total_bytes += array.nbytes

            return total_bytes / (1024 * 1024)  # Convert to MB

        except Exception as e:
            logger.error(f"Error calculating pool memory usage: {str(e)}")
            return 0.0

    def _initialize_memory_pool_basic(self) -> Dict[str, Any]:
        """Fallback basic memory pool initialization."""
        try:
            return {
                'small_arrays': [np.zeros((100, 100), dtype=np.uint8) for _ in range(10)],
                'medium_arrays': [np.zeros((500, 500), dtype=np.uint8) for _ in range(5)],
                'large_arrays': [np.zeros((1000, 1000), dtype=np.uint8) for _ in range(2)],
                'temp_buffers': [np.zeros(1000, dtype=np.float32) for _ in range(10)],
                'usage_counters': {'small_arrays': 0, 'medium_arrays': 0, 'large_arrays': 0, 'temp_buffers': 0},
                'memory_strategy': 'basic'
            }
        except Exception as e:
            logger.error(f"Error initializing basic memory pool: {str(e)}")
            return {'memory_strategy': 'none'}

    def get_hardware_optimized_array(self, shape: Tuple[int, ...], dtype=np.uint8) -> np.ndarray:
        """
        Get optimally allocated array based on hardware capabilities.

        Args:
            shape: Array shape
            dtype: Array data type

        Returns:
            Pre-allocated or new array
        """
        try:
            # Determine array category based on size
            total_elements = np.prod(shape)

            if total_elements <= 10000:  # Small array
                pool_key = 'small_arrays'
            elif total_elements <= 250000:  # Medium array
                pool_key = 'medium_arrays'
            else:  # Large array
                pool_key = 'large_arrays'

            # Try to get from pool
            if pool_key in self.memory_pool and self.memory_pool[pool_key]:
                array = self.memory_pool[pool_key].pop()
                self.memory_pool['usage_counters'][pool_key] += 1

                # Resize if needed
                if array.shape != shape:
                    array = np.resize(array, shape)

                # Convert dtype if needed
                if array.dtype != dtype:
                    array = array.astype(dtype)

                return array
            else:
                # Allocate new array
                return np.zeros(shape, dtype=dtype)

        except Exception as e:
            logger.error(f"Error getting hardware optimized array: {str(e)}")
            return np.zeros(shape, dtype=dtype)

    def return_array_to_pool(self, array: np.ndarray, pool_key: str = None) -> None:
        """
        Return array to memory pool for reuse.

        Args:
            array: Array to return
            pool_key: Specific pool to return to (auto-detected if None)
        """
        try:
            if pool_key is None:
                # Auto-detect pool based on array size
                total_elements = array.size
                if total_elements <= 10000:
                    pool_key = 'small_arrays'
                elif total_elements <= 250000:
                    pool_key = 'medium_arrays'
                else:
                    pool_key = 'large_arrays'

            # Return to pool if there's space
            if (pool_key in self.memory_pool and
                isinstance(self.memory_pool[pool_key], list) and
                len(self.memory_pool[pool_key]) < self.memory_pool['pool_sizes'].get(pool_key, 10)):

                # Clear array data
                array.fill(0)
                self.memory_pool[pool_key].append(array)

        except Exception as e:
            logger.error(f"Error returning array to pool: {str(e)}")
