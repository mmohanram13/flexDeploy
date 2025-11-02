"""
Pydantic models for FlexDeploy API
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Device(BaseModel):
    """Device model"""
    device_id: str
    device_name: str
    manufacturer: str
    model: str
    os_name: str
    site: str
    department: str
    ring: int
    total_memory: str
    total_storage: str
    network_speed: str
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_disk_space: float
    risk_score: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Ring(BaseModel):
    """Ring configuration model"""
    ring_id: int
    ring_name: str
    categorization_prompt: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GatingFactors(BaseModel):
    """Gating factors model"""
    avg_cpu_usage_max: Optional[float] = None
    avg_memory_usage_max: Optional[float] = None
    avg_disk_free_space_min: Optional[float] = None
    risk_score_min: Optional[int] = None
    risk_score_max: Optional[int] = None


class Deployment(BaseModel):
    """Deployment model"""
    deployment_id: str
    deployment_name: str
    status: str  # Not Started, In Progress, Completed, Failed, Stopped
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DeploymentRing(BaseModel):
    """Deployment ring status model"""
    ring_id: int
    ring_name: str
    device_count: int
    status: str  # Not Started, In Progress, Completed, Failed, Stopped
    failure_reason: Optional[str] = None


class DeploymentDetail(BaseModel):
    """Detailed deployment information"""
    deployment_id: str
    deployment_name: str
    status: str
    rings: List[DeploymentRing]
    gating_factors: Optional[GatingFactors] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DashboardMetrics(BaseModel):
    """Dashboard metrics model"""
    total_devices: int
    total_deployments: int
    active_rings: int


class RingDistribution(BaseModel):
    """Ring device distribution model"""
    name: str
    value: int
