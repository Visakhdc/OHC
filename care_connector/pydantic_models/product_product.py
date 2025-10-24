from pydantic import BaseModel
from .product_category import CategoryData

class ProductData(BaseModel):
    product_name : str
    x_care_id: str
    cost:float = 0.0
    mrp:float = 0.0
    category: CategoryData
