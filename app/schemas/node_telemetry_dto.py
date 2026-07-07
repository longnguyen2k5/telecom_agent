from pydantic import BaseModel, Field

class NodeTelemetryOutput(BaseModel): 
    node_identifier: str = Field(..., description="Unique identifier for the node")
    metric_type: str = Field(..., description="Type of metric (e.g., 'cpu_usage', 'ram_usage')")
    window_minutes: int = Field(..., description="Time window in minutes for which telemetry data is considered")
    sample_count: int = Field(..., description="Number of samples collected in the specified time window")
    observed_mean: float = Field(..., description="Mean value of the observed metric")
    observed_variance: float = Field(..., description="Variance of the observed metric")
    