"""Configuration settings for the orchestrator."""

from dataclasses import dataclass, field
from typing import Optional
import uuid
import random


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator system."""
    
    # Master configuration
    master_id: str = "master-orchestrator"
    master_host: str = "localhost"
    master_port: int = 8080
    
    # Slave configuration
    default_num_agents: int = 2  # Changed from 5 to 2
    slave_heartbeat_interval: float = 5.0
    slave_max_retries: int = 3
    slave_timeout: float = 20.0
    
    # Task configuration
    task_queue_size: int = 1000
    task_retry_limit: int = 3
    task_timeout: float = 60.0
    
    # Communication
    message_queue_type: str = "memory"  # Options: memory, redis, sqs
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    aws_region: Optional[str] = None
    sqs_queue_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # AWS Strands configuration
    use_aws_strands: bool = True  # Changed to True since AWS credentials are available
    strands_model: str = "amazon.nova-act-v1:0"
    strands_max_tokens: int = 4096
    
    @classmethod
    def from_dict(cls, config: dict) -> "OrchestratorConfig":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in config.items() if k in cls.__annotations__})
    
    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            k: getattr(self, k)
            for k in self.__annotations__
        }
    
    def random_agent_details(self) -> dict:
        """Return a small random details dict for a spawned agent."""
        slave_id = f"slave-{uuid.uuid4().hex[:8]}"
        capabilities = {
            "tasks": random.sample(
                ["process_data", "health_check", "deploy", "analyze_risk", "monitor"], 
                k=random.randint(1, 3)
            ),
            "battery": random.randint(20, 100),
            "cpu": round(random.uniform(0.1, 2.0), 2),
        }
        return {
            "slave_id": slave_id,
            "capabilities": capabilities
        }


# Default configuration
DEFAULT_CONFIG = OrchestratorConfig()
