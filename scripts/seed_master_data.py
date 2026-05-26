from app.crud.inventory import seed_inventory_locations
from app.db.session import SessionLocal


def seed_master_data() -> None:
    db = SessionLocal()
    try:
        seed_inventory_locations(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> None:
    seed_master_data()


if __name__ == "__main__":
    main()
