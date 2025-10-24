from pydantic import BaseModel

class CategoryData(BaseModel):
    category_name : str
    parent_category_name: str
    x_care_id: str