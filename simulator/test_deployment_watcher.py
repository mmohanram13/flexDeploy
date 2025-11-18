"""Test script to verify deployment watcher functionality."""

import asyncio
import logging
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

from src.common.config import OrchestratorConfig
from src.master.orchestrator import MasterOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deployment_watcher_test.log')
    ]
)

logger = logging.getLogger(__name__)


async def test_deployment_watcher():
    """Test the deployment watcher functionality."""
    logger.info("=" * 80)
    logger.info("DEPLOYMENT WATCHER TEST STARTED")
    logger.info("=" * 80)
    
    # Create config
    config = OrchestratorConfig()
    config.default_num_agents = 3
    config.slave_heartbeat_interval = 5.0
    
    # Create orchestrator
    master = MasterOrchestrator(config)
    
    # Load devices and start orchestrator in background
    await master.device_manager.load_devices_from_db()
    await master.ring_manager.load_ring_configurations()
    
    logger.info(f"Loaded {len(master.device_manager.device_cache)} devices")
    
    # Spawn some agents
    for i in range(config.default_num_agents):
        agent_id = master.spawn_agent_random()
        logger.info(f"Spawned agent: {agent_id}")
    
    # Start background tasks
    master.running = True
    watcher_task = asyncio.create_task(
        master.deployment_manager.deployment_watcher_loop(lambda: master.running)
    )
    
    logger.info("Watcher task started")
    logger.info("Waiting for deployments to process...")
    logger.info("The watcher will auto-start any 'Not Started' deployments")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Run for 2 minutes to observe deployment progress
        await asyncio.sleep(120)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    finally:
        logger.info("Stopping orchestrator...")
        master.running = False
        
        # Wait for watcher to finish
        try:
            await asyncio.wait_for(watcher_task, timeout=5.0)
        except asyncio.TimeoutError:
            watcher_task.cancel()
        
        logger.info("=" * 80)
        logger.info("DEPLOYMENT WATCHER TEST COMPLETED")
        logger.info("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_deployment_watcher())
    except KeyboardInterrupt:
        print("\nTest stopped by user")
