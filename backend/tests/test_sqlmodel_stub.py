from sqlmodel import Field, Session, SQLModel, create_engine, select


class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    value: int


def test_where_comparison_operators_and_first() -> None:
    engine = create_engine("sqlite:///test.db")
    with Session(engine) as session:
        session.add(Item(value=1))
        session.add(Item(value=2))
        session.add(Item(value=3))
        session.commit()

        gt_rows = session.exec(select(Item).where(Item.value > 1).order_by(Item.value.asc())).all()
        assert [row.value for row in gt_rows] == [2, 3]

        le_first = session.exec(select(Item).where(Item.value <= 2).order_by(Item.value.desc())).first()
        assert le_first is not None
        assert le_first.value == 2


def test_where_accepts_multiple_conditions() -> None:
    engine = create_engine("sqlite:///test2.db")
    with Session(engine) as session:
        session.add(Item(value=4))
        session.add(Item(value=5))
        session.commit()

        rows = session.exec(select(Item).where(Item.value >= 4, Item.value != 4)).all()
        assert [row.value for row in rows] == [5]
