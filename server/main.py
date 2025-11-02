"""
FastAPI server for FlexDeploy - AI Deployment Orchestrator
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import uvicorn

from server.database import Database


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
db_path = os.path.join(os.path.dirname(__file__), "flexdeploy.db")
db = Database(db_path)


@app.on_event("startup")
async def startup_event():
    """Connect to database on startup"""
    db.connect()
    print("✓ Database connected")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    db.close()
    print("✓ Database connection closed")


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
            "totalMemory": row[8],
            "totalStorage": row[9],
            "networkSpeed": row[10],
            "avgCpuUsage": row[11],
            "avgMemoryUsage": row[12],
            "avgDiskSpace": row[13],
            "riskScore": row[14],
        })
    
    return devices


@app.get("/api/deployments", response_model=List[Deployment])
async def get_deployments():
    """Get all deployments"""
    cursor = db.conn.cursor()
    rows = cursor.execute("""
        SELECT deployment_id, deployment_name, status
        FROM deployments
        ORDER BY deployment_id
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
    """Get deployment details including ring status"""
    cursor = db.conn.cursor()
    
    # Get deployment info
    deployment = cursor.execute("""
        SELECT deployment_id, deployment_name, status
        FROM deployments
        WHERE deployment_id = ?
    """, (deployment_id,)).fetchone()
    
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Get ring details
    rings = cursor.execute("""
        SELECT ring_name, device_count, status, failure_reason
        FROM deployment_rings
        WHERE deployment_id = ?
        ORDER BY ring_id
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


def main():
    """Run the server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
