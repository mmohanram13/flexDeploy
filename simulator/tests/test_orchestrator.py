"""Unit tests for the orchestrator system."""

import asyncio
import unittest
from datetime import datetime
from src import (
    MasterOrchestrator,
    SlaveAgent,
    OrchestratorConfig,
    QueueManager,
    TaskStatus,
)


class TestOrchestrator(unittest.TestCase):
    """Test cases for the master-slave orchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = OrchestratorConfig(
            master_id="test-master",
            slave_heartbeat_interval=1,
            slave_timeout=5,
            task_timeout=10,
            use_aws_strands=False
        )
        self.queue_manager = QueueManager(queue_type="memory", maxsize=100)
    
    def test_config_creation(self):
        """Test configuration creation."""
        config = OrchestratorConfig(master_id="test")
        self.assertEqual(config.master_id, "test")
        self.assertEqual(config.slave_heartbeat_interval, 5)
    
    def test_master_initialization(self):
        """Test master orchestrator initialization."""
        master = MasterOrchestrator(self.config)
        self.assertEqual(master.agent_id, "test-master")
        self.assertEqual(len(master.slaves), 0)
        self.assertEqual(len(master.tasks), 0)
        self.assertFalse(master.running)
    
    def test_slave_initialization(self):
        """Test slave agent initialization."""
        slave = SlaveAgent(
            slave_id="test-slave",
            master_id=self.config.master_id,
            capabilities={"tasks": ["test"]},
            config=self.config,
            queue_manager=self.queue_manager
        )
        self.assertEqual(slave.slave_id, "test-slave")
        self.assertEqual(slave.master_id, "test-master")
        self.assertEqual(slave.status, "idle")
        self.assertFalse(slave.running)
    
    def test_task_handler_registration(self):
        """Test task handler registration."""
        slave = SlaveAgent(
            slave_id="test-slave",
            master_id=self.config.master_id,
            capabilities={"tasks": ["test"]},
            config=self.config,
            queue_manager=self.queue_manager
        )
        
        def test_handler(params):
            return {"result": "success"}
        
        slave.register_task_handler("test_task", test_handler)
        self.assertIn("test_task", slave.task_handlers)


class TestAsyncOrchestrator(unittest.IsolatedAsyncioTestCase):
    """Async test cases for the orchestrator."""
    
    async def asyncSetUp(self):
        """Set up async test fixtures."""
        self.config = OrchestratorConfig(
            master_id="test-master",
            slave_heartbeat_interval=1,
            slave_timeout=5,
            task_timeout=10,
            use_aws_strands=False
        )
        self.queue_manager = QueueManager(queue_type="memory", maxsize=100)
    
    async def test_slave_registration(self):
        """Test slave registration with master."""
        master = MasterOrchestrator(self.config)
        master.queue_manager = self.queue_manager
        
        result = await master.register_slave(
            "test-slave",
            {"tasks": ["test"]}
        )
        
        self.assertTrue(result)
        self.assertIn("test-slave", master.slaves)
        self.assertEqual(master.slaves["test-slave"]["status"], "idle")
    
    async def test_task_submission(self):
        """Test task submission."""
        master = MasterOrchestrator(self.config)
        master.queue_manager = self.queue_manager
        
        task_id = await master.submit_task(
            "test_task",
            {"data": [1, 2, 3]},
            priority=1
        )
        
        self.assertIsNotNone(task_id)
        self.assertIn(task_id, master.tasks)
        
        task = master.tasks[task_id]
        self.assertEqual(task.task_type, "test_task")
        self.assertEqual(task.status, TaskStatus.PENDING)
    
    async def test_task_execution_flow(self):
        """Test complete task execution flow."""
        master = MasterOrchestrator(self.config)
        master.queue_manager = self.queue_manager
        
        slave = SlaveAgent(
            slave_id="test-slave",
            master_id=self.config.master_id,
            capabilities={"tasks": ["sum"]},
            config=self.config,
            queue_manager=self.queue_manager
        )
        
        # Register task handler
        async def sum_handler(params):
            data = params.get("data", [])
            return {"result": sum(data)}
        
        slave.register_task_handler("sum", sum_handler)
        
        # Start master and slave
        master_task = asyncio.create_task(master.start())
        slave_task = asyncio.create_task(slave.start())
        
        # Wait for registration
        await asyncio.sleep(1)
        
        # Submit task
        task_id = await master.submit_task(
            "sum",
            {"data": [1, 2, 3, 4, 5]},
            priority=1
        )
        
        # Wait for execution
        await asyncio.sleep(3)
        
        # Check result
        task_status = await master.get_task_status(task_id)
        self.assertIsNotNone(task_status)
        self.assertEqual(task_status["status"], "completed")
        self.assertEqual(task_status["result"]["result"], 15)
        
        # Cleanup
        await master.stop()
        await slave.stop()
        master_task.cancel()
        slave_task.cancel()
        
        try:
            await asyncio.gather(master_task, slave_task)
        except asyncio.CancelledError:
            pass
    
    async def test_cluster_status(self):
        """Test cluster status retrieval."""
        master = MasterOrchestrator(self.config)
        master.queue_manager = self.queue_manager
        
        # Register slave
        await master.register_slave("slave-1", {"tasks": ["test"]})
        
        # Submit tasks
        await master.submit_task("test", {}, priority=1)
        await master.submit_task("test", {}, priority=2)
        
        # Get status
        status = await master.get_cluster_status()
        
        self.assertEqual(status["master_id"], "test-master")
        self.assertEqual(status["total_slaves"], 1)
        self.assertEqual(status["total_tasks"], 2)
        self.assertEqual(status["pending_tasks"], 2)
    
    async def test_multiple_slaves(self):
        """Test orchestration with multiple slaves."""
        master = MasterOrchestrator(self.config)
        master.queue_manager = self.queue_manager
        
        # Create multiple slaves
        slaves = []
        for i in range(3):
            slave = SlaveAgent(
                slave_id=f"slave-{i}",
                master_id=self.config.master_id,
                capabilities={"tasks": ["process"]},
                config=self.config,
                queue_manager=self.queue_manager
            )
            
            async def process_handler(params):
                await asyncio.sleep(0.5)
                return {"processed": True}
            
            slave.register_task_handler("process", process_handler)
            slaves.append(slave)
        
        # Start all agents
        tasks = [asyncio.create_task(master.start())]
        tasks.extend([asyncio.create_task(slave.start()) for slave in slaves])
        
        # Wait for registration
        await asyncio.sleep(1)
        
        # Submit multiple tasks
        task_ids = []
        for i in range(5):
            task_id = await master.submit_task("process", {"id": i})
            task_ids.append(task_id)
        
        # Wait for execution
        await asyncio.sleep(3)
        
        # Check status
        status = await master.get_cluster_status()
        self.assertEqual(status["total_slaves"], 3)
        self.assertGreater(status["completed_tasks"], 0)
        
        # Cleanup
        await master.stop()
        for slave in slaves:
            await slave.stop()
        
        for task in tasks:
            task.cancel()
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass


def run_tests():
    """Run all tests."""
    # Run sync tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOrchestrator)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run async tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAsyncOrchestrator)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
