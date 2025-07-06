"""
Comprehensive test suite for basketball court detection validation.

This module provides a complete testing framework for validating all phases
of court detection development with automated test execution and reporting.
"""

import numpy as np
import cv2
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .accuracy_metrics import AccuracyMetrics, AccuracyResult
from .performance_metrics import PerformanceBenchmark, PerformanceResult

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """Container for individual test case data."""
    name: str
    frame: np.ndarray
    ground_truth_corners: List[Tuple[float, float]]
    expected_confidence: float
    difficulty_level: str  # 'easy', 'medium', 'hard'
    court_type: str  # 'indoor', 'outdoor'
    lighting_condition: str  # 'good', 'poor', 'variable'

@dataclass
class TestResult:
    """Container for test execution results."""
    test_case_name: str
    accuracy_result: AccuracyResult
    performance_result: PerformanceResult
    passed: bool
    failure_reason: Optional[str] = None

class CourtDetectionTestSuite:
    """
    Comprehensive test suite for basketball court detection validation.
    
    This class provides automated testing capabilities for all phases of
    court detection development with detailed reporting and analysis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize test suite.
        
        Args:
            config: Configuration dictionary with test parameters
        """
        self.config = config or {}
        
        # Test configuration
        self.min_iou_threshold = self.config.get('min_iou_threshold', 0.5)
        self.min_corner_accuracy = self.config.get('min_corner_accuracy', 0.75)
        self.max_processing_time_ms = self.config.get('max_processing_time_ms', 100.0)
        self.min_success_rate = self.config.get('min_success_rate', 0.8)
        
        # Initialize metrics calculators
        self.accuracy_metrics = AccuracyMetrics(config.get('accuracy_config', {}))
        self.performance_benchmark = PerformanceBenchmark(config.get('performance_config', {}))
        
        # Test data
        self.test_cases = []
        self.test_results = []
        
        logger.info("CourtDetectionTestSuite initialized successfully")
    
    def load_test_cases(self, test_data_path: str) -> bool:
        """
        Load test cases from directory or configuration file.
        
        Args:
            test_data_path: Path to test data directory or config file
            
        Returns:
            True if test cases loaded successfully
        """
        try:
            test_path = Path(test_data_path)
            
            if test_path.is_file() and test_path.suffix == '.json':
                # Load from JSON configuration
                return self._load_test_cases_from_json(test_path)
            elif test_path.is_dir():
                # Load from directory structure
                return self._load_test_cases_from_directory(test_path)
            else:
                # Generate synthetic test cases
                return self._generate_synthetic_test_cases()
                
        except Exception as e:
            logger.error(f"Error loading test cases: {str(e)}")
            return False
    
    def _generate_synthetic_test_cases(self) -> bool:
        """Generate synthetic test cases for testing."""
        try:
            logger.info("Generating synthetic test cases...")
            
            # Generate different types of synthetic court images
            test_cases = [
                self._create_synthetic_test_case("simple_court", "easy", "indoor", "good"),
                self._create_synthetic_test_case("noisy_court", "medium", "outdoor", "poor"),
                self._create_synthetic_test_case("distorted_court", "hard", "indoor", "variable"),
                self._create_synthetic_test_case("low_contrast", "hard", "outdoor", "poor"),
                self._create_synthetic_test_case("high_contrast", "easy", "indoor", "good")
            ]
            
            self.test_cases = test_cases
            logger.info(f"Generated {len(test_cases)} synthetic test cases")
            return True
            
        except Exception as e:
            logger.error(f"Error generating synthetic test cases: {str(e)}")
            return False
    
    def _create_synthetic_test_case(self, name: str, difficulty: str, 
                                   court_type: str, lighting: str) -> TestCase:
        """Create a synthetic test case with known ground truth."""
        try:
            # Create synthetic court image
            height, width = 480, 640
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Define court corners based on difficulty
            if difficulty == "easy":
                corners = [(100, 100), (540, 100), (540, 380), (100, 380)]
                expected_confidence = 0.9
            elif difficulty == "medium":
                corners = [(80, 120), (560, 90), (580, 360), (120, 390)]
                expected_confidence = 0.7
            else:  # hard
                corners = [(60, 140), (580, 80), (600, 340), (140, 400)]
                expected_confidence = 0.5
            
            # Draw court outline
            court_points = np.array(corners, dtype=np.int32)
            cv2.polylines(frame, [court_points], True, (255, 255, 255), 2)
            
            # Add court features (center circle, free throw lines, etc.)
            center_x = int(np.mean([c[0] for c in corners]))
            center_y = int(np.mean([c[1] for c in corners]))
            cv2.circle(frame, (center_x, center_y), 30, (255, 255, 255), 2)
            
            # Add noise based on difficulty and lighting
            if difficulty != "easy" or lighting == "poor":
                noise = np.random.randint(0, 50, frame.shape, dtype=np.uint8)
                frame = cv2.add(frame, noise)
            
            # Adjust brightness based on lighting condition
            if lighting == "poor":
                frame = cv2.convertScaleAbs(frame, alpha=0.5, beta=-30)
            elif lighting == "variable":
                # Add gradient lighting
                gradient = np.linspace(0.3, 1.0, width).reshape(1, -1, 1)
                frame = (frame * gradient).astype(np.uint8)
            
            return TestCase(
                name=name,
                frame=frame,
                ground_truth_corners=corners,
                expected_confidence=expected_confidence,
                difficulty_level=difficulty,
                court_type=court_type,
                lighting_condition=lighting
            )
            
        except Exception as e:
            logger.error(f"Error creating synthetic test case: {str(e)}")
            # Return minimal test case
            return TestCase(
                name=name,
                frame=np.zeros((480, 640, 3), dtype=np.uint8),
                ground_truth_corners=[(0, 0), (640, 0), (640, 480), (0, 480)],
                expected_confidence=0.5,
                difficulty_level=difficulty,
                court_type=court_type,
                lighting_condition=lighting
            )
    
    def run_comprehensive_test(self, detector_func: callable, 
                             test_name: str = "comprehensive_test") -> Dict[str, Any]:
        """
        Run comprehensive test suite on a detection method.
        
        Args:
            detector_func: Court detection function to test
            test_name: Name for this test run
            
        Returns:
            Dictionary with comprehensive test results
        """
        try:
            logger.info(f"Starting comprehensive test: {test_name}")
            
            if not self.test_cases:
                logger.warning("No test cases loaded, generating synthetic cases")
                self._generate_synthetic_test_cases()
            
            # Reset previous results
            self.test_results = []
            self.accuracy_metrics.reset_history()
            self.performance_benchmark.reset_history()
            
            # Run tests on each test case
            for test_case in self.test_cases:
                logger.debug(f"Running test case: {test_case.name}")
                
                try:
                    # Measure performance
                    start_time = time.perf_counter()
                    detection_result = detector_func(test_case.frame)
                    end_time = time.perf_counter()
                    
                    processing_time_ms = (end_time - start_time) * 1000
                    
                    # Extract corners from detection result
                    if hasattr(detection_result, 'corners') and detection_result.corners:
                        predicted_corners = detection_result.corners
                        confidence_score = getattr(detection_result, 'confidence_score', 0.0)
                        method_name = getattr(detection_result, 'detection_method', 'unknown')
                    else:
                        predicted_corners = []
                        confidence_score = 0.0
                        method_name = 'failed'
                    
                    # Calculate accuracy metrics
                    accuracy_result = self.accuracy_metrics.calculate_comprehensive_accuracy(
                        predicted_corners,
                        test_case.ground_truth_corners,
                        confidence_score,
                        method_name
                    )
                    
                    # Create performance result
                    performance_result = PerformanceResult(
                        method_name=method_name,
                        processing_time_ms=processing_time_ms,
                        memory_usage_mb=0.0,  # Would need more complex monitoring
                        cpu_usage_percent=0.0,
                        peak_memory_mb=0.0,
                        throughput_fps=1000.0 / processing_time_ms if processing_time_ms > 0 else 0.0,
                        frame_count=1,
                        success_rate=1.0 if len(predicted_corners) >= 4 else 0.0
                    )
                    
                    # Determine if test passed
                    passed = self._evaluate_test_result(accuracy_result, performance_result, test_case)
                    failure_reason = None if passed else self._get_failure_reason(accuracy_result, performance_result, test_case)
                    
                    # Store test result
                    test_result = TestResult(
                        test_case_name=test_case.name,
                        accuracy_result=accuracy_result,
                        performance_result=performance_result,
                        passed=passed,
                        failure_reason=failure_reason
                    )
                    
                    self.test_results.append(test_result)
                    
                except Exception as e:
                    logger.error(f"Error in test case {test_case.name}: {str(e)}")
                    # Create failed test result
                    failed_result = TestResult(
                        test_case_name=test_case.name,
                        accuracy_result=AccuracyResult(
                            iou_score=0.0, corner_accuracy=0.0, aspect_ratio_error=1.0,
                            geometric_validity=False, confidence_score=0.0,
                            processing_time_ms=0.0, method_name="error",
                            additional_metrics={}
                        ),
                        performance_result=PerformanceResult(
                            method_name="error", processing_time_ms=0.0,
                            memory_usage_mb=0.0, cpu_usage_percent=0.0,
                            peak_memory_mb=0.0, throughput_fps=0.0,
                            frame_count=0, success_rate=0.0
                        ),
                        passed=False,
                        failure_reason=f"Exception: {str(e)}"
                    )
                    self.test_results.append(failed_result)
            
            # Generate comprehensive report
            report = self._generate_test_report(test_name)
            
            logger.info(f"Comprehensive test completed: {test_name}")
            logger.info(f"Overall pass rate: {report['overall_pass_rate']:.3f}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error in comprehensive test: {str(e)}")
            return {'error': str(e)}
    
    def run_phase_comparison_test(self, phase_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run comparison test across different development phases.
        
        Args:
            phase_configs: Dictionary mapping phase names to configurations
            
        Returns:
            Dictionary with phase comparison results
        """
        try:
            from ..court_detector import CourtDetector
            
            logger.info("Starting phase comparison test")
            
            if not self.test_cases:
                self._generate_synthetic_test_cases()
            
            phase_results = {}
            
            for phase_name, config in phase_configs.items():
                logger.info(f"Testing phase: {phase_name}")
                
                # Create detector for this phase
                detector = CourtDetector(config)
                
                # Run comprehensive test
                phase_result = self.run_comprehensive_test(
                    detector.detect_court,
                    f"phase_{phase_name}"
                )
                
                phase_results[phase_name] = phase_result
                
                # Cleanup
                if hasattr(detector, 'cleanup_all_components'):
                    detector.cleanup_all_components()
            
            # Generate comparison report
            comparison_report = self._generate_phase_comparison_report(phase_results)
            
            logger.info("Phase comparison test completed")
            return comparison_report
            
        except Exception as e:
            logger.error(f"Error in phase comparison test: {str(e)}")
            return {'error': str(e)}
    
    def _evaluate_test_result(self, accuracy_result: AccuracyResult, 
                             performance_result: PerformanceResult,
                             test_case: TestCase) -> bool:
        """Evaluate if test result meets acceptance criteria."""
        try:
            # Check accuracy criteria
            if accuracy_result.iou_score < self.min_iou_threshold:
                return False
            
            if accuracy_result.corner_accuracy < self.min_corner_accuracy:
                return False
            
            # Check performance criteria
            if performance_result.processing_time_ms > self.max_processing_time_ms:
                return False
            
            # Check geometric validity
            if not accuracy_result.geometric_validity:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating test result: {str(e)}")
            return False
    
    def _get_failure_reason(self, accuracy_result: AccuracyResult, 
                           performance_result: PerformanceResult,
                           test_case: TestCase) -> str:
        """Get detailed failure reason for failed test."""
        reasons = []
        
        if accuracy_result.iou_score < self.min_iou_threshold:
            reasons.append(f"IoU too low: {accuracy_result.iou_score:.3f} < {self.min_iou_threshold}")
        
        if accuracy_result.corner_accuracy < self.min_corner_accuracy:
            reasons.append(f"Corner accuracy too low: {accuracy_result.corner_accuracy:.3f} < {self.min_corner_accuracy}")
        
        if performance_result.processing_time_ms > self.max_processing_time_ms:
            reasons.append(f"Processing too slow: {performance_result.processing_time_ms:.1f}ms > {self.max_processing_time_ms}ms")
        
        if not accuracy_result.geometric_validity:
            reasons.append("Invalid geometry detected")
        
        return "; ".join(reasons) if reasons else "Unknown failure"

    def _generate_test_report(self, test_name: str) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        try:
            if not self.test_results:
                return {'error': 'No test results available'}

            # Calculate overall statistics
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r.passed)
            overall_pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0

            # Accuracy statistics
            iou_scores = [r.accuracy_result.iou_score for r in self.test_results]
            corner_accuracies = [r.accuracy_result.corner_accuracy for r in self.test_results]
            processing_times = [r.performance_result.processing_time_ms for r in self.test_results]

            # Breakdown by difficulty
            difficulty_breakdown = {}
            for test_case in self.test_cases:
                difficulty = test_case.difficulty_level
                if difficulty not in difficulty_breakdown:
                    difficulty_breakdown[difficulty] = {'total': 0, 'passed': 0}

                difficulty_breakdown[difficulty]['total'] += 1

                # Find corresponding result
                result = next((r for r in self.test_results if r.test_case_name == test_case.name), None)
                if result and result.passed:
                    difficulty_breakdown[difficulty]['passed'] += 1

            # Calculate pass rates by difficulty
            for difficulty in difficulty_breakdown:
                total = difficulty_breakdown[difficulty]['total']
                passed = difficulty_breakdown[difficulty]['passed']
                difficulty_breakdown[difficulty]['pass_rate'] = passed / total if total > 0 else 0.0

            report = {
                'test_name': test_name,
                'timestamp': time.time(),
                'overall_statistics': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': total_tests - passed_tests,
                    'overall_pass_rate': overall_pass_rate
                },
                'accuracy_statistics': {
                    'mean_iou': np.mean(iou_scores),
                    'std_iou': np.std(iou_scores),
                    'min_iou': np.min(iou_scores),
                    'max_iou': np.max(iou_scores),
                    'mean_corner_accuracy': np.mean(corner_accuracies),
                    'std_corner_accuracy': np.std(corner_accuracies)
                },
                'performance_statistics': {
                    'mean_processing_time_ms': np.mean(processing_times),
                    'std_processing_time_ms': np.std(processing_times),
                    'min_processing_time_ms': np.min(processing_times),
                    'max_processing_time_ms': np.max(processing_times),
                    'mean_throughput_fps': 1000.0 / np.mean(processing_times) if np.mean(processing_times) > 0 else 0.0
                },
                'difficulty_breakdown': difficulty_breakdown,
                'failed_tests': [
                    {
                        'test_name': r.test_case_name,
                        'failure_reason': r.failure_reason,
                        'iou_score': r.accuracy_result.iou_score,
                        'corner_accuracy': r.accuracy_result.corner_accuracy,
                        'processing_time_ms': r.performance_result.processing_time_ms
                    }
                    for r in self.test_results if not r.passed
                ],
                'detailed_results': [
                    {
                        'test_name': r.test_case_name,
                        'passed': r.passed,
                        'iou_score': r.accuracy_result.iou_score,
                        'corner_accuracy': r.accuracy_result.corner_accuracy,
                        'processing_time_ms': r.performance_result.processing_time_ms,
                        'confidence_score': r.accuracy_result.confidence_score,
                        'geometric_validity': r.accuracy_result.geometric_validity
                    }
                    for r in self.test_results
                ]
            }

            return report

        except Exception as e:
            logger.error(f"Error generating test report: {str(e)}")
            return {'error': str(e)}

    def _generate_phase_comparison_report(self, phase_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate phase comparison report."""
        try:
            comparison_report = {
                'timestamp': time.time(),
                'phases_tested': list(phase_results.keys()),
                'phase_summary': {},
                'performance_comparison': {},
                'accuracy_comparison': {},
                'recommendations': []
            }

            # Extract key metrics for each phase
            for phase_name, phase_result in phase_results.items():
                if 'error' in phase_result:
                    comparison_report['phase_summary'][phase_name] = {'error': phase_result['error']}
                    continue

                overall_stats = phase_result.get('overall_statistics', {})
                accuracy_stats = phase_result.get('accuracy_statistics', {})
                performance_stats = phase_result.get('performance_statistics', {})

                comparison_report['phase_summary'][phase_name] = {
                    'pass_rate': overall_stats.get('overall_pass_rate', 0.0),
                    'mean_iou': accuracy_stats.get('mean_iou', 0.0),
                    'mean_corner_accuracy': accuracy_stats.get('mean_corner_accuracy', 0.0),
                    'mean_processing_time_ms': performance_stats.get('mean_processing_time_ms', 0.0),
                    'mean_throughput_fps': performance_stats.get('mean_throughput_fps', 0.0)
                }

            # Generate recommendations
            if len(comparison_report['phase_summary']) > 1:
                # Find best performing phase
                best_accuracy_phase = max(
                    comparison_report['phase_summary'].items(),
                    key=lambda x: x[1].get('mean_iou', 0.0) if 'error' not in x[1] else 0.0
                )[0]

                best_performance_phase = max(
                    comparison_report['phase_summary'].items(),
                    key=lambda x: x[1].get('mean_throughput_fps', 0.0) if 'error' not in x[1] else 0.0
                )[0]

                comparison_report['recommendations'] = [
                    f"Best accuracy: {best_accuracy_phase}",
                    f"Best performance: {best_performance_phase}"
                ]

            return comparison_report

        except Exception as e:
            logger.error(f"Error generating phase comparison report: {str(e)}")
            return {'error': str(e)}

    def export_test_results(self, filepath: str) -> bool:
        """Export test results to file."""
        try:
            if not self.test_results:
                logger.warning("No test results to export")
                return False

            # Generate comprehensive report
            report = self._generate_test_report("exported_results")

            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Test results exported to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error exporting test results: {str(e)}")
            return False

    def get_test_summary(self) -> Dict[str, Any]:
        """Get quick test summary."""
        try:
            if not self.test_results:
                return {'message': 'No test results available'}

            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r.passed)

            return {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'pass_rate': passed_tests / total_tests if total_tests > 0 else 0.0,
                'test_cases_loaded': len(self.test_cases)
            }

        except Exception as e:
            logger.error(f"Error getting test summary: {str(e)}")
            return {'error': str(e)}
