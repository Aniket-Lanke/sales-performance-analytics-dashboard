from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime,
    ForeignKey, Text, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="category", lazy="select")

    def to_dict(self):
        return {
            "category_id": self.category_id,
            "category_name": self.category_name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Region(Base):
    __tablename__ = "regions"

    region_id = Column(Integer, primary_key=True, autoincrement=True)
    region_name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="region", lazy="select")

    def to_dict(self):
        return {
            "region_id": self.region_id,
            "region_name": self.region_name,
            "code": self.code,
            "country": self.country,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_code = Column(String(50), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    segment = Column(String(50), default="Standard", index=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan", lazy="select")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            "customer_id": self.customer_id,
            "customer_code": self.customer_code,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "segment": self.segment,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(50), nullable=False, unique=True, index=True)
    product_name = Column(String(150), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False, index=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=False)
    sku = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product", lazy="select")

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "category_id": self.category_id,
            "category_name": self.category.category_name if self.category else None,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0.0,
            "cost_price": float(self.cost_price) if self.cost_price is not None else 0.0,
            "sku": self.sku,
            "is_active": self.is_active
        }


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(60), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    region_id = Column(Integer, ForeignKey("regions.region_id", ondelete="RESTRICT"), nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    order_timestamp = Column(DateTime, nullable=False)
    payment_method = Column(String(50), nullable=False, index=True)
    order_status = Column(String(50), nullable=False, default="Completed", index=True)
    shipping_cost = Column(Numeric(10, 2), default=0.00)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(12, 2), nullable=False)
    is_synthetic = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    region = relationship("Region", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="select")

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "order_number": self.order_number,
            "customer_id": self.customer_id,
            "customer_name": self.customer.full_name if self.customer else "Unknown",
            "region_id": self.region_id,
            "region_name": self.region.region_name if self.region else "Unknown",
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "payment_method": self.payment_method,
            "order_status": self.order_status,
            "shipping_cost": float(self.shipping_cost) if self.shipping_cost is not None else 0.0,
            "discount_amount": float(self.discount_amount) if self.discount_amount is not None else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount is not None else 0.0,
            "is_synthetic": self.is_synthetic,
            "items_count": len(self.items) if self.items else 0
        }


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_rate = Column(Numeric(5, 4), default=0.0000)
    total_price = Column(Numeric(12, 2), nullable=False)

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_positive_quantity"),
        Index("idx_items_order_product", "order_id", "product_id"),
    )

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def to_dict(self):
        return {
            "order_item_id": self.order_item_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else "Unknown",
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price is not None else 0.0,
            "discount_rate": float(self.discount_rate) if self.discount_rate is not None else 0.0,
            "total_price": float(self.total_price) if self.total_price is not None else 0.0
        }


class DataImportLog(Base):
    __tablename__ = "data_import_logs"

    import_id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    total_rows = Column(Integer, nullable=False)
    valid_records = Column(Integer, nullable=False)
    duplicate_rows = Column(Integer, nullable=False)
    missing_values_handled = Column(Integer, nullable=False)
    rejected_rows = Column(Integer, nullable=False)
    quality_score = Column(Numeric(5, 2), nullable=False)
    status = Column(String(50), nullable=False)
    audit_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "import_id": self.import_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "total_rows": self.total_rows,
            "valid_records": self.valid_records,
            "duplicate_rows": self.duplicate_rows,
            "missing_values_handled": self.missing_values_handled,
            "rejected_rows": self.rejected_rows,
            "quality_score": float(self.quality_score) if self.quality_score is not None else 0.0,
            "status": self.status,
            "audit_details": self.audit_details,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
