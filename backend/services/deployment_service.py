from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Deployment
from sqlalchemy.orm import joinedload


class DeploymentService:
    async def create_deployment(self, deployment_data: dict, db: AsyncSession) -> Deployment:
        try:
            new_deployment = Deployment(**deployment_data)
            db.add(new_deployment)
            await db.commit()
            await db.refresh(new_deployment)
            return new_deployment
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create deployment: {str(e)}")

    async def get_deployment_by_id(self, deployment_id: UUID, db: AsyncSession) -> Deployment:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(status_code=404, detail="Deployment not found")
            return deployment
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve deployment: {str(e)}")

    async def list_all_deployments(self, db: AsyncSession) -> List[Deployment]:
        try:
            result = await db.execute(select(Deployment))
            deployments = result.scalars().all()
            return deployments
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list deployments: {str(e)}")

    async def update_deployment(self, deployment_id: UUID, updated_data: dict, db: AsyncSession) -> Deployment:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(status_code=404, detail="Deployment not found")

            for key, value in updated_data.items():
                setattr(deployment, key, value)

            db.add(deployment)
            await db.commit()
            await db.refresh(deployment)
            return deployment
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update deployment: {str(e)}")

    async def delete_deployment(self, deployment_id: UUID, db: AsyncSession) -> None:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(status_code=404, detail="Deployment not found")

            await db.delete(deployment)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete deployment: {str(e)}")