import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models import Base, Customer, Product, Order, OrderItem


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Customer).limit(1))
        if result.scalar_one_or_none():
            print("Already seeded")
            return

        customers = [
            Customer(id=i, name=f"Customer {i}", email=f"c{i}@example.com", company=f"Company {i}")
            for i in range(1, 11)
        ]
        products = [
            Product(id=i, sku=f"SKU-{i:03d}", name=f"Product {i}", unit_price=Decimal(10 + i), stock_quantity=100)
            for i in range(1, 16)
        ]
        session.add_all(customers + products)
        await session.flush()

        base_date = datetime(2026, 1, 1)
        for i in range(1, 21):
            order = Order(
                id=i,
                customer_id=(i % 10) + 1,
                status="completed" if i % 3 else "pending",
                order_date=base_date + timedelta(days=i),
                total=Decimal("0"),
            )
            session.add(order)
            await session.flush()
            item = OrderItem(
                order_id=order.id,
                product_id=(i % 15) + 1,
                quantity=2,
                unit_price=Decimal(10 + (i % 15) + 1),
            )
            order.total = item.unit_price * item.quantity
            session.add(item)

        await session.commit()
        print("Seeded 10 customers, 15 products, 20 orders")


if __name__ == "__main__":
    asyncio.run(seed())
