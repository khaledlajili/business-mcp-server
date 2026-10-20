from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_internal_token
from app.database import get_db
from app.models import Customer, Order, OrderItem, Product, Quote, QuoteItem, SupportTicket
from app.schemas import (
    CustomerOut, OrderOut, ProductOut, QuoteCreate, QuoteOut,
    SalesSummaryOut, TicketCreate, TicketOut,
)

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_internal_token)])


@router.get("/customers", response_model=list[CustomerOut])
async def search_customers(
    query: str = Query(""),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Customer)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(Customer.name.ilike(like) | Customer.email.ilike(like))
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.refresh(order, ["items"])
    return order


@router.get("/inventory/{sku}", response_model=ProductOut)
async def check_inventory(sku: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Product).where(Product.sku == sku)
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="SKU not found")
    return product


@router.post("/quotes", response_model=QuoteOut, status_code=201)
async def create_quote(payload: QuoteCreate, db: AsyncSession = Depends(get_db)):
    customer = await db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Idempotency
    existing = await db.execute(select(Quote).where(Quote.request_id == payload.request_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Duplicate request_id")

    total = Decimal("0")
    quote_items = []
    for item in payload.items:
        stmt = select(Product).where(Product.sku == item.sku, Product.active.is_(True))
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=400, detail=f"Unknown or inactive SKU: {item.sku}")
        line_total = product.unit_price * item.quantity
        total += line_total
        quote_items.append(QuoteItem(product_id=product.id, quantity=item.quantity, unit_price=product.unit_price))

    quote = Quote(customer_id=payload.customer_id, status="draft", total=total, request_id=payload.request_id)
    db.add(quote)
    await db.flush()
    for qi in quote_items:
        qi.quote_id = quote.id
        db.add(qi)
    await db.commit()
    await db.refresh(quote)
    return quote


@router.get("/sales/summary", response_model=SalesSummaryOut)
async def sales_summary(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
):
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    stmt = select(Order).where(Order.order_date >= start_date, Order.order_date <= end_date)
    result = await db.execute(stmt)
    orders = result.scalars().all()

    total_sales = sum((o.total for o in orders), Decimal("0"))
    order_count = len(orders)

    by_status = {}
    by_day = {}
    for o in orders:
        by_status[o.status] = by_status.get(o.status, Decimal("0")) + o.total
        day = o.order_date.date().isoformat()
        by_day[day] = by_day.get(day, Decimal("0")) + o.total

    return SalesSummaryOut(
        total_sales=total_sales,
        order_count=order_count,
        by_day=[{"date": d, "total": t} for d, t in sorted(by_day.items())],
        by_status=[{"status": s, "total": t} for s, t in by_status.items()],
    )


@router.post("/support-tickets", response_model=TicketOut, status_code=201)
async def create_ticket(payload: TicketCreate, db: AsyncSession = Depends(get_db)):
    customer = await db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    existing = await db.execute(select(SupportTicket).where(SupportTicket.request_id == payload.request_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Duplicate request_id")

    ticket = SupportTicket(
        customer_id=payload.customer_id,
        subject=payload.subject,
        description=payload.description,
        status="open",
        request_id=payload.request_id,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket
