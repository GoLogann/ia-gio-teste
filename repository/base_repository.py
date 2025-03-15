from sqlalchemy.orm import Session
from typing import Type, TypeVar, Generic

T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, db: Session):
        self.db = db

    def add(self, obj: T):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, model: Type[T], obj_id: str) -> T:
        return self.db.query(model).get(obj_id)

    def delete(self, obj: T):
        self.db.delete(obj)
        self.db.commit()
