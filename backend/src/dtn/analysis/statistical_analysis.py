"""
Statistical Analysis for DTN Experiments

Provides comprehensive statistical analysis of experiment results including
confidence intervals, significance testing, and performance insights.
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
import logging

logger = logging.getLogger(__name__)


@dataclass
class StatisticalSummary:
    """Statistical summary for a metric."""
    mean: float
    median: float
    std_dev: float
    variance: float
    min_value: float
    max_value: float
    quartile_25: float
    quartile_75: float
    sample_size: int
    confidence_interval_95: Tuple[float, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'mean': self.mean,
            'median': self.median,
            'std_dev': self.std_dev,
            'variance': self.variance,
            'min': self.min_value,
            'max': self.max_value,
            'q25': self.quartile_25,
            'q75': self.quartile_75,
            'sample_size': self.sample_size,
            'confidence_interval_95': {
                'lower': self.confidence_interval_95[0],
                'upper': self.confidence_interval_95[1]
            }
        }


@dataclass
class ComparisonResult:
    """Statistical comparison between two groups."""
    group1_name: str
    group2_name: str
    metric_name: str
    test_statistic: float
    p_value: float
    is_significant: bool
    effect_size: float
    interpretation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'group1': self.group1_name,
            'group2': self.group2_name,
            'metric': self.metric_name,
            'test_statistic': self.test_statistic,
            'p_value': self.p_value,
            'is_significant': self.is_significant,
            'effect_size': self.effect_size,
            'interpretation': self.interpretation
        }


class ExperimentAnalyzer:
    """Comprehensive experiment results analyzer."""
    
    def __init__(self, significance_level: float = 0.05):
        self.alpha = significance_level
    
    def calculate_statistical_summary(self, values: List[float]) -> StatisticalSummary:
        """Calculate comprehensive statistical summary."""
        if not values:
            raise ValueError("Cannot calculate statistics for empty list")
        
        values_array = np.array(values)
        n = len(values)
        
        mean_val = np.mean(values_array)
        median_val = np.median(values_array)
        std_val = np.std(values_array, ddof=1) if n > 1 else 0.0
        var_val = np.var(values_array, ddof=1) if n > 1 else 0.0
        
        min_val = np.min(values_array)
        max_val = np.max(values_array)
        q25 = np.percentile(values_array, 25)
        q75 = np.percentile(values_array, 75)
        
        # Calculate 95% confidence interval for the mean
        if n > 1:
            se = std_val / math.sqrt(n)
            t_critical = stats.t.ppf(1 - self.alpha/2, df=n-1)
            margin_error = t_critical * se
            ci_lower = mean_val - margin_error
            ci_upper = mean_val + margin_error
        else:
            ci_lower = ci_upper = mean_val
        
        return StatisticalSummary(
            mean=mean_val,
            median=median_val,
            std_dev=std_val,
            variance=var_val,
            min_value=min_val,
            max_value=max_val,
            quartile_25=q25,
            quartile_75=q75,
            sample_size=n,
            confidence_interval_95=(ci_lower, ci_upper)
        )
    
    def compare_two_groups(
        self,
        group1_values: List[float],
        group2_values: List[float],
        group1_name: str,
        group2_name: str,
        metric_name: str,
        test_type: str = "auto"
    ) -> ComparisonResult:
        """Compare two groups statistically."""
        
        if not group1_values or not group2_values:
            raise ValueError("Both groups must have values for comparison")
        
        group1_array = np.array(group1_values)
        group2_array = np.array(group2_values)
        
        # Choose appropriate test
        if test_type == "auto":
            if len(group1_values) >= 30 and len(group2_values) >= 30:
                test_type = "t_test"  # Large samples, use t-test
            else:
                # Check normality for small samples
                _, p1 = stats.shapiro(group1_array) if len(group1_array) <= 50 else (0, 0.1)
                _, p2 = stats.shapiro(group2_array) if len(group2_array) <= 50 else (0, 0.1)
                
                if p1 > 0.05 and p2 > 0.05:
                    test_type = "t_test"
                else:
                    test_type = "mannwhitney"
        
        # Perform the test
        if test_type == "t_test":
            # Independent samples t-test
            test_stat, p_value = stats.ttest_ind(group1_array, group2_array)
            
            # Calculate Cohen's d for effect size
            pooled_std = math.sqrt(((len(group1_array) - 1) * np.var(group1_array, ddof=1) + 
                                  (len(group2_array) - 1) * np.var(group2_array, ddof=1)) / 
                                 (len(group1_array) + len(group2_array) - 2))
            
            effect_size = (np.mean(group1_array) - np.mean(group2_array)) / pooled_std
            
        elif test_type == "mannwhitney":
            # Mann-Whitney U test (non-parametric)
            test_stat, p_value = stats.mannwhitneyu(group1_array, group2_array, 
                                                   alternative='two-sided')
            
            # Calculate rank-biserial correlation for effect size
            n1, n2 = len(group1_array), len(group2_array)
            u1 = test_stat
            u2 = n1 * n2 - u1
            effect_size = 1 - (2 * min(u1, u2)) / (n1 * n2)
            
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        
        # Determine significance
        is_significant = p_value < self.alpha
        
        # Generate interpretation
        interpretation = self._interpret_comparison(
            group1_name, group2_name, metric_name,
            np.mean(group1_array), np.mean(group2_array),
            p_value, effect_size, is_significant
        )
        
        return ComparisonResult(
            group1_name=group1_name,
            group2_name=group2_name,
            metric_name=metric_name,
            test_statistic=test_stat,
            p_value=p_value,
            is_significant=is_significant,
            effect_size=effect_size,
            interpretation=interpretation
        )
    
    def _interpret_comparison(
        self,
        group1_name: str,
        group2_name: str,
        metric_name: str,
        mean1: float,
        mean2: float,
        p_value: float,
        effect_size: float,
        is_significant: bool
    ) -> str:
        """Generate human-readable interpretation."""
        
        # Effect size interpretation
        abs_effect = abs(effect_size)
        if abs_effect < 0.2:
            effect_desc = "negligible"
        elif abs_effect < 0.5:
            effect_desc = "small"
        elif abs_effect < 0.8:
            effect_desc = "medium"
        else:
            effect_desc = "large"
        
        # Determine which group is better
        if metric_name in ["delivery_ratio", "throughput", "success_rate"]:
            # Higher is better
            better_group = group1_name if mean1 > mean2 else group2_name
            improvement = abs(mean1 - mean2) / min(mean1, mean2) * 100
        else:
            # Lower is better (delay, overhead, etc.)
            better_group = group1_name if mean1 < mean2 else group2_name
            improvement = abs(mean1 - mean2) / max(mean1, mean2) * 100
        
        if is_significant:
            interpretation = (f"{better_group} shows statistically significant improvement "
                            f"in {metric_name} (p={p_value:.4f}, effect size: {effect_desc}). "
                            f"Performance improvement: {improvement:.1f}%.")
        else:
            interpretation = (f"No statistically significant difference in {metric_name} "
                            f"between {group1_name} and {group2_name} "
                            f"(p={p_value:.4f}, effect size: {effect_desc}).")
        
        return interpretation
    
    def analyze_trend(
        self,
        x_values: List[float],
        y_values: List[float],
        x_name: str,
        y_name: str
    ) -> Dict[str, Any]:
        """Analyze trend in data (e.g., performance vs buffer size)."""
        
        if len(x_values) != len(y_values) or len(x_values) < 3:
            return {"error": "Insufficient data for trend analysis"}
        
        # Calculate correlation
        correlation, p_value = stats.pearsonr(x_values, y_values)
        
        # Linear regression
        slope, intercept, r_value, p_reg, std_err = stats.linregress(x_values, y_values)
        
        # Determine trend strength
        if abs(correlation) < 0.3:
            strength = "weak"
        elif abs(correlation) < 0.7:
            strength = "moderate"
        else:
            strength = "strong"
        
        # Determine direction
        if correlation > 0:
            direction = "positive"
            trend_desc = f"{y_name} increases as {x_name} increases"
        else:
            direction = "negative"
            trend_desc = f"{y_name} decreases as {x_name} increases"
        
        return {
            'correlation': correlation,
            'correlation_p_value': p_value,
            'is_significant': p_value < self.alpha,
            'strength': strength,
            'direction': direction,
            'trend_description': trend_desc,
            'linear_regression': {
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value ** 2,
                'p_value': p_reg,
                'std_error': std_err
            }
        }
    
    def perform_anova(
        self,
        groups: Dict[str, List[float]],
        metric_name: str
    ) -> Dict[str, Any]:
        """Perform one-way ANOVA for multiple groups."""
        
        if len(groups) < 2:
            return {"error": "Need at least 2 groups for ANOVA"}
        
        group_values = list(groups.values())
        group_names = list(groups.keys())
        
        # Perform one-way ANOVA
        f_statistic, p_value = stats.f_oneway(*group_values)
        
        is_significant = p_value < self.alpha
        
        # Calculate eta-squared (effect size for ANOVA)
        all_values = np.concatenate(group_values)
        grand_mean = np.mean(all_values)
        
        ss_between = sum(len(group) * (np.mean(group) - grand_mean)**2 
                        for group in group_values)
        ss_total = sum((value - grand_mean)**2 for value in all_values)
        
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        # Post-hoc analysis if significant
        post_hoc_results = []
        if is_significant and len(groups) > 2:
            # Pairwise comparisons with Bonferroni correction
            alpha_corrected = self.alpha / (len(groups) * (len(groups) - 1) / 2)
            
            for i, (name1, values1) in enumerate(groups.items()):
                for j, (name2, values2) in enumerate(groups.items()):
                    if i < j:  # Avoid duplicate comparisons
                        comparison = self.compare_two_groups(
                            values1, values2, name1, name2, metric_name
                        )
                        # Apply Bonferroni correction
                        comparison.is_significant = comparison.p_value < alpha_corrected
                        post_hoc_results.append(comparison.to_dict())
        
        return {
            'f_statistic': f_statistic,
            'p_value': p_value,
            'is_significant': is_significant,
            'eta_squared': eta_squared,
            'groups_tested': len(groups),
            'total_samples': len(all_values),
            'post_hoc_comparisons': post_hoc_results,
            'interpretation': self._interpret_anova(
                metric_name, groups, f_statistic, p_value, eta_squared, is_significant
            )
        }
    
    def _interpret_anova(
        self,
        metric_name: str,
        groups: Dict[str, List[float]],
        f_stat: float,
        p_value: float,
        eta_squared: float,
        is_significant: bool
    ) -> str:
        """Interpret ANOVA results."""
        
        # Effect size interpretation
        if eta_squared < 0.01:
            effect_desc = "negligible"
        elif eta_squared < 0.06:
            effect_desc = "small"
        elif eta_squared < 0.14:
            effect_desc = "medium"
        else:
            effect_desc = "large"
        
        if is_significant:
            # Find best performing group
            group_means = {name: np.mean(values) for name, values in groups.items()}
            
            if metric_name in ["delivery_ratio", "throughput", "success_rate"]:
                best_group = max(group_means.keys(), key=lambda k: group_means[k])
            else:
                best_group = min(group_means.keys(), key=lambda k: group_means[k])
            
            interpretation = (f"Statistically significant difference in {metric_name} "
                            f"across groups (F={f_stat:.3f}, p={p_value:.4f}). "
                            f"Effect size: {effect_desc} (η²={eta_squared:.3f}). "
                            f"Best performing group: {best_group}.")
        else:
            interpretation = (f"No statistically significant difference in {metric_name} "
                            f"across groups (F={f_stat:.3f}, p={p_value:.4f}). "
                            f"Effect size: {effect_desc}.")
        
        return interpretation


def analyze_experiment_comprehensively(experiment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform comprehensive analysis of experiment results."""
    
    analyzer = ExperimentAnalyzer()
    analysis_results = {
        'summary_statistics': {},
        'group_comparisons': [],
        'trend_analyses': [],
        'anova_results': {},
        'key_insights': [],
        'recommendations': []
    }
    
    if not experiment_results:
        return {"error": "No experiment results to analyze"}
    
    # Extract metrics
    metrics = ['delivery_ratio', 'average_delay', 'network_overhead']
    
    # Group results by experiment parameter
    has_buffer_size = any('buffer_size' in result for result in experiment_results)
    has_ttl = any('ttl_seconds' in result for result in experiment_results)
    has_algorithm = any('algorithm' in result for result in experiment_results)
    
    try:
        # Summary statistics for each metric
        for metric in metrics:
            values = [result['metrics'][metric] for result in experiment_results 
                     if metric in result['metrics']]
            
            if values:
                analysis_results['summary_statistics'][metric] = \
                    analyzer.calculate_statistical_summary(values).to_dict()
        
        # Buffer size analysis
        if has_buffer_size:
            buffer_groups = {}
            for result in experiment_results:
                buffer_label = result.get('buffer_label', 'unknown')
                if buffer_label not in buffer_groups:
                    buffer_groups[buffer_label] = {metric: [] for metric in metrics}
                
                for metric in metrics:
                    if metric in result['metrics']:
                        buffer_groups[buffer_label][metric].append(result['metrics'][metric])
            
            # Perform ANOVA for each metric across buffer sizes
            for metric in metrics:
                metric_groups = {label: values[metric] for label, values in buffer_groups.items() 
                               if values[metric]}
                
                if len(metric_groups) > 1:
                    anova_result = analyzer.perform_anova(metric_groups, metric)
                    analysis_results['anova_results'][f'buffer_size_{metric}'] = anova_result
            
            # Trend analysis for buffer size vs performance
            buffer_sizes = []
            delivery_ratios = []
            delays = []
            overheads = []
            
            for result in experiment_results:
                if 'buffer_size' in result:
                    buffer_sizes.append(result['buffer_size'] / (1024 * 1024))  # Convert to MB
                    if 'delivery_ratio' in result['metrics']:
                        delivery_ratios.append(result['metrics']['delivery_ratio'])
                    if 'average_delay' in result['metrics']:
                        delays.append(result['metrics']['average_delay'])
                    if 'network_overhead' in result['metrics']:
                        overheads.append(result['metrics']['network_overhead'])
            
            if buffer_sizes and delivery_ratios:
                trend = analyzer.analyze_trend(buffer_sizes, delivery_ratios, 
                                             'Buffer Size (MB)', 'Delivery Ratio')
                analysis_results['trend_analyses'].append({
                    'parameter': 'buffer_size',
                    'metric': 'delivery_ratio',
                    **trend
                })
        
        # Algorithm comparison analysis
        if has_algorithm:
            algorithm_groups = {}
            for result in experiment_results:
                algorithm = result.get('algorithm', 'unknown')
                if algorithm not in algorithm_groups:
                    algorithm_groups[algorithm] = {metric: [] for metric in metrics}
                
                for metric in metrics:
                    if metric in result['metrics']:
                        algorithm_groups[algorithm][metric].append(result['metrics'][metric])
            
            # Pairwise comparisons between algorithms
            algorithm_names = list(algorithm_groups.keys())
            for i, alg1 in enumerate(algorithm_names):
                for j, alg2 in enumerate(algorithm_names):
                    if i < j:  # Avoid duplicate comparisons
                        for metric in metrics:
                            if (algorithm_groups[alg1][metric] and 
                                algorithm_groups[alg2][metric]):
                                
                                comparison = analyzer.compare_two_groups(
                                    algorithm_groups[alg1][metric],
                                    algorithm_groups[alg2][metric],
                                    alg1, alg2, metric
                                )
                                analysis_results['group_comparisons'].append(comparison.to_dict())
        
        # Generate key insights
        insights = _generate_insights(analysis_results, has_buffer_size, has_ttl, has_algorithm)
        analysis_results['key_insights'] = insights
        
        # Generate recommendations
        recommendations = _generate_recommendations(analysis_results, experiment_results)
        analysis_results['recommendations'] = recommendations
        
    except Exception as e:
        logger.error(f"Error in statistical analysis: {e}")
        analysis_results['error'] = str(e)
    
    return analysis_results


def _generate_insights(
    analysis: Dict[str, Any],
    has_buffer_size: bool,
    has_ttl: bool,
    has_algorithm: bool
) -> List[str]:
    """Generate key insights from analysis results."""
    insights = []
    
    # Buffer size insights
    if has_buffer_size and 'buffer_size_delivery_ratio' in analysis['anova_results']:
        anova = analysis['anova_results']['buffer_size_delivery_ratio']
        if anova['is_significant']:
            insights.append("Buffer size has a statistically significant impact on delivery ratio")
    
    # Algorithm performance insights
    significant_comparisons = [
        comp for comp in analysis['group_comparisons']
        if comp['is_significant'] and comp['metric'] == 'delivery_ratio'
    ]
    
    if significant_comparisons:
        insights.append(f"Found {len(significant_comparisons)} significant differences in routing algorithm performance")
    
    # Trend insights
    for trend in analysis['trend_analyses']:
        if trend['is_significant']:
            insights.append(f"{trend['trend_description']} (correlation: {trend['correlation']:.3f})")
    
    # Performance variability insights
    for metric, stats in analysis['summary_statistics'].items():
        cv = stats['std_dev'] / stats['mean'] if stats['mean'] > 0 else 0
        if cv > 0.2:
            insights.append(f"High variability observed in {metric} (CV: {cv:.2f})")
    
    return insights


def _generate_recommendations(
    analysis: Dict[str, Any],
    experiment_results: List[Dict[str, Any]]
) -> List[str]:
    """Generate actionable recommendations."""
    recommendations = []
    
    # Buffer size recommendations
    buffer_comparisons = [
        comp for comp in analysis['group_comparisons']
        if 'MB' in comp['group1'] or 'MB' in comp['group2']
    ]
    
    if buffer_comparisons:
        # Find the best performing buffer size
        best_performance = max(buffer_comparisons, 
                             key=lambda x: x['effect_size'] if x['is_significant'] else 0)
        if best_performance['is_significant']:
            recommendations.append(f"Consider using larger buffer sizes for better performance based on significant improvements observed")
    
    # Algorithm recommendations
    algo_comparisons = [
        comp for comp in analysis['group_comparisons']
        if comp['metric'] == 'delivery_ratio' and comp['is_significant']
    ]
    
    if algo_comparisons:
        best_algo_comparison = max(algo_comparisons, key=lambda x: x['effect_size'])
        recommendations.append(f"For delivery ratio optimization, consider the algorithm comparison results showing significant differences")
    
    # Performance trade-off recommendations
    if analysis['summary_statistics']:
        recommendations.append("Monitor the trade-off between delivery ratio and network overhead when selecting optimal configurations")
    
    return recommendations