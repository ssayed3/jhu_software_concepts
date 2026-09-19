import os
from datetime import date

from sqlalchemy import Date, Float, Integer, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DB_NAME = "module3_db"
DB_USER = os.getenv("DB_USER", "sayedsayed")

DATABASE_URL = f"postgresql+psycopg://{DB_USER}@/{DB_NAME}"


class Base(DeclarativeBase):
    pass


class Applicant(Base):
    __tablename__ = "applicants"

    p_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program: Mapped[str | None] = mapped_column(Text)
    comments: Mapped[str | None] = mapped_column(Text)
    date_added: Mapped[date | None] = mapped_column(Date)
    url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    term: Mapped[str | None] = mapped_column(Text)
    us_or_international: Mapped[str | None] = mapped_column(Text)
    gpa: Mapped[float | None] = mapped_column(Float)
    gre: Mapped[float | None] = mapped_column(Float)
    gre_v: Mapped[float | None] = mapped_column(Float)
    gre_aw: Mapped[float | None] = mapped_column(Float)
    degree: Mapped[str | None] = mapped_column(Text)
    llm_generated_program: Mapped[str | None] = mapped_column(Text)
    llm_generated_university: Mapped[str | None] = mapped_column(Text)


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)