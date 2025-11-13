from pydantic import BaseModel
from enum import Enum

class CategoryStatus(Enum):
    active = 'active'
    retired = 'retired'
    draft = 'draft'

class CategoryData(BaseModel):
    category_name: str
    x_care_id: str
    parent_x_care_id: str | None = None
    status: CategoryStatus | None = None