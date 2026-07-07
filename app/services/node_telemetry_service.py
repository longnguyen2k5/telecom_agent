from app.db.repositories.node_telemetry_repo import get_node_telemetry
from app.schemas.node_telemetry_dto import NodeTelemetryOutput
import math

async def calculate_telemetry_distribution(
    node_identifier: str, 
    metric_type: str, 
    window_minutes: int = 60
): 
    raw_logs = await get_node_telemetry(node_identifier, window_minutes)
    
    if not raw_logs:
        raise ValueError("No telemetry data found for the specified parameters.")

    metrics_list = [] 
    for log in raw_logs: 
        if getattr(log, 'metrics', None):
            value = getattr(log.metrics, metric_type, None)
            if value is not None: 
                metrics_list.append(value)
            
    n = len(metrics_list)
    if n < 2: 
        raise ValueError("Not enough data points to calculate distribution.")

    observed_mean = sum(metrics_list) / n
    
    if n >= 30: 
        temp_mean = observed_mean
        temp_variance = sum((x - temp_mean) ** 2 for x in metrics_list) / (n - 1)
        temp_std = math.sqrt(max(temp_variance, 1e-6))
        
        filtered_metrics = [x for x in metrics_list if (abs(x - temp_mean) / temp_std) <= 2.5]
        if len(filtered_metrics) >= 2:
            metrics_list = filtered_metrics
            n = len(metrics_list)
            observed_mean = sum(metrics_list) / n
        
    sum_squared_diff = sum((x - observed_mean) ** 2 for x in metrics_list)
    observed_variance = sum_squared_diff / (n - 1)
    
    MAX_LAB_VARIANCE = 36.0  
    MIN_LAB_VARIANCE = 4.0 
    
    if observed_variance > MAX_LAB_VARIANCE:
        observed_variance = MAX_LAB_VARIANCE
    elif observed_variance < MIN_LAB_VARIANCE:
        observed_variance = MIN_LAB_VARIANCE
        
    return NodeTelemetryOutput(
        node_identifier=node_identifier,
        metric_type=metric_type,
        window_minutes=window_minutes,
        sample_count=n,
        observed_mean=round(observed_mean, 2),
        observed_variance=round(observed_variance, 4)
    )
    