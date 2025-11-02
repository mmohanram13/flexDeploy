"""Integration example: Using the orchestrator with FlexDeploy deployment system."""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict
from src import (
    MasterOrchestrator,
    SlaveAgent,
    OrchestratorConfig,
    QueueManager,
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# FlexDeploy-specific task handlers

async def analyze_device_risk(parameters: dict) -> dict:
    """Analyze risk score for devices before deployment."""
    devices = parameters.get("devices", [])
    
    logger.info(f"Analyzing risk for {len(devices)} devices")
    
    risk_analysis = []
    for device in devices:
        # Calculate risk score based on device metrics
        cpu_risk = device.get("cpu_usage", 0) * 0.3
        memory_risk = device.get("memory_usage", 0) * 0.3
        history_risk = device.get("failure_rate", 0) * 0.4
        
        risk_score = round(cpu_risk + memory_risk + history_risk, 2)
        
        # Determine ring assignment
        if risk_score < 30:
            ring = 1  # Low Risk
        elif risk_score < 60:
            ring = 2  # Medium Risk
        elif risk_score < 80:
            ring = 3  # High Risk
        else:
            ring = 4  # VIP (highest scrutiny)
        
        risk_analysis.append({
            "device_id": device["id"],
            "device_name": device["name"],
            "risk_score": risk_score,
            "recommended_ring": ring,
            "reasoning": f"CPU: {cpu_risk:.1f}, Memory: {memory_risk:.1f}, History: {history_risk:.1f}"
        })
    
    return {
        "total_devices": len(devices),
        "analysis": risk_analysis,
        "timestamp": datetime.now().isoformat()
    }


async def execute_ring_deployment(parameters: dict) -> dict:
    """Execute deployment to a specific ring of devices."""
    ring_id = parameters.get("ring_id")
    devices = parameters.get("devices", [])
    package = parameters.get("package")
    
    logger.info(f"Deploying {package} to Ring {ring_id} ({len(devices)} devices)")
    
    results = []
    successful = 0
    failed = 0
    
    for device in devices:
        # Simulate deployment
        await asyncio.sleep(0.5)
        
        # Higher risk devices have higher failure probability
        risk_score = device.get("risk_score", 50)
        success = risk_score < 85  # Devices with >85 risk score likely to fail
        
        if success:
            successful += 1
            status = "success"
        else:
            failed += 1
            status = "failed"
        
        results.append({
            "device_id": device["id"],
            "device_name": device["name"],
            "status": status,
            "deployment_time": "12s" if success else "timeout"
        })
    
    return {
        "ring_id": ring_id,
        "package": package,
        "total_devices": len(devices),
        "successful": successful,
        "failed": failed,
        "success_rate": round((successful / len(devices)) * 100, 2) if devices else 0,
        "results": results
    }


async def monitor_ring_health(parameters: dict) -> dict:
    """Monitor health metrics after deployment."""
    deployment_id = parameters.get("deployment_id")
    ring_id = parameters.get("ring_id")
    devices = parameters.get("devices", [])
    
    logger.info(f"Monitoring Ring {ring_id} health for deployment {deployment_id}")
    
    await asyncio.sleep(1)
    
    # Simulate health monitoring
    anomalies = []
    for device in devices:
        # Check for anomalies
        cpu_spike = device.get("cpu_usage", 0) > 75
        memory_spike = device.get("memory_usage", 0) > 80
        
        if cpu_spike or memory_spike:
            anomalies.append({
                "device_id": device["id"],
                "device_name": device["name"],
                "anomaly": "CPU spike" if cpu_spike else "Memory spike",
                "value": device.get("cpu_usage" if cpu_spike else "memory_usage")
            })
    
    anomaly_rate = (len(anomalies) / len(devices)) * 100 if devices else 0
    recommendation = "pause" if anomaly_rate > 10 else "continue"
    
    return {
        "deployment_id": deployment_id,
        "ring_id": ring_id,
        "total_devices": len(devices),
        "anomalies_detected": len(anomalies),
        "anomaly_rate": round(anomaly_rate, 2),
        "recommendation": recommendation,
        "anomalies": anomalies[:5],  # Return first 5 anomalies
        "health_status": "unhealthy" if anomaly_rate > 10 else "healthy"
    }


async def generate_deployment_report(parameters: dict) -> dict:
    """Generate comprehensive deployment report."""
    deployment_id = parameters.get("deployment_id")
    rings_data = parameters.get("rings", [])
    
    logger.info(f"Generating report for deployment {deployment_id}")
    
    await asyncio.sleep(1)
    
    total_devices = sum(r.get("total_devices", 0) for r in rings_data)
    total_successful = sum(r.get("successful", 0) for r in rings_data)
    total_failed = sum(r.get("failed", 0) for r in rings_data)
    
    report = {
        "deployment_id": deployment_id,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_devices": total_devices,
            "successful": total_successful,
            "failed": total_failed,
            "success_rate": round((total_successful / total_devices) * 100, 2) if total_devices else 0
        },
        "rings": rings_data,
        "recommendations": []
    }
    
    # Add recommendations based on results
    if total_failed > 0:
        report["recommendations"].append(
            "Review failed devices and consider reassignment to lower risk rings"
        )
    
    if report["summary"]["success_rate"] < 95:
        report["recommendations"].append(
            "Success rate below threshold. Investigate root causes before proceeding"
        )
    
    return report


async def main():
    """FlexDeploy integration example."""
    
    logger.info("=" * 80)
    logger.info("FlexDeploy Orchestrator Integration Example")
    logger.info("=" * 80)
    
    # Configuration
    config = OrchestratorConfig(
        master_id="flexdeploy-master",
        slave_heartbeat_interval=5,
        task_timeout=120,
        use_aws_strands=False  # Set to True with AWS credentials
    )
    
    queue_manager = QueueManager(queue_type="memory", maxsize=200)
    
    # Create master
    master = MasterOrchestrator(config)
    master.queue_manager = queue_manager
    
    # Create specialized slave agents
    risk_analyzer = SlaveAgent(
        slave_id="risk-analyzer-001",
        master_id=config.master_id,
        capabilities={
            "tasks": ["analyze_risk"],
            "specialization": "risk_assessment"
        },
        config=config,
        queue_manager=queue_manager
    )
    risk_analyzer.register_task_handler("analyze_risk", analyze_device_risk)
    
    deployment_executor_1 = SlaveAgent(
        slave_id="executor-001",
        master_id=config.master_id,
        capabilities={
            "tasks": ["deploy_ring", "monitor_health"],
            "specialization": "deployment"
        },
        config=config,
        queue_manager=queue_manager
    )
    deployment_executor_1.register_task_handler("deploy_ring", execute_ring_deployment)
    deployment_executor_1.register_task_handler("monitor_health", monitor_ring_health)
    
    deployment_executor_2 = SlaveAgent(
        slave_id="executor-002",
        master_id=config.master_id,
        capabilities={
            "tasks": ["deploy_ring", "monitor_health"],
            "specialization": "deployment"
        },
        config=config,
        queue_manager=queue_manager
    )
    deployment_executor_2.register_task_handler("deploy_ring", execute_ring_deployment)
    deployment_executor_2.register_task_handler("monitor_health", monitor_ring_health)
    
    report_generator = SlaveAgent(
        slave_id="report-generator-001",
        master_id=config.master_id,
        capabilities={
            "tasks": ["generate_report"],
            "specialization": "reporting"
        },
        config=config,
        queue_manager=queue_manager
    )
    report_generator.register_task_handler("generate_report", generate_deployment_report)
    
    # Start all agents
    logger.info("\nStarting orchestrator cluster...")
    tasks = [
        asyncio.create_task(master.start()),
        asyncio.create_task(risk_analyzer.start()),
        asyncio.create_task(deployment_executor_1.start()),
        asyncio.create_task(deployment_executor_2.start()),
        asyncio.create_task(report_generator.start())
    ]
    
    await asyncio.sleep(2)
    
    # Simulated device data (similar to FlexDeploy UI mock data)
    devices = [
        {"id": f"device-{i:03d}", "name": f"LAPTOP-{i:03d}", "cpu_usage": 20 + i*3, 
         "memory_usage": 30 + i*2, "failure_rate": i*2}
        for i in range(50)
    ]
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Starting Deployment Pipeline for {len(devices)} devices")
    logger.info(f"{'='*80}")
    
    # Phase 1: Risk Analysis
    logger.info("\n[Phase 1] Analyzing device risk scores...")
    risk_task_id = await master.submit_task(
        "analyze_risk",
        {"devices": devices},
        priority=10
    )
    
    await asyncio.sleep(2)
    
    risk_result = await master.get_task_status(risk_task_id)
    if risk_result and risk_result.get("result"):
        analysis = risk_result["result"]["analysis"]
        logger.info(f"Risk analysis complete: {len(analysis)} devices analyzed")
        
        # Group devices by ring
        rings = {0: [], 1: [], 2: [], 3: [], 4: []}
        for device_analysis in analysis:
            ring = device_analysis["recommended_ring"]
            device_id = device_analysis["device_id"]
            device = next(d for d in devices if d["id"] == device_id)
            device["risk_score"] = device_analysis["risk_score"]
            rings[ring].append(device)
        
        logger.info(f"Ring distribution: R0={len(rings[0])}, R1={len(rings[1])}, "
                   f"R2={len(rings[2])}, R3={len(rings[3])}, R4={len(rings[4])}")
    
    # Phase 2: Deploy to rings in sequence
    logger.info("\n[Phase 2] Executing ring-based deployment...")
    
    ring_results = []
    for ring_id in [0, 1, 2]:  # Deploy to Ring 0, 1, 2
        if not rings[ring_id]:
            continue
        
        logger.info(f"\nDeploying to Ring {ring_id} ({len(rings[ring_id])} devices)...")
        
        deploy_task_id = await master.submit_task(
            "deploy_ring",
            {
                "ring_id": ring_id,
                "devices": rings[ring_id],
                "package": "KB5043145"
            },
            priority=9 - ring_id
        )
        
        await asyncio.sleep(3)
        
        deploy_result = await master.get_task_status(deploy_task_id)
        if deploy_result and deploy_result.get("result"):
            result_data = deploy_result["result"]
            ring_results.append(result_data)
            logger.info(f"Ring {ring_id}: {result_data['successful']}/{result_data['total_devices']} "
                       f"successful ({result_data['success_rate']}%)")
            
            # Phase 3: Monitor ring health
            if result_data["successful"] > 0:
                logger.info(f"Monitoring Ring {ring_id} health...")
                
                monitor_task_id = await master.submit_task(
                    "monitor_health",
                    {
                        "deployment_id": "D-1003",
                        "ring_id": ring_id,
                        "devices": rings[ring_id]
                    },
                    priority=8
                )
                
                await asyncio.sleep(2)
                
                monitor_result = await master.get_task_status(monitor_task_id)
                if monitor_result and monitor_result.get("result"):
                    health = monitor_result["result"]
                    logger.info(f"Ring {ring_id} health: {health['health_status']} "
                               f"(Anomaly rate: {health['anomaly_rate']}%)")
                    
                    if health["recommendation"] == "pause":
                        logger.warning(f"⚠️  AI recommends pausing deployment at Ring {ring_id}")
                        logger.warning(f"Detected {health['anomalies_detected']} anomalies")
                        break
    
    # Phase 4: Generate report
    logger.info("\n[Phase 4] Generating deployment report...")
    
    report_task_id = await master.submit_task(
        "generate_report",
        {
            "deployment_id": "D-1003",
            "rings": ring_results
        },
        priority=5
    )
    
    await asyncio.sleep(2)
    
    report_result = await master.get_task_status(report_task_id)
    if report_result and report_result.get("result"):
        report = report_result["result"]
        logger.info(f"\n{'='*80}")
        logger.info("Deployment Report")
        logger.info(f"{'='*80}")
        logger.info(f"Deployment ID: {report['deployment_id']}")
        logger.info(f"Total Devices: {report['summary']['total_devices']}")
        logger.info(f"Successful: {report['summary']['successful']}")
        logger.info(f"Failed: {report['summary']['failed']}")
        logger.info(f"Success Rate: {report['summary']['success_rate']}%")
        
        if report["recommendations"]:
            logger.info("\nRecommendations:")
            for rec in report["recommendations"]:
                logger.info(f"  • {rec}")
    
    # Final cluster status
    logger.info(f"\n{'='*80}")
    logger.info("Final Cluster Status")
    logger.info(f"{'='*80}")
    
    cluster_status = await master.get_cluster_status()
    logger.info(f"Master: {cluster_status['master_id']}")
    logger.info(f"Total Slaves: {cluster_status['total_slaves']}")
    logger.info(f"Active: {cluster_status['active_slaves']}, Idle: {cluster_status['idle_slaves']}")
    logger.info(f"Tasks Completed: {cluster_status['completed_tasks']}/{cluster_status['total_tasks']}")
    
    # Shutdown
    logger.info(f"\n{'='*80}")
    logger.info("Shutting down orchestrator")
    logger.info(f"{'='*80}")
    
    await master.stop()
    await risk_analyzer.stop()
    await deployment_executor_1.stop()
    await deployment_executor_2.stop()
    await report_generator.stop()
    
    for task in tasks:
        task.cancel()
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    
    logger.info("\n✅ FlexDeploy orchestrator example completed!")


if __name__ == "__main__":
    asyncio.run(main())
