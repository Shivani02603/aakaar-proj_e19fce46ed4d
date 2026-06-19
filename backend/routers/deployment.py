from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime
from database.models import Deployment
from database.config import get_db
from backend.services.auth import get_current_user

router = APIRouter(prefix="/deployment", tags=["Deployment"])

# Pydantic schemas
class DeploymentBase(BaseModel):
    name: str = Field(..., example="My Deployment")
    description: Optional[str] = Field(None, example="Description of the deployment")
    created_at: Optional[datetime] = None

class DeploymentCreate(DeploymentBase):
    pass

class DeploymentUpdate(BaseModel):
    name: Optional[str] = Field(None, example="Updated Deployment Name")
    description: Optional[str] = Field(None, example="Updated description")

class DeploymentResponse(DeploymentBase):
    id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000")

# CRUD endpoints
@router.post("/", response_model=DeploymentResponse)
async def create_deployment(
    deployment: DeploymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    new_deployment = Deployment(
        name=deployment.name,
        description=deployment.description,
        created_at=datetime.utcnow(),
    )
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)
    return DeploymentResponse(
        id=new_deployment.id,
        name=new_deployment.name,
        description=new_deployment.description,
        created_at=new_deployment.created_at,
    )

@router.get("/", response_model=List[DeploymentResponse])
async def list_deployments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployments = db.query(Deployment).all()
    return [
        DeploymentResponse(
            id=deployment.id,
            name=deployment.name,
            description=deployment.description,
            created_at=deployment.created_at,
        )
        for deployment in deployments
    ]

@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return DeploymentResponse(
        id=deployment.id,
        name=deployment.name,
        description=deployment.description,
        created_at=deployment.created_at,
    )

@router.put("/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(
    deployment_id: UUID,
    deployment: DeploymentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    existing_deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not existing_deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if deployment.name is not None:
        existing_deployment.name = deployment.name
    if deployment.description is not None:
        existing_deployment.description = deployment.description
    
    db.commit()
    db.refresh(existing_deployment)
    return DeploymentResponse(
        id=existing_deployment.id,
        name=existing_deployment.name,
        description=existing_deployment.description,
        created_at=existing_deployment.created_at,
    )

@router.delete("/{deployment_id}")
async def delete_deployment(
    deployment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    db.delete(deployment)
    db.commit()
    return {"detail": "Deployment deleted successfully"}