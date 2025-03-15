from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectDataSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    project_name: Optional[str] = None
    research_field: Optional[str] = None
    responsible_name: Optional[str] = None
    dialog_id: Optional[UUID] = None
    responsible_area: Optional[str] = None
    project_goal: Optional[str] = None
    project_benefits: Optional[str] = None
    project_differentiator: Optional[str] = None
    milestone: Optional[str] = None
    road_blocks: Optional[str] = None
    research_methods: Optional[str] = None
    next_steps: Optional[str] = None
    additional_details: Optional[str] = None
    user_observations: Optional[str] = None
    is_confirmed: bool

    class Config:
        from_attributes = True
