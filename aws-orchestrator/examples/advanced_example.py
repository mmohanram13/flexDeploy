"""Advanced example with AWS Strands integration."""

import asyncio
import logging
from src import (
    MasterOrchestrator,
    SlaveAgent,
    OrchestratorConfig,
    QueueManager,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Advanced task handlers with AI integration
async def ai_analyze_deployment_risk(parameters: dict) -> dict:
    """AI-powered deployment risk analysis."""
    devices = parameters.get("devices", [])
    deployment_config = parameters.get("config", {})
    
    logger.info(f"Analyzing deployment risk for {len(devices)} devices")
    await asyncio.sleep(2)  # Simulate AI processing
    
    # Simulate risk assessment
    risk_scores = {}
    for device in devices:
        risk_score = (device.get("cpu_usage", 0) * 0.3 + 
                     device.get("memory_usage", 0) * 0.3 +
                     device.get("failure_rate", 0) * 0.4)
        risk_scores[device["id"]] = round(risk_score, 2)
    
    return {
        "risk_scores": risk_scores,
        "total_devices": len(devices),
        "high_risk_count": sum(1 for score in risk_scores.values() if score > 70)
    }


async def ai_optimize_deployment_strategy(parameters: dict) -> dict:
    """AI-powered deployment strategy optimization."""
    rings = parameters.get("rings", [])
    devices = parameters.get("devices", [])
    
    logger.info(f"Optimizing deployment strategy for {len(rings)} rings")
    await asyncio.sleep(3)  # Simulate AI processing
    
    # Simulate strategy optimization
    strategy = {
        "ring_assignments": {},
        "deployment_order": [],
        "estimated_duration": 0
    }
    
    for i, ring in enumerate(rings):
        ring_id = ring["id"]
        strategy["deployment_order"].append(ring_id)
        strategy["ring_assignments"][ring_id] = {
            "devices": len(devices) // len(rings),
            "wait_time": ring.get("wait_time", 15),
            "max_failures": ring.get("max_failures", 2)
        }
    
    strategy["estimated_duration"] = sum(
        r.get("wait_time", 15) for r in rings
    )
    
    return strategy


async def monitor_deployment_health(parameters: dict) -> dict:
    """Monitor deployment health metrics."""
    deployment_id = parameters.get("deployment_id")
    ring_id = parameters.get("ring_id")
    
    logger.info(f"Monitoring deployment {deployment_id} at ring {ring_id}")
    await asyncio.sleep(1.5)
    
    # Simulate health monitoring
    health_metrics = {
        "deployment_id": deployment_id,
        "ring_id": ring_id,
        "status": "healthy",
        "metrics": {
            "success_rate": 98.5,
            "avg_cpu_delta": 2.3,
            "avg_memory_delta": 5.1,
            "failures": 1,
            "anomalies": 0
        },
        "recommendation": "proceed"
    }
    
    return health_metrics


async def execute_deployment_task(parameters: dict) -> dict:
    """Execute actual deployment on devices."""
    devices = parameters.get("devices", [])
    package = parameters.get("package", "unknown")
    
    logger.info(f"Deploying {package} to {len(devices)} devices")
    await asyncio.sleep(2)
    
    # Simulate deployment
    results = []
    for device in devices:
        success = device.get("risk_score", 50) < 80  # Higher risk = more likely to fail
        results.append({
            "device_id": device["id"],
            "status": "success" if success else "failed",
            "duration": 10 + (device.get("risk_score", 0) / 10)
        })
    
    success_count = sum(1 for r in results if r["status"] == "success")
    
    return {
        "package": package,
        "total_devices": len(devices),
        "successful": success_count,
        "failed": len(devices) - success_count,
        "results": results
    }


async def main():
    """Advanced example with AI-powered orchestration."""
    
    # Create configuration with AWS Strands enabled
    config = OrchestratorConfig(
        master_id="master-ai-001",
        slave_heartbeat_interval=5,
        task_timeout=120,
        use_aws_strands=False,  # Set to True if AWS credentials are configured
        strands_model="amazon.nova-act-v1:0"
    )
    
    # Create shared queue manager
    queue_manager = QueueManager(queue_type="memory", maxsize=200)
    
    # Create master orchestrator
    master = MasterOrchestrator(config)
    master.queue_manager = queue_manager
    
    # Create specialized slave agents
    risk_analyzer = SlaveAgent(
        slave_id="slave-risk-analyzer",
        master_id=config.master_id,
        capabilities={"tasks": ["ai_analyze_risk"], "specialization": "risk_assessment"},
        config=config,
        queue_manager=queue_manager
    )
    
    strategy_optimizer = SlaveAgent(
        slave_id="slave-strategy-optimizer",
        master_id=config.master_id,
        capabilities={"tasks": ["ai_optimize_strategy"], "specialization": "optimization"},
        config=config,
        queue_manager=queue_manager
    )
    
    deployment_executor = SlaveAgent(
        slave_id="slave-deployment-executor",
        master_id=config.master_id,
        capabilities={"tasks": ["execute_deployment", "monitor_health"], "specialization": "execution"},
        config=config,
        queue_manager=queue_manager
    )
    
    # Register task handlers
    risk_analyzer.register_task_handler("ai_analyze_risk", ai_analyze_deployment_risk)
    strategy_optimizer.register_task_handler("ai_optimize_strategy", ai_optimize_deployment_strategy)
    deployment_executor.register_task_handler("execute_deployment", execute_deployment_task)
    deployment_executor.register_task_handler("monitor_health", monitor_deployment_health)
    
    logger.info("=" * 80)
    logger.info("Advanced AI-Powered Orchestrator Example")
    logger.info("=" * 80)
    
    # Start agents
    master_task = asyncio.create_task(master.start())
    risk_task = asyncio.create_task(risk_analyzer.start())
    strategy_task = asyncio.create_task(strategy_optimizer.start())
    executor_task = asyncio.create_task(deployment_executor.start())
    
    # Wait for registration
    await asyncio.sleep(2)
    
    logger.info("\n" + "=" * 80)
    logger.info("Simulating AI-Powered Deployment Pipeline")
    logger.info("=" * 80)
    
    # Simulated device data
    devices = [
        {"id": f"device-{i:03d}", "cpu_usage": 30 + i*2, "memory_usage": 40 + i, "failure_rate": i*5}
        for i in range(10)
    ]
    
    rings = [
        {"id": 0, "name": "Canary", "wait_time": 30, "max_failures": 0},
        {"id": 1, "name": "Low Risk", "wait_time": 120, "max_failures": 2},
        {"id": 2, "name": "Medium Risk", "wait_time": 240, "max_failures": 5},
    ]
    
    # Step 1: Analyze deployment risk
    logger.info("\n[Step 1] Analyzing deployment risk...")
    risk_task_id = await master.submit_task(
        "ai_analyze_risk",
        {"devices": devices, "config": {"package": "KB5043145"}},
        priority=10
    )
    
    await asyncio.sleep(3)
    
    risk_result = await master.get_task_status(risk_task_id)
    if risk_result and risk_result.get("result"):
        logger.info(f"Risk Analysis Complete: {risk_result['result']}")
    
    # Step 2: Optimize deployment strategy
    logger.info("\n[Step 2] Optimizing deployment strategy...")
    strategy_task_id = await master.submit_task(
        "ai_optimize_strategy",
        {"rings": rings, "devices": devices},
        priority=9
    )
    
    await asyncio.sleep(4)
    
    strategy_result = await master.get_task_status(strategy_task_id)
    if strategy_result and strategy_result.get("result"):
        logger.info(f"Strategy Optimization Complete: {strategy_result['result']}")
    
    # Step 3: Execute deployment
    logger.info("\n[Step 3] Executing deployment...")
    deployment_task_id = await master.submit_task(
        "execute_deployment",
        {"devices": devices[:5], "package": "KB5043145"},
        priority=8
    )
    
    await asyncio.sleep(3)
    
    deployment_result = await master.get_task_status(deployment_task_id)
    if deployment_result and deployment_result.get("result"):
        logger.info(f"Deployment Complete: {deployment_result['result']}")
    
    # Step 4: Monitor deployment health
    logger.info("\n[Step 4] Monitoring deployment health...")
    monitor_task_id = await master.submit_task(
        "monitor_health",
        {"deployment_id": "D-1003", "ring_id": 0},
        priority=7
    )
    
    await asyncio.sleep(2)
    
    monitor_result = await master.get_task_status(monitor_task_id)
    if monitor_result and monitor_result.get("result"):
        logger.info(f"Health Monitoring Complete: {monitor_result['result']}")
    
    # Final status
    logger.info("\n" + "=" * 80)
    logger.info("Final Cluster Status")
    logger.info("=" * 80)
    
    status = await master.get_cluster_status()
    logger.info(f"\nMaster: {status['master_id']}")
    logger.info(f"Slaves: {status['total_slaves']} (Active: {status['active_slaves']}, Idle: {status['idle_slaves']})")
    logger.info(f"Tasks: {status['completed_tasks']}/{status['total_tasks']} completed")
    
    # Shutdown
    logger.info("\n" + "=" * 80)
    logger.info("Shutting down")
    logger.info("=" * 80)
    
    await master.stop()
    await risk_analyzer.stop()
    await strategy_optimizer.stop()
    await deployment_executor.stop()
    
    # Cancel tasks
    for task in [master_task, risk_task, strategy_task, executor_task]:
        task.cancel()
    
    try:
        await asyncio.gather(master_task, risk_task, strategy_task, executor_task)
    except asyncio.CancelledError:
        pass
    
    logger.info("\nAdvanced example completed!")


if __name__ == "__main__":
    asyncio.run(main())
