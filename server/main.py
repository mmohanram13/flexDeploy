"""
FastAPI server for FlexDeploy - AI Deployment Orchestrator
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import uvicorn

from server.database import Database
from server.config import get_config
from server.bedrock_agents import (
    get_bedrock_service,
    RingCategorizationAgent,
    DeploymentFailureAgent,
    GatingFactorAgent
)
from server.simulator_service import SimulatorService
from server.database import populate_default_data


# Initialize FastAPI app
app = FastAPI(title="FlexDeploy API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
import os
# Use flexdeploy.db from the root directory
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "flexdeploy.db")
db = Database(db_path)

# Initialize Bedrock agents
bedrock_service = None
ring_categorization_agent = None
deployment_failure_agent = None
gating_factor_agent = None

# Initialize simulator service
simulator_service = None


@app.on_event("startup")
async def startup_event():
    """Connect to database on startup"""
    global bedrock_service, ring_categorization_agent, deployment_failure_agent, gating_factor_agent, simulator_service
    
    db.connect()
    print("[OK] Database connected")
    
    # Create tables if they don't exist
    db.create_tables()
    print("[OK] Database tables verified/created")
    
    # Populate default data if database is empty
    populate_default_data(db)
    
    # Check if there are any devices/deployments and provide guidance
    cursor = db.conn.cursor()
    device_count = cursor.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    deployment_count = cursor.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]
    
    if device_count == 0 and deployment_count == 0:
        print("\n[INFO] No sample data found in database")
        print("  To populate with demo data, run:")
        print("    python server/migrate_data.py")
        print("  Or use the Simulator UI to create devices/deployments\n")
    
    # Initialize simulator service
    simulator_service = SimulatorService(db.conn)
    print("[OK] Simulator service initialized")
    
    # Load configuration
    try:
        config = get_config()
        print(f"[OK] Configuration loaded")
        print(f"  - SSO Region: {config.sso_region}")
        print(f"  - Bedrock Region: {config.bedrock_region}")
    except Exception as e:
        print(f"[WARN] Warning: Could not load config.ini: {e}")
        print("  Using default configuration")
    
    # Initialize Bedrock agents
    try:
        bedrock_service = get_bedrock_service()
        ring_categorization_agent = RingCategorizationAgent(bedrock_service, db.conn)
        deployment_failure_agent = DeploymentFailureAgent(bedrock_service)
        gating_factor_agent = GatingFactorAgent(bedrock_service)
        print("[OK] AWS Bedrock agents initialized")
        print(f"  - Credentials from: ~/.aws/credentials")
        print(f"  - Configuration from: config.ini")
    except Exception as e:
        print(f"[WARN] Warning: Could not initialize Bedrock agents: {e}")
        print("  AI features will be disabled.")
        print("  Check:")
        print("    1. AWS credentials in ~/.aws/credentials (aws_access_key_id, aws_secret_access_key, aws_session_token)")
        print("    2. Configuration in config.ini (SSO URLs, regions)")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    db.close()
    print("[OK] Database connection closed")


# Pydantic models for request/response
class Device(BaseModel):
    deviceId: str
    deviceName: str
    manufacturer: str
    model: str
    osName: str
    site: str
    department: str
    ring: int
    totalMemory: str
    totalStorage: str
    networkSpeed: str
    avgCpuUsage: float
    avgMemoryUsage: float
    avgDiskSpace: float
    riskScore: int


class Deployment(BaseModel):
    deploymentId: Optional[str] = None
    deploymentName: str
    status: str


class DeploymentRing(BaseModel):
    ringName: str
    deviceCount: int
    status: str
    failureReason: Optional[str] = None


class GatingFactors(BaseModel):
    avgCpuUsageMax: Optional[float] = None
    avgMemoryUsageMax: Optional[float] = None
    avgDiskFreeSpaceMin: Optional[float] = None
    riskScoreMin: Optional[int] = None
    riskScoreMax: Optional[int] = None


class CreateDeploymentRequest(BaseModel):
    deploymentName: str
    status: str
    gatingFactorMode: str = 'default'  # 'default', 'custom', or 'prompt'
    customGatingFactors: Optional[GatingFactors] = None
    gatingPrompt: Optional[str] = None


class AICategorizeRequest(BaseModel):
    deviceIds: Optional[List[str]] = None  # If None, categorize all devices


class AIGatingFactorRequest(BaseModel):
    naturalLanguageInput: str


class AIFailureAnalysisRequest(BaseModel):
    deploymentId: str
    ringName: str


class DeploymentDetail(BaseModel):
    deploymentId: str
    deploymentName: str
    rings: List[DeploymentRing]
    gatingFactors: Optional[GatingFactors] = None


class Ring(BaseModel):
    ringId: int
    ringName: str
    categorizationPrompt: str


class DashboardMetrics(BaseModel):
    totalDevices: int
    totalDeployments: int
    activeRings: int


class DeviceDistribution(BaseModel):
    name: str
    value: int


# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "FlexDeploy API", "version": "1.0.0"}


@app.get("/api/devices", response_model=List[Device])
async def get_devices():
    """Get all devices"""
    cursor = db.conn.cursor()
    rows = cursor.execute("""
        SELECT device_id, device_name, manufacturer, model, os_name, site, department, ring,
               total_memory, total_storage, network_speed, avg_cpu_usage, avg_memory_usage,
               avg_disk_space, risk_score
        FROM devices
        ORDER BY device_id
    """).fetchall()
    
    devices = []
    for row in rows:
        devices.append({
            "deviceId": row[0],
            "deviceName": row[1],
            "manufacturer": row[2],
            "model": row[3],
            "osName": row[4],
            "site": row[5],
            "department": row[6],
            "ring": row[7],
            "totalMemory": f"{row[8]} GB",
            "totalStorage": f"{row[9]} GB",
            "networkSpeed": f"{row[10]} Mbps",
            "avgCpuUsage": row[11],
            "avgMemoryUsage": row[12],
            "avgDiskSpace": row[13],
            "riskScore": row[14],
        })
    
    return devices


@app.get("/api/deployments", response_model=List[Deployment])
async def get_deployments():
    """Get all deployments with updated statuses"""
    cursor = db.conn.cursor()
    rows = cursor.execute("""
        SELECT deployment_id, deployment_name, status
        FROM deployments
        ORDER BY 
            CASE 
                WHEN deployment_id = 'DEP-001' THEN 1
                WHEN deployment_id = 'DEP-002' THEN 2  
                WHEN deployment_id = 'DEP-003' THEN 3
                WHEN deployment_id = 'DEP-004' THEN 4
                ELSE 5
            END,
            deployment_id
    """).fetchall()
    
    deployments = []
    for row in rows:
        deployments.append({
            "deploymentId": row[0],
            "deploymentName": row[1],
            "status": row[2],
        })
    
    return deployments


@app.get("/api/deployments/{deployment_id}", response_model=DeploymentDetail)
async def get_deployment_detail(deployment_id: str):
    """Get deployment details including ring status with scenario-based data"""
    cursor = db.conn.cursor()
    
    # Get deployment info
    deployment = cursor.execute("""
        SELECT deployment_id, deployment_name, status
        FROM deployments
        WHERE deployment_id = ?
    """, (deployment_id,)).fetchone()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Get ring details with proper ordering
    rings = cursor.execute("""
        SELECT r.ring_name, dr.device_count, dr.status, dr.failure_reason
        FROM deployment_rings dr
        JOIN rings r ON dr.ring_id = r.ring_id
        WHERE dr.deployment_id = ?
        ORDER BY dr.ring_id
    """, (deployment_id,)).fetchall()
    
    ring_list = []
    for ring in rings:
        ring_list.append({
            "ringName": ring[0],
            "deviceCount": ring[1],
            "status": ring[2],
            "failureReason": ring[3],
        })
    
    # Get deployment-specific gating factors
    gating_factors_row = cursor.execute("""
        SELECT avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
               risk_score_min, risk_score_max
        FROM deployment_gating_factors
        WHERE deployment_id = ?
    """, (deployment_id,)).fetchone()
    
    gating_factors = None
    if gating_factors_row:
        gating_factors = {
            "avgCpuUsageMax": gating_factors_row[0],
            "avgMemoryUsageMax": gating_factors_row[1],
            "avgDiskFreeSpaceMin": gating_factors_row[2],
            "riskScoreMin": gating_factors_row[3],
            "riskScoreMax": gating_factors_row[4],
        }
    
    return {
        "deploymentId": deployment[0],
        "deploymentName": deployment[1],
        "rings": ring_list,
        "gatingFactors": gating_factors,
    }


@app.get("/api/deployments/status/all")
async def get_all_deployments_status():
    """Get status updates for all deployments - optimized for polling"""
    cursor = db.conn.cursor()
    
    # Get all deployments
    deployments_rows = cursor.execute("""
        SELECT deployment_id, deployment_name, status, updated_at
        FROM deployments
        ORDER BY 
            CASE 
                WHEN deployment_id = 'DEP-001' THEN 1
                WHEN deployment_id = 'DEP-002' THEN 2  
                WHEN deployment_id = 'DEP-003' THEN 3
                WHEN deployment_id = 'DEP-004' THEN 4
                ELSE 5
            END,
            deployment_id
    """).fetchall()
    
    deployments = []
    for dep_row in deployments_rows:
        deployment_id = dep_row[0]
        
        # Get ring status for this deployment
        rings_rows = cursor.execute("""
            SELECT dr.ring_id, r.ring_name, dr.device_count, dr.status, dr.failure_reason, dr.updated_at
            FROM deployment_rings dr
            JOIN rings r ON dr.ring_id = r.ring_id
            WHERE dr.deployment_id = ?
            ORDER BY dr.ring_id
        """, (deployment_id,)).fetchall()
        
        rings = []
        for ring_row in rings_rows:
            rings.append({
                "ringId": ring_row[0],
                "ringName": ring_row[1],
                "deviceCount": ring_row[2],
                "status": ring_row[3],
                "failureReason": ring_row[4],
                "updatedAt": ring_row[5]
            })
        
        deployments.append({
            "deploymentId": dep_row[0],
            "deploymentName": dep_row[1],
            "status": dep_row[2],
            "updatedAt": dep_row[3],
            "rings": rings
        })
    
    return {
        "deployments": deployments,
        "timestamp": cursor.execute("SELECT CURRENT_TIMESTAMP").fetchone()[0]
    }


@app.get("/api/rings", response_model=List[Ring])
async def get_rings():
    """Get all ring configurations"""
    cursor = db.conn.cursor()
    rows = cursor.execute("""
        SELECT ring_id, ring_name, categorization_prompt
        FROM rings
        ORDER BY ring_id
    """).fetchall()
    
    rings = []
    for row in rows:
        rings.append({
            "ringId": row[0],
            "ringName": row[1],
            "categorizationPrompt": row[2],
        })
    
    return rings


@app.put("/api/rings/{ring_id}")
async def update_ring(ring_id: int, ring: Ring):
    """Update ring configuration"""
    cursor = db.conn.cursor()
    
    cursor.execute("""
        UPDATE rings
        SET ring_name = ?,
            categorization_prompt = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE ring_id = ?
    """, (
        ring.ringName,
        ring.categorizationPrompt,
        ring_id,
    ))
    
    db.conn.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Ring not found")
    
    return {"message": "Ring updated successfully"}


@app.get("/api/gating-factors", response_model=GatingFactors)
async def get_default_gating_factors():
    """Get default gating factors"""
    cursor = db.conn.cursor()
    row = cursor.execute("""
        SELECT avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
               risk_score_min, risk_score_max
        FROM default_gating_factors
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()
    
    if not row:
        # Return default values if no configuration exists
        return {
            "avgCpuUsageMax": 100,
            "avgMemoryUsageMax": 100,
            "avgDiskFreeSpaceMin": 0,
            "riskScoreMin": 0,
            "riskScoreMax": 100,
        }
    
    return {
        "avgCpuUsageMax": row[0],
        "avgMemoryUsageMax": row[1],
        "avgDiskFreeSpaceMin": row[2],
        "riskScoreMin": row[3],
        "riskScoreMax": row[4],
    }


@app.put("/api/gating-factors")
async def update_default_gating_factors(gating_factors: GatingFactors):
    """Update default gating factors"""
    cursor = db.conn.cursor()
    
    # Check if a record exists
    existing = cursor.execute("SELECT id FROM default_gating_factors LIMIT 1").fetchone()
    
    if existing:
        cursor.execute("""
            UPDATE default_gating_factors
            SET avg_cpu_usage_max = ?,
                avg_memory_usage_max = ?,
                avg_disk_free_space_min = ?,
                risk_score_min = ?,
                risk_score_max = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            gating_factors.avgCpuUsageMax,
            gating_factors.avgMemoryUsageMax,
            gating_factors.avgDiskFreeSpaceMin,
            gating_factors.riskScoreMin,
            gating_factors.riskScoreMax,
            existing[0],
        ))
    else:
        cursor.execute("""
            INSERT INTO default_gating_factors 
            (avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min, 
             risk_score_min, risk_score_max)
            VALUES (?, ?, ?, ?, ?)
        """, (
            gating_factors.avgCpuUsageMax,
            gating_factors.avgMemoryUsageMax,
            gating_factors.avgDiskFreeSpaceMin,
            gating_factors.riskScoreMin,
            gating_factors.riskScoreMax,
        ))
    
    db.conn.commit()
    
    return {"message": "Default gating factors updated successfully"}


@app.get("/api/dashboard/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics():
    """Get dashboard metrics"""
    metrics = db.get_dashboard_metrics()
    return metrics


@app.get("/api/dashboard/device-distribution", response_model=List[DeviceDistribution])
async def get_device_distribution():
    """Get device distribution by ring"""
    distribution = db.get_device_distribution_by_ring()
    return distribution


@app.post("/api/deployments")
async def create_deployment(request: CreateDeploymentRequest):
    """Create a new deployment with auto-generated ID and configurable gating factors"""
    cursor = db.conn.cursor()
    
    # Auto-generate deployment ID
    cursor.execute("""
        SELECT deployment_id FROM deployments 
        WHERE deployment_id LIKE 'DEP-%'
        ORDER BY deployment_id DESC
    """)
    
    max_num = 0
    for row in cursor.fetchall():
        dep_id = row[0]
        if dep_id.startswith("DEP-"):
            try:
                num_part = dep_id.split("-")[1]
                num = int(num_part)
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                continue
    
    new_id = f"DEP-{str(max_num + 1).zfill(3)}"
    
    # Insert deployment
    cursor.execute("""
        INSERT INTO deployments (deployment_id, deployment_name, status)
        VALUES (?, ?, ?)
    """, (new_id, request.deploymentName, request.status))
    
    # Determine gating factors based on mode
    gating_factors = None
    
    if request.gatingFactorMode == 'default':
        # Get default gating factors
        default_gating = cursor.execute("""
            SELECT avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
                   risk_score_min, risk_score_max
            FROM default_gating_factors
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()
        
        if default_gating:
            gating_factors = default_gating
    
    elif request.gatingFactorMode == 'custom':
        # Use custom provided gating factors
        if request.customGatingFactors:
            gating_factors = (
                request.customGatingFactors.avgCpuUsageMax,
                request.customGatingFactors.avgMemoryUsageMax,
                request.customGatingFactors.avgDiskFreeSpaceMin,
                request.customGatingFactors.riskScoreMin or 0,
                request.customGatingFactors.riskScoreMax or 100,
            )
    
    elif request.gatingFactorMode == 'prompt':
        # TODO: Integrate with AI/LLM to interpret the gating prompt
        # Example integration:
        # from openai import OpenAI
        # client = OpenAI()
        # response = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{
        #         "role": "system",
        #         "content": "You are a deployment gating expert. Convert user requirements into numeric thresholds."
        #     }, {
        #         "role": "user", 
        #         "content": f"Set gating factors for: {request.gatingPrompt}"
        #     }]
        # )
        # Parse the AI response to extract numeric values
        
        # For now, use conservative defaults based on the prompt
        gating_factors = (80.0, 80.0, 20.0, 0, 100)
    
    # Insert gating factors for deployment
    if gating_factors:
        cursor.execute("""
            INSERT INTO deployment_gating_factors 
            (deployment_id, avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
             risk_score_min, risk_score_max)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (new_id, *gating_factors))
    
    # Create deployment rings for all rings
    rings = cursor.execute("""
        SELECT ring_id, ring_name
        FROM rings
        ORDER BY ring_id
    """).fetchall()
    
    for ring in rings:
        # Count devices in this ring
        device_count = cursor.execute("""
            SELECT COUNT(*) FROM devices WHERE ring = ?
        """, (ring[0],)).fetchone()[0]
        
        cursor.execute("""
            INSERT INTO deployment_rings 
            (deployment_id, ring_id, ring_name, device_count, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            new_id,
            ring[0],
            ring[1],
            device_count,
            'Not Started',
        ))
    
    db.conn.commit()
    
    return {
        "message": "Deployment created successfully",
        "deploymentId": new_id
    }


@app.post("/api/deployments/{deployment_id}/run")
async def run_deployment(deployment_id: str):
    """Start a deployment"""
    cursor = db.conn.cursor()
    
    # Update deployment status
    cursor.execute("""
        UPDATE deployments
        SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP
        WHERE deployment_id = ?
    """, (deployment_id,))
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    db.conn.commit()
    
    return {"message": "Deployment started successfully"}


@app.post("/api/deployments/{deployment_id}/stop")
async def stop_deployment(deployment_id: str):
    """Stop a deployment"""
    cursor = db.conn.cursor()
    
    # Update deployment status
    cursor.execute("""
        UPDATE deployments
        SET status = 'Stopped', updated_at = CURRENT_TIMESTAMP
        WHERE deployment_id = ?
    """, (deployment_id,))
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    db.conn.commit()
    
    return {"message": "Deployment stopped successfully"}


@app.delete("/api/deployments/{deployment_id}")
async def delete_deployment(deployment_id: str):
    """Delete a deployment and its related data"""
    cursor = db.conn.cursor()
    
    # Check if deployment exists
    deployment = cursor.execute("""
        SELECT deployment_id FROM deployments WHERE deployment_id = ?
    """, (deployment_id,)).fetchone()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Delete related deployment_gating_factors
    cursor.execute("""
        DELETE FROM deployment_gating_factors WHERE deployment_id = ?
    """, (deployment_id,))
    
    # Delete related deployment_rings
    cursor.execute("""
        DELETE FROM deployment_rings WHERE deployment_id = ?
    """, (deployment_id,))
    
    # Delete the deployment itself
    cursor.execute("""
        DELETE FROM deployments WHERE deployment_id = ?
    """, (deployment_id,))
    
    db.conn.commit()
    
    return {"message": "Deployment deleted successfully"}


# AI Agent Endpoints

@app.post("/api/ai/categorize-devices")
async def ai_categorize_devices(request: AICategorizeRequest):
    """
    Use AI to categorize devices into rings based on ring prompts
    Pipeline: prompt -> SQL agent -> reasoning agent -> result
    """
    if ring_categorization_agent is None:
        raise HTTPException(
            status_code=503,
            detail="AI categorization service not available. Check AWS Bedrock configuration."
        )
    
    cursor = db.conn.cursor()
    
    # Get ring prompts
    rings = cursor.execute("""
        SELECT ring_id, ring_name, categorization_prompt
        FROM rings
        ORDER BY ring_id
    """).fetchall()
    
    ring_prompts = [
        {
            "ringId": r[0],
            "ringName": r[1],
            "categorizationPrompt": r[2]
        }
        for r in rings
    ]
    
    # Get devices to categorize
    if request.deviceIds:
        placeholders = ','.join('?' * len(request.deviceIds))
        query = f"""
            SELECT device_id, device_name, manufacturer, model, os_name, site, department, ring,
                   total_memory, total_storage, network_speed, avg_cpu_usage, avg_memory_usage,
                   avg_disk_space, risk_score
            FROM devices
            WHERE device_id IN ({placeholders})
        """
        rows = cursor.execute(query, request.deviceIds).fetchall()
    else:
        rows = cursor.execute("""
            SELECT device_id, device_name, manufacturer, model, os_name, site, department, ring,
                   total_memory, total_storage, network_speed, avg_cpu_usage, avg_memory_usage,
                   avg_disk_space, risk_score
            FROM devices
        """).fetchall()
    
    devices = []
    for row in rows:
        devices.append({
            "deviceId": row[0],
            "deviceName": row[1],
            "manufacturer": row[2],
            "model": row[3],
            "osName": row[4],
            "site": row[5],
            "department": row[6],
            "ring": row[7],
            "totalMemory": row[8],
            "totalStorage": row[9],
            "networkSpeed": row[10],
            "avgCpuUsage": row[11],
            "avgMemoryUsage": row[12],
            "avgDiskSpace": row[13],
            "riskScore": row[14],
        })
    
    # Categorize devices using AI
    try:
        results = ring_categorization_agent.batch_categorize_devices(devices, ring_prompts)
        
        # Update database with new categorizations
        updated_count = 0
        categorizations = []
        
        for device_id, ring_id, reasoning in results:
            cursor.execute("""
                UPDATE devices
                SET ring = ?, updated_at = CURRENT_TIMESTAMP
                WHERE device_id = ?
            """, (ring_id, device_id))
            
            if cursor.rowcount > 0:
                updated_count += 1
            
            categorizations.append({
                "deviceId": device_id,
                "assignedRing": ring_id,
                "reasoning": reasoning
            })
        
        db.conn.commit()
        
        return {
            "message": f"Successfully categorized {updated_count} devices",
            "categorizations": categorizations
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI categorization failed: {str(e)}"
        )


@app.post("/api/ai/analyze-failure")
async def ai_analyze_deployment_failure(request: AIFailureAnalysisRequest):
    """
    Use AI to analyze deployment failure reasons
    Pipeline: gating factor -> prompt -> result
    """
    if deployment_failure_agent is None:
        raise HTTPException(
            status_code=503,
            detail="AI failure analysis service not available. Check AWS Bedrock configuration."
        )
    
    cursor = db.conn.cursor()
    
    # Get deployment info
    deployment = cursor.execute("""
        SELECT deployment_id, deployment_name
        FROM deployments
        WHERE deployment_id = ?
    """, (request.deploymentId,)).fetchone()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Get gating factors for this deployment
    gating_factors_row = cursor.execute("""
        SELECT avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
               risk_score_min, risk_score_max
        FROM deployment_gating_factors
        WHERE deployment_id = ?
    """, (request.deploymentId,)).fetchone()
    
    if not gating_factors_row:
        # Use default gating factors
        gating_factors_row = cursor.execute("""
            SELECT avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
                   risk_score_min, risk_score_max
            FROM default_gating_factors
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()
    
    if not gating_factors_row:
        gating_factors_dict = {
            "avgCpuUsageMax": 80.0,
            "avgMemoryUsageMax": 80.0,
            "avgDiskFreeSpaceMin": 20.0,
            "riskScoreMin": 0,
            "riskScoreMax": 100
        }
    else:
        gating_factors_dict = {
            "avgCpuUsageMax": gating_factors_row[0],
            "avgMemoryUsageMax": gating_factors_row[1],
            "avgDiskFreeSpaceMin": gating_factors_row[2],
            "riskScoreMin": gating_factors_row[3],
            "riskScoreMax": gating_factors_row[4]
        }
    
    # Get ring ID from ring name
    ring_id_row = cursor.execute("""
        SELECT ring_id FROM rings WHERE ring_name = ?
    """, (request.ringName,)).fetchone()
    
    if not ring_id_row:
        raise HTTPException(status_code=404, detail="Ring not found")
    
    ring_id = ring_id_row[0]
    
    # Get device metrics for this ring
    device_rows = cursor.execute("""
        SELECT device_id, device_name, avg_cpu_usage, avg_memory_usage, avg_disk_space, risk_score
        FROM devices
        WHERE ring = ?
    """, (ring_id,)).fetchall()
    
    device_metrics = [
        {
            "deviceId": row[0],
            "deviceName": row[1],
            "avgCpuUsage": row[2],
            "avgMemoryUsage": row[3],
            "avgDiskSpace": row[4],
            "riskScore": row[5]
        }
        for row in device_rows
    ]
    
    try:
        # Analyze failure using AI
        analysis = deployment_failure_agent.analyze_failure(
            ring_name=request.ringName,
            device_metrics=device_metrics,
            gating_factors=gating_factors_dict,
            deployment_name=deployment[1]
        )
        
        # Update the failure reason in the database
        cursor.execute("""
            UPDATE deployment_rings
            SET failure_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE deployment_id = ? AND ring_name = ?
        """, (analysis, request.deploymentId, request.ringName))
        
        db.conn.commit()
        
        return {
            "deploymentId": request.deploymentId,
            "ringName": request.ringName,
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI failure analysis failed: {str(e)}"
        )


@app.post("/api/ai/gating-factors")
async def ai_parse_gating_factors(request: AIGatingFactorRequest):
    """
    Use AI to convert natural language to gating factors
    Pipeline: user text -> prompt -> gating factor -> result
    """
    if gating_factor_agent is None:
        raise HTTPException(
            status_code=503,
            detail="AI gating factor service not available. Check AWS Bedrock configuration."
        )
    
    try:
        # Parse natural language to gating factors
        result = gating_factor_agent.parse_natural_language(request.naturalLanguageInput)
        
        return {
            "gatingFactors": {
                "avgCpuUsageMax": result["avgCpuUsageMax"],
                "avgMemoryUsageMax": result["avgMemoryUsageMax"],
                "avgDiskFreeSpaceMin": result["avgDiskFreeSpaceMin"],
                "riskScoreMin": result["riskScoreMin"],
                "riskScoreMax": result["riskScoreMax"]
            },
            "explanation": result["explanation"],
            "originalInput": request.naturalLanguageInput
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI gating factor parsing failed: {str(e)}"
        )


@app.post("/api/ai/validate-gating-factors")
async def ai_validate_gating_factors(gating_factors: GatingFactors):
    """
    Use AI to validate and suggest improvements for gating factors
    """
    if gating_factor_agent is None:
        raise HTTPException(
            status_code=503,
            detail="AI gating factor service not available. Check AWS Bedrock configuration."
        )
    
    try:
        gating_dict = {
            "avgCpuUsageMax": gating_factors.avgCpuUsageMax,
            "avgMemoryUsageMax": gating_factors.avgMemoryUsageMax,
            "avgDiskFreeSpaceMin": gating_factors.avgDiskFreeSpaceMin,
            "riskScoreMin": gating_factors.riskScoreMin,
            "riskScoreMax": gating_factors.riskScoreMax
        }
        
        validation_result = gating_factor_agent.validate_and_suggest(gating_dict)
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI validation failed: {str(e)}"
        )


# ==================== SIMULATION APIs ====================

class DeviceCreate(BaseModel):
    """Model for creating a device via API"""
    deviceId: str
    deviceName: str
    manufacturer: str
    model: str
    osName: str
    site: str
    department: str
    ring: Optional[int] = None
    totalMemory: int  # in GB
    totalStorage: int  # in GB
    networkSpeed: int  # in Mbps
    avgCpuUsage: float = 50.0
    avgMemoryUsage: float = 50.0
    avgDiskSpace: float = 50.0
    riskScore: Optional[int] = None


class DeviceMetrics(BaseModel):
    """Model for updating device metrics"""
    deviceId: str
    avgCpuUsage: float
    avgMemoryUsage: float
    avgDiskSpace: float
    riskScore: Optional[int] = None


class RingMetrics(BaseModel):
    """Model for updating metrics for all devices in a ring"""
    ringId: int
    deploymentId: str
    avgCpuUsage: Optional[float] = None
    avgMemoryUsage: Optional[float] = None
    avgDiskSpace: Optional[float] = None
    riskScore: Optional[int] = None


class DeploymentRingStatus(BaseModel):
    """Model for updating deployment ring status"""
    deploymentId: str
    ringId: int
    status: str  # Not Started, In Progress, Completed, Failed, Stopped
    failureReason: Optional[str] = None


@app.post("/api/simulator/devices")
async def create_device(device: DeviceCreate):
    """
    Create or update a device with metadata.
    Used by simulator to add devices to the system.
    If ring is not provided, device will be assigned to ring 0 by default.
    """
    try:
        result = simulator_service.create_or_update_device(
            device_id=device.deviceId,
            device_name=device.deviceName,
            manufacturer=device.manufacturer,
            model=device.model,
            os_name=device.osName,
            site=device.site,
            department=device.department,
            ring=device.ring if device.ring is not None else 0,  # Default to ring 0 if not provided
            total_memory=device.totalMemory,
            total_storage=device.totalStorage,
            network_speed=device.networkSpeed,
            avg_cpu_usage=device.avgCpuUsage,
            avg_memory_usage=device.avgMemoryUsage,
            avg_disk_space=device.avgDiskSpace,
            risk_score=device.riskScore
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create device: {str(e)}")


@app.post("/api/simulator/device-metrics")
async def update_device_metrics_endpoint(metrics: DeviceMetrics):
    """
    Update CPU, memory, and disk usage for a specific device.
    Used by simulator to update device metrics dynamically.
    """
    try:
        result = simulator_service.update_device_metrics(
            device_id=metrics.deviceId,
            avg_cpu_usage=metrics.avgCpuUsage,
            avg_memory_usage=metrics.avgMemoryUsage,
            avg_disk_space=metrics.avgDiskSpace,
            risk_score=metrics.riskScore
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update metrics: {str(e)}")


@app.post("/api/simulator/ring-metrics")
async def update_ring_metrics_endpoint(ring_metrics: RingMetrics):
    """
    Update metrics for all devices in a specific ring.
    Used by simulator to set average metrics for ring simulation.
    """
    try:
        result = simulator_service.update_ring_metrics(
            ring_id=ring_metrics.ringId,
            deployment_id=ring_metrics.deploymentId,
            avg_cpu_usage=ring_metrics.avgCpuUsage,
            avg_memory_usage=ring_metrics.avgMemoryUsage,
            avg_disk_space=ring_metrics.avgDiskSpace,
            risk_score=ring_metrics.riskScore
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update ring metrics: {str(e)}")


@app.post("/api/simulator/deployment-status")
async def update_deployment_ring_status_endpoint(status_update: DeploymentRingStatus):
    """
    Update the status of a specific ring in a deployment.
    Used by simulator to control deployment progression.
    """
    try:
        result = simulator_service.update_deployment_ring_status(
            deployment_id=status_update.deploymentId,
            ring_id=status_update.ringId,
            status=status_update.status,
            failure_reason=status_update.failureReason
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update deployment status: {str(e)}")


@app.get("/api/simulator/deployment/{deployment_id}/ring/{ring_id}/devices")
async def get_ring_devices_endpoint(deployment_id: str, ring_id: int):
    """
    Get all devices in a specific ring for simulation purposes.
    Returns device details including current metrics.
    """
    try:
        devices = simulator_service.get_ring_devices(deployment_id, ring_id)
        return {
            "deploymentId": deployment_id,
            "ringId": ring_id,
            "devices": devices
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ring devices: {str(e)}")


@app.post("/api/simulator/stress-profile")
async def apply_stress_profile(request: dict):
    """
    Apply a pre-configured stress profile to a ring.
    Stress levels: low, normal, high, critical
    """
    try:
        deployment_id = request.get("deploymentId")
        ring_id = request.get("ringId")
        stress_level = request.get("stressLevel", "normal")
        
        result = simulator_service.apply_stress_profile(
            deployment_id=deployment_id,
            ring_id=ring_id,
            stress_level=stress_level
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply stress profile: {str(e)}")


@app.post("/api/simulator/reinit")
async def reinit_application():
    """
    Reinitialize the application by deleting all devices and deployments.
    Used by simulator to reset the system to a clean state.
    """
    try:
        cursor = db.conn.cursor()
        
        # Delete all deployment-related data
        cursor.execute("DELETE FROM deployment_gating_factors")
        cursor.execute("DELETE FROM deployment_rings")
        cursor.execute("DELETE FROM deployments")
        
        # Delete all devices
        cursor.execute("DELETE FROM devices")
        
        db.conn.commit()
        
        return {
            "status": "success",
            "message": "Application reinitialized successfully. All devices and deployments have been deleted."
        }
    except Exception as e:
        db.conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reinitialize application: {str(e)}")


def main():
    """Run the server"""
    try:
        config = get_config()
        host = config.server_host
        port = config.server_port
    except:
        host = "0.0.0.0"
        port = 8000
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
