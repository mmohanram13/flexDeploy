import sys
import os
import asyncio
from pathlib import Path
import json
import random

# Ensure aws-orchestrator/src is importable
root = Path(__file__).resolve().parent
src_dir = str((root / "src").resolve())
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from src.common.config import OrchestratorConfig
from src.master.orchestrator import MasterOrchestrator

# Check if running in AWS Lambda
IS_LAMBDA = "LAMBDA_TASK_ROOT" in os.environ

if IS_LAMBDA:
    try:
        from mangum import Mangum
    except ImportError:
        print("Warning: mangum not installed. Install with: pip install mangum")
        IS_LAMBDA = False

# Install aiohttp in your venv: pip install aiohttp
from aiohttp import web

async def _create_app(master: MasterOrchestrator) -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()

    async def spawn_agent(request):
        sid = master.spawn_agent_random()
        return web.json_response({"agent_id": sid})

    async def add_asset(request):
        try:
            payload = await request.json()
            if not payload:
                return web.json_response({"error": "empty payload"}, status=400)
        except Exception:
            return web.json_response({"error": "invalid json"}, status=400)
        
        # Extract asset info for device metrics if available
        device_metrics = {
            "battery": random.randint(40, 95),
            "cpu": random.uniform(0.5, 2.0),
            "name": payload.get("name", "Unknown Device"),
            "osName": payload.get("osName", "Unknown OS")
        }
        
        # Add device metrics to capabilities
        agent_id = await master.on_asset_added({
            **payload,
            "metrics": device_metrics
        })
        
        # Ensure device status is created
        master._ensure_all_agents_have_device_status()
        
        return web.json_response({
            "agent_id": agent_id,
            "message": "Asset added and agent created with metrics"
        })

    async def submit_task(request):
        try:
            body = await request.json()
            task_type = body.get("task_type")
            parameters = body.get("parameters", {})
            priority = int(body.get("priority", 0))
            if not task_type:
                raise ValueError("task_type required")
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
        task_id = await master.submit_task(task_type, parameters, priority=priority)
        return web.json_response({"task_id": task_id})

    async def list_agents(request):
        return web.json_response({"agents": list(master.agents.keys())})

    async def cluster_status(request):
        status = await master.get_cluster_status()
        return web.json_response(status, dumps=lambda obj: json.dumps(obj, default=str))

    async def task_status(request):
        task_id = request.match_info.get("task_id")
        status = await master.get_task_status(task_id)
        if status is None:
            return web.json_response({"error": "task not found"}, status=404)
        return web.json_response(status, dumps=lambda obj: json.dumps(obj, default=str))

    async def start_deployment(request):
        try:
            body = await request.json()
            deployment_id = body.get("deployment_id")
            if not deployment_id:
                raise ValueError("deployment_id required")
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
        result = await master.start_deployment(deployment_id)
        return web.json_response(result)

    async def complete_deployment(request):
        try:
            body = await request.json()
            deployment_id = body.get("deployment_id")
            if not deployment_id:
                raise ValueError("deployment_id required")
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
        result = await master.complete_deployment(deployment_id)
        return web.json_response(result, dumps=lambda obj: json.dumps(obj, default=str))

    async def deployment_status(request):
        deployment_id = request.rel_url.query.get("deployment_id")
        result = await master.get_deployment_status(deployment_id)
        return web.json_response(result, dumps=lambda obj: json.dumps(obj, default=str))
    
    async def asset_details(request):
        """Get full details of all assets with their associated agents."""
        asset_id = request.rel_url.query.get("asset_id")
        
        # If asset_id provided, return just that asset
        if asset_id:
            for agent_id, asset in master.agent_to_asset.items():
                if asset and asset.get("id") == asset_id:
                    result = {
                        "asset": asset,
                        "agent_id": agent_id,
                        "agent_status": "unknown"
                    }
                    # Add agent status if available
                    if agent_id in master.slaves:
                        result["agent_status"] = master.slaves[agent_id].get("status", "unknown")
                    return web.json_response(result)
            return web.json_response({"error": "asset not found"}, status=404)
        
        # Otherwise return all assets
        all_assets = {}
        for agent_id, asset in master.agent_to_asset.items():
            if asset:
                asset_id = asset.get("id")
                if asset_id:
                    status = "unknown"
                    # Add agent status if available
                    if agent_id in master.slaves:
                        status = master.slaves[agent_id].get("status", "unknown")
                    
                    all_assets[asset_id] = {
                        "asset": asset,
                        "agent_id": agent_id,
                        "agent_status": status
                    }
        
        return web.json_response({"assets": list(all_assets.values())})

    async def simulate_activity(request):
        """Manually trigger agent metric changes for testing."""
        try:
            # First ensure all agents have device status
            master._ensure_all_agents_have_device_status()
            
            # Debug current status
            status_before = {}
            for agent_id, ds in master.device_statuses.items():
                if ds:
                    status_before[agent_id] = {
                        "cpu": ds.cpu_usage,
                        "battery": ds.battery_level,
                        "memory": ds.memory_usage
                    }
            
            # Simulate activity
            affected_agents = await master._simulate_deployment_activity()
            
            # Debug after status
            status_after = {}
            for agent_id in affected_agents:
                ds = master.device_statuses.get(agent_id)
                if ds:
                    status_after[agent_id] = {
                        "cpu": ds.cpu_usage,
                        "battery": ds.battery_level,
                        "memory": ds.memory_usage
                    }
            
            return web.json_response({
                "status": "success", 
                "affected_agents": affected_agents,
                "message": f"Simulated activity on {len(affected_agents)} agents",
                "before": status_before,
                "after": status_after
            })
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return web.json_response({"error": str(e), "traceback": tb}, status=500)

    app.router.add_post("/spawn_agent", spawn_agent)
    app.router.add_post("/add_asset", add_asset)
    app.router.add_post("/submit_task", submit_task)
    app.router.add_get("/list_agents", list_agents)
    app.router.add_get("/cluster_status", cluster_status)
    app.router.add_get("/status/{task_id}", task_status)
    
    # Deployment endpoints
    app.router.add_post("/start_deployment", start_deployment)
    app.router.add_post("/complete_deployment", complete_deployment)
    app.router.add_get("/deployment_status", deployment_status)
    
    # Asset details endpoint
    app.router.add_get("/asset_details", asset_details)
    
    # Simulation endpoint for testing
    app.router.add_post("/simulate_activity", simulate_activity)
    
    return app

async def _start_http_server(app: web.Application, host: str = "0.0.0.0", port: int = 8000):
    """Start aiohttp server (for EC2, ECS, on-premise)."""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"HTTP API running at http://{host}:{port}")
    # Run until cancelled
    await asyncio.Event().wait()

async def main():
    # build config and master
    cfg = OrchestratorConfig()
    # ensure default exists with new value of 2
    if not hasattr(cfg, "default_num_agents"):
        cfg.default_num_agents = 2  # Changed default to 2 agents
    if not hasattr(cfg, "slave_heartbeat_interval"):
        cfg.slave_heartbeat_interval = 5.0
    cfg.master_id = getattr(cfg, "master_id", "master-001")

    master = MasterOrchestrator(cfg)

    # start master message loop in background
    print("Starting master orchestrator (background)...")
    start_task = asyncio.create_task(master.start())

    # spawn default agents
    print(f"Spawning {cfg.default_num_agents} default agents...")
    for _ in range(cfg.default_num_agents):
        master.spawn_agent_random()

    # simulate UI adding an asset which spawns one more agent
    await asyncio.sleep(1.0)
    asset = {
        "id": "5449...048",
        "name": "mmr-10180",
        "site": "HQ",
        "department": "IT"
    }
    print("Simulating asset add from UI (will spawn one agent)...")
    await master.on_asset_added(asset)

    # Create app
    app = await _create_app(master)

    if IS_LAMBDA:
        print("Running in AWS Lambda mode (using mangum adapter)")
        # Return the mangum handler for Lambda
        return Mangum(app)
    else:
        print("Orchestrator is running. HTTP API will accept commands. Agents will continue to run until you stop the process (Ctrl+C).")
        # start HTTP API server and block (EC2, ECS, on-premise)
        await _start_http_server(app, host="0.0.0.0", port=8000)

# For Lambda: export as handler
if IS_LAMBDA:
    async def _init_master():
        cfg = OrchestratorConfig()
        if not hasattr(cfg, "default_num_agents"):
            cfg.default_num_agents = 2  # Changed default to 2 agents
        if not hasattr(cfg, "slave_heartbeat_interval"):
            cfg.slave_heartbeat_interval = 5.0
        cfg.master_id = getattr(cfg, "master_id", "master-001")
        master = MasterOrchestrator(cfg)
        start_task = asyncio.create_task(master.start())
        for _ in range(cfg.default_num_agents):
            master.spawn_agent_random()
        await asyncio.sleep(1.0)
        asset = {
            "id": "5449...048",
            "name": "mmr-10180",
            "site": "HQ",
            "department": "IT"
        }
        await master.on_asset_added(asset)
        return master

    # Create master instance once at Lambda init
    _master_instance = None
    _app_instance = None

    async def lambda_handler(event, context):
        global _master_instance, _app_instance
        if _master_instance is None:
            _master_instance = await _init_master()
            _app_instance = await _create_app(_master_instance)
        handler = Mangum(_app_instance)
        return await handler(event, context)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Process interrupted")