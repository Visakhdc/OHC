from pydantic import BaseModel

class DiscountGroup(BaseModel):
    x_care_id: str
    name: str

class InvoiceDiscounts(BaseModel):
    x_care_id: str
    name: str
    discount_group: DiscountGroup
    amount: float = 0.0