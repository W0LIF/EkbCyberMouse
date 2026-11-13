from sqlalchemy import (
    Column, String, Text, Float, Boolean, Integer, Date, Time, DateTime, ForeignKey, BigInteger
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from api.app.db import Base


class ServiceCenterModel(Base):
    __tablename__ = "service_centers"

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    opens_at = Column(Time, nullable=False, default="08:00")
    closes_at = Column(Time, nullable=False, default="22:00")

    staff = relationship("StaffModel", back_populates="service_center")


class AccessNodeModel(Base):
    __tablename__ = "access_nodes"

    id = Column(Text, primary_key=True)
    type = Column(Text, nullable=False)  # 'olt', 'switch'
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)

    orders = relationship("OrderModel", back_populates="access_node")


class WorkTypeModel(Base):
    __tablename__ = "work_types"

    code = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    profile = Column(Text, nullable=False)
    requires_height = Column(Boolean, nullable=False, default=False)
    norm_minutes = Column(Integer, nullable=False)
    deadline_hours = Column(Integer, nullable=True)
    deadline_days = Column(Integer, nullable=True)

    orders = relationship("OrderModel", back_populates="work_type")


class StaffModel(Base):
    __tablename__ = "staff"

    id = Column(Text, primary_key=True)
    service_center_id = Column(Text, ForeignKey("service_centers.id"), nullable=False)
    profile = Column(Text, nullable=False)  # 'installation', '3ltp', 'both'
    technologies = Column(ARRAY(Text), nullable=False)
    height_access = Column(Boolean, nullable=False, default=False)
    shift_start = Column(Time, nullable=False)
    shift_end = Column(Time, nullable=False)
    lunch_start = Column(Time, nullable=False)
    lunch_end = Column(Time, nullable=False)
    backpack_ont = Column(Integer, nullable=False, default=0)
    backpack_router = Column(Integer, nullable=False, default=0)
    backpack_tv = Column(Integer, nullable=False, default=0)

    service_center = relationship("ServiceCenterModel", back_populates="staff")
    orders = relationship("OrderModel", back_populates="assigned_staff")


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Text, primary_key=True)
    work_type_code = Column(Text, ForeignKey("work_types.code"), nullable=False)
    technology = Column(Text, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    address = Column(Text, nullable=True)
    access_node_id = Column(Text, ForeignKey("access_nodes.id"), nullable=True)
    registered_at = Column(DateTime(timezone=True), nullable=False)
    slot_start = Column(DateTime(timezone=True), nullable=False)
    slot_end = Column(DateTime(timezone=True), nullable=False)
    is_repeat = Column(Boolean, nullable=False, default=False)
    req_ont = Column(Integer, nullable=False, default=0)
    req_router = Column(Integer, nullable=False, default=0)
    req_tv = Column(Integer, nullable=False, default=0)
    status = Column(Text, nullable=False, default="pending")  # pending|planned|unassigned|pgp|done|cancelled
    pgp_group_id = Column(Text, nullable=True)
    assigned_staff_id = Column(Text, ForeignKey("staff.id"), nullable=True)
    planned_start = Column(DateTime(timezone=True), nullable=True)
    planned_end = Column(DateTime(timezone=True), nullable=True)
    unassigned_reason = Column(Text, nullable=True)

    work_type = relationship("WorkTypeModel", back_populates="orders")
    access_node = relationship("AccessNodeModel", back_populates="orders")
    assigned_staff = relationship("StaffModel", back_populates="orders")


class EventModel(Base):
    __tablename__ = "events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    received_at = Column(DateTime(timezone=True), nullable=False)
    type = Column(Text, nullable=False)  # new_order|cancel_visit|delay|staff_unavailable
    payload = Column(JSONB, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    response_ms = Column(Integer, nullable=True)


class PlanModel(Base):
    __tablename__ = "plans"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_date = Column(Date, nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSONB, nullable=False)