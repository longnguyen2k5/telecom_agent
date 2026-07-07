from pydantic import BaseModel
from typing import Literal


class BaselineStatsTuned(BaseModel): 
    status: str =  "success"
    node_id: str
    deviation_state: Literal['CRITICAL_ANOMALY', 'ANOMALY', 'BORDERLINE', 'NORMAL']
    z_score: float
    kl_drift: float
    alpha_applied: float
    beta_applied: float
    old_threshold: float
    new_mean: float
    new_variance: float
    new_threshold: float
    is_updated: bool