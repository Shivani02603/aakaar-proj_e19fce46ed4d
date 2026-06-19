from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from database.models import Deployment
from sqlalchemy.orm import joinedload


class DeploymentService:
    @staticmethod
    async def create_deployment(deployment_data: dict, db: AsyncSession) -> Deployment:
        try:
            deployment = Deployment(**deployment_data)
            db.add(deployment)
            await db.commit()
            await db.refresh(deployment)
            return deployment
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create deployment: {str(e)}")

    @staticmethod
    async def get_deployment_by_id(deployment_id: UUID, db: AsyncSession) -> Deployment:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(status_code=404, detail="Deployment not found")
            return deployment
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve deployment: {str(e)}")

    @staticmethod
    async def list_all_deployments(db: AsyncSession) -> List[Deployment]:
        try:
            result = await db.execute(select(Deployment).options(joinedload("*")))
            deployments = result.scalars().all()
            return deployments
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Failed to list deployments: {str(e)}")

    @staticmethod
    async def update_deployment(deployment_id: UUID, deployment_update: dict, db: AsyncSession) -> Deployment:
        try:
            result = await db.execute(select(Deployment).where(Deployment.id == deployment_id))
            deployment = result.scalar_one_or_none()
            if not deployment:
                raise HTTPException(status_code=404, detail="Deployment not found")

            for key, value in deployment_update.items():
                setattr(deployment, key, value)

            db.add(deployment)
            await db.commit()
            await db.refresh(deployment)
            return deployment
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update deployment: {str(e)}")

    @staticmethod
    async def delete_deployment(deployment_id: UUID, db: AsyncSession) -> None:
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