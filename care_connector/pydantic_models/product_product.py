from pydantic import BaseModel

class ProductData(BaseModel):
    product_name : str
    x_care_id: str
    cost:float = 0.0
    mrp:float = 0.0
    category: str
