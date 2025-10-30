from pydantic import BaseModel
from .product_category import CategoryData
from enum import Enum

class TaxType(Enum):
    purchase_tax = "purchase_tax"
    sale_tax = "sale_tax"

class TaxData(BaseModel):
    tax_type: TaxType
    tax_name: str
    tax_percentage : float

class ProductData(BaseModel):
    product_name : str
    x_care_id: str
    cost:float | None = None
    mrp:float = 0.0
    category: CategoryData
    taxes : list[TaxData] | None = None
