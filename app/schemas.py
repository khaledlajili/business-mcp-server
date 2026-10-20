from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str
    company: str | None = None
    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    unit_price: Decimal
    stock_quantity: int
    active: bool
    model_config = {"from_attributes": True}


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal
    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    customer_id: int
    status: str
    order_date: datetime
    total: Decimal
    items: list[OrderItemOut]
    model_config = {"from_attributes": True}


class QuoteItemIn(BaseModel):
    sku: str
    quantity: int = Field(gt=0)


class QuoteCreate(BaseModel):
    customer_id: int
    items: list[QuoteItemIn]
    request_id: str


class QuoteOut(BaseModel):
    id: int
    customer_id: int
    status: str
    total: Decimal
    request_id: str
    model_config = {"from_attributes": True}


class SalesSummaryOut(BaseModel):
    total_sales: Decimal
    order_count: int
    by_day: list[dict]
    by_status: list[dict]


class TicketCreate(BaseModel):
    customer_id: int
    subject: str = Field(max_length=300)
    description: str
    request_id: str


class TicketOut(BaseModel):
    id: int
    customer_id: int
    subject: str
    status: str
    request_id: str
    model_config = {"from_attributes": True}
