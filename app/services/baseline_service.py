import math 
from datetime import datetime 
from app.models.infrastructure_schemas import HourStat
from app.db.repositories.baseline_repo import get_static_baseline, update_baseline_stats
from app.models.infrastructure_schemas import NodeMetricBaselineModel
from app.schemas.baseline_dto import BaselineStatsTuned

def calculate_closed_form_KL_variance(p_stats: HourStat, q_stats: HourStat) -> float:
    v_p = max(p_stats.variance, 1e-6)
    v_q = max(q_stats.variance, 1e-6)
    
    term1 = math.log(v_q / v_p)
    term2 = (v_p + (p_stats.mean - q_stats.mean) ** 2) / v_q
    
    return max(0.0, 0.5 * (term1 + term2 - 1.0))

async def get_policy(node_identifier: str, metric_type: str) -> NodeMetricBaselineModel:
    now = datetime.now()
    season_context = 'WEEKDAY' if now.weekday() < 5 else 'WEEKEND'
    policy = await get_static_baseline(node_identifier, metric_type, season_context)
    if not policy:
        raise ValueError(f"No baseline policy found for node '{node_identifier}', metric '{metric_type}', season '{season_context}'")
    return policy

async def evaluate_and_adapt_policy(
    node_identifier: str,
    metric_type: str, 
    observed_mean: float,
    observed_variance: float,
    z_critical_limit: float = 1.645, # 95% confidence interval
    alpha_max: float = 0.5,      
    beta_max: float = 0.1,       
    T_learning: float = 4.0,      
    T_elastic: float = 8.0        
): 
    now = datetime.now()
    hour_key = str(now.hour)
    season = 'WEEKDAY' if now.weekday() < 5 else 'WEEKEND'
    
    policy = await get_policy(node_identifier, metric_type)
    
    hour_stats = policy.baseline_stats.get(hour_key)
    initial_stats = hour_stats.initial
    current_stats = hour_stats.current
    
    observed_stats = HourStat(mean=observed_mean, variance=observed_variance)
    
    current_stats_stddev = math.sqrt(current_stats.variance)
    z_score = (observed_stats.mean - current_stats.mean) / max(current_stats_stddev, 1e-6)
    abs_z = abs(z_score)
    
    if abs_z > z_critical_limit + 1.5:
        deviation_state = 'CRITICAL_ANOMALY'
    elif z_critical_limit < abs_z <= (z_critical_limit + 0.3):
        deviation_state = 'BORDERLINE'
    elif abs_z > z_critical_limit:
        deviation_state = 'ANOMALY'
    else: 
        deviation_state = 'NORMAL'
        
    d_drift = calculate_closed_form_KL_variance(observed_stats, current_stats)
    d_elastic = calculate_closed_form_KL_variance(observed_stats, initial_stats)
    
    alpha = alpha_max * (math.exp(-d_drift / T_learning)) # if d_drift is large, alpha is small, meaning the current stats can not learn from the observed stats, and vice versa
    beta = beta_max * (1 - math.exp(-d_elastic / T_elastic)) # if d_elastic is large, beta is large, meaning we should pull the current stats back to the initial stats, and vice versa
    
    new_mean = current_stats.mean + alpha * (observed_stats.mean - current_stats.mean) - beta * (current_stats.mean - initial_stats.mean)
    new_variance = current_stats.variance + alpha * (observed_stats.variance - current_stats.variance) - beta * (current_stats.variance - initial_stats.variance)
    
    new_mean = max(new_mean, initial_stats.mean * 0.8) 
    
    new_variance = min(new_variance, initial_stats.variance * 2.5)
    new_variance = max(new_variance, initial_stats.variance * 0.2, 4.0)
    
    is_updated_flag = False
    if deviation_state != 'CRITICAL_ANOMALY':
        new_stats = HourStat(mean=new_mean, variance=new_variance)
        update_success = await update_baseline_stats(node_identifier, metric_type, season, hour_key, new_stats)
        
        if not update_success:
            raise RuntimeError(f"Failed to update baseline stats for node '{node_identifier}', metric '{metric_type}', season '{season}', hour '{hour_key}'")
        is_updated_flag = True
    else:
        # Revert to current stats since we are rejecting the update
        new_mean = current_stats.mean
        new_variance = current_stats.variance
    
    return BaselineStatsTuned(
        status="success",
        node_id=node_identifier,
        deviation_state=deviation_state,
        z_score=round(z_score, 2),
        kl_drift=round(d_drift, 2),
        alpha_applied=round(alpha, 2),
        beta_applied=round(beta, 2),
        old_threshold=round(current_stats.mean + z_critical_limit * current_stats_stddev, 2),
        new_mean=round(new_mean, 2),
        new_variance=round(new_variance, 2),
        new_threshold=round(new_mean + z_critical_limit * math.sqrt(new_variance), 2),
        is_updated=is_updated_flag
    )
     
    
            
    