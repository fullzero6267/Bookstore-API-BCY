from sqlalchemy.orm import Session
from app.core.errors import raise_not_found

def get_or_404(db: Session, model, id_value, code: str = "RESOURCE_NOT_FOUND"):

    #공통 조회 유틸 없으면 404
    obj = db.query(model).filter(model.id == id_value).first()
    if not obj:
        raise_not_found(code)
    return obj