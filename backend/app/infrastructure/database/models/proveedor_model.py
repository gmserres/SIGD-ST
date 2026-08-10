from sqlalchemy import Boolean, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ProveedorModel(Base):
    __tablename__ = "proveedores"
    __table_args__ = (
        UniqueConstraint(
            "cuit",
            name="uq_proveedores_cuit",
        ),
    )

    id_proveedor: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
    )
    cuit: Mapped[str] = mapped_column(
        String(11),
        nullable=False,
    )
    razon_social: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
