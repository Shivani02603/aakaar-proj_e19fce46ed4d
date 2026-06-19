from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from database.models import Deployment
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/deployment", tags=["Deployment"])

# Pydantic schemas
class DeploymentBase(BaseModel):
    name: str = Field(..., example="My Deployment")
    description: Optional[str] = Field(None, example="Deployment description")
    version: str = Field(..., example="1.0.0")
    created_at: Optional[str] = Field(None, example="2023-10-01T12:00:00Z")

class DeploymentCreate(DeploymentBase):
    pass

class DeploymentUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Deployment Name")
    description: Optional[str] = Field(None, example="Updated description")
    version: Optional[str] = Field(None, example="1.0.1")

class DeploymentResponse(DeploymentBase):
    id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

# CRUD endpoints
@router.post("/", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment: DeploymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    new_deployment = Deployment(**deployment.dict())
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)
    return new_deployment

@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployments = db.query(Deployment).all()
    return deployments

@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment

@router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: UUID,
    deployment_update: DeploymentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    
    for key, value in deployment_update.dict(exclude_unset=True).items():
        setattr(deployment, key, value)
    
    db.commit()
    db.refresh(deployment)
    return deployment

@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    
    db.delete(deployment)
    db.commit()
    return None

# Additional endpoints for deployment functionality
@router.post("/docker-compose", status_code=status.HTTP_200_OK)
async def deploy_with_docker_compose(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Simulate Docker Compose deployment logic
    try:
        # Example: Trigger Docker Compose commands
        # subprocess.run(["docker-compose", "up", "-d"], check=True)
        return {"detail": "Deployment initiated using Docker Compose"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/docker-compose/status", status_code=status.HTTP_200_OK)
async def get_docker_compose_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Simulate checking Docker Compose status
    try:
        # Example: Check Docker Compose status
        # result = subprocess.run(["docker-compose", "ps"], capture_output=True, text=True)
        # return {"status": result.stdout}
        return {"status": "Docker Compose services are running"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))