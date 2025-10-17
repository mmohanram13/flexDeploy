import asyncio

def add_asset(orchestrator, asset: dict):
	"""
	Called by the UI layer when a new asset is added.
	This schedules an async call to the orchestrator to spawn/trigger an agent.
	"""
	loop = asyncio.get_event_loop()
	# fire-and-forget; if caller wants the result they can await orchestrator.on_asset_added directly
	loop.create_task(orchestrator.on_asset_added(asset))
	print("[UI] asset add requested, agent spawn scheduled")