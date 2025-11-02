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
    deploymentId: str
    deploymentName: str
    status: str


class DeploymentRing(BaseModel):
    ringName: str
    deviceCount: int
    status: str
    failureReason: Optional[str] = None


class DeploymentDetail(BaseModel):
    deploymentId: str
    deploymentName: str
    rings: List[DeploymentRing]


class Ring(BaseModel):
    ringId: int
    ringName: str
    categorizationPrompt: str
    gatingFactors: dict


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
    
    return {
        "deploymentId": deployment[0],
        "deploymentName": deployment[1],
        "rings": ring_list,
    }


@app.get("/api/rings", response_model=List[Ring])
async def get_rings():
    """Get all ring configurations"""
    cursor = db.conn.cursor()
    rows = cursor.execute("""
        SELECT ring_id, ring_name, categorization_prompt, risk_score_min, risk_score_max,
               avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min
        FROM rings
        ORDER BY ring_id
    """).fetchall()
    
    rings = []
    for row in rows:
        rings.append({
            "ringId": row[0],
            "ringName": row[1],
            "categorizationPrompt": row[2],
            "gatingFactors": {
                "riskScore": {"min": row[3], "max": row[4]},
                "avgCpuUsage": {"max": row[5]},
                "avgMemoryUsage": {"max": row[6]},
                "avgDiskFreeSpace": {"min": row[7]},
            }
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
            risk_score_min = ?,
            risk_score_max = ?,
            avg_cpu_usage_max = ?,
            avg_memory_usage_max = ?,
            avg_disk_free_space_min = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE ring_id = ?
    """, (
        ring.ringName,
        ring.categorizationPrompt,
        ring.gatingFactors.get("riskScore", {}).get("min"),
        ring.gatingFactors.get("riskScore", {}).get("max"),
        ring.gatingFactors.get("avgCpuUsage", {}).get("max"),
        ring.gatingFactors.get("avgMemoryUsage", {}).get("max"),
        ring.gatingFactors.get("avgDiskFreeSpace", {}).get("min"),
        ring_id,
    ))
    
    db.conn.commit()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Ring not found")
    
    return {"message": "Ring updated successfully"}


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
