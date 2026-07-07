from app.db.mongodb import get_database
from app.models.infrastructure_schemas import NodeMetricBaselineModel, HourStat, BaselineHourStats
from datetime import datetime

METRIC_BLUEPRINTS = {
    "cpu_usage": {
        "low_hours": (0, 1, 2, 3, 4, 5, 6, 23),   
        "high_hours": (9, 10, 11, 14, 15, 16, 17, 19, 20, 21, 22), 
        "low_stat": HourStat(mean=15.0, variance=16.0),  
        "high_stat": HourStat(mean=85.0, variance=36.0)
    },
    "ram_usage": {
        "default_stat": HourStat(mean=55.0, variance=2.25) 
    }
}

def generate_default_baseline(metric_type: str) -> dict[str, BaselineHourStats]:
    if metric_type not in METRIC_BLUEPRINTS:
        raise ValueError(f"Unknown metric type: {metric_type}")
    
    blueprint = METRIC_BLUEPRINTS[metric_type]
    default_stats = {}
    
    for hour in range(24):
        hour_key = str(hour)
        if metric_type == "cpu_usage":
            if hour in blueprint["low_hours"]:
                stat = blueprint["low_stat"]
            elif hour in blueprint["high_hours"]:
                stat = blueprint["high_stat"]
            else:
                stat = HourStat(mean=50.0, variance=16.0)  # Trung bình
        elif metric_type == "ram_usage":
            stat = blueprint["default_stat"]
        
        default_stats[hour_key] = BaselineHourStats(initial=stat, current=stat)
    
    return default_stats


async def get_static_baseline(node_identifier: str, metric_type: str, season_context: str) -> NodeMetricBaselineModel:
    db = get_database()
    query = {
        "node_identifier": node_identifier,
        "metric_type": metric_type,
        "season_context": season_context
    }
    raw_doc = await db["node_metric_baseline"].find_one(query)
    if not raw_doc:
        raise ValueError(f"No baseline found for node '{node_identifier}', metric '{metric_type}', season '{season_context}'")
    return NodeMetricBaselineModel(**raw_doc)


async def update_baseline_stats(node_identifier: str, metric_type: str, season_context: str, hour_key: str, new_stats: HourStat) -> bool:
    db = get_database()
    query = {
        'node_identifier': node_identifier,
        'metric_type': metric_type,
        'season_context': season_context
    }
    update = {
        '$set': {
            f'baseline_stats.{hour_key}.current': new_stats.model_dump(),
            f'baseline_stats.{hour_key}.last_updated': datetime.now().isoformat()
        }
    }
    result = await db["node_metric_baseline"].update_one(query, update)
    
    if result.matched_count == 0: 
        hour_stats = generate_default_baseline(metric_type)
        hour_stats[hour_key].current = new_stats
        
        fallback_model = NodeMetricBaselineModel(
            node_identifier=node_identifier,
            metric_type=metric_type,
            season_context=season_context,
            baseline_stats=hour_stats
        )
        await db["node_metric_baseline"].insert_one(fallback_model.model_dump())
        return True
    return result.modified_count > 0