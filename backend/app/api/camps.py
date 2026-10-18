import re
import unicodedata
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy.orm import Session, joinedload

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models import Camp, CampModality, CampStatus, ModalityType, User

router = APIRouter()


class ModalityInput(BaseModel):
    type: ModalityType
    label: str


class CampInput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    city: str | None = None
    age: int | None = None
    min_age: int | None = None
    max_age: int | None = None
    capacity: int | None = None
    status: CampStatus | None = None
    modalities: list[ModalityInput] | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date doit être supérieure ou égale à start_date")
        return self


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-") or "camp"


def _camp_response(camp: Camp, public: bool = False):
    landing_page = camp.landing_page
    result = {
        "id": str(camp.id),
        "name": camp.name,
        "slug": camp.slug,
        "description": camp.description,
        "start_date": camp.start_date,
        "end_date": camp.end_date,
        "city": camp.city,
        "min_age": camp.min_age,
        "max_age": camp.max_age,
        "status": camp.status.value,
        "modalities": [
            {"type": modality.type.value, "label": modality.label}
            for modality in camp.modalities
        ],
        "landing_page": None if landing_page is None else {
            "season_theme": landing_page.season_theme.value,
            "hero_title": landing_page.hero_title,
            "hero_description": landing_page.hero_description,
            "published_at": landing_page.published_at,
        },
    }
    if not public:
        result.update({"organizer_id": str(camp.organizer_id), "capacity": camp.capacity})
    return result


def _ensure_camp_access(camp: Camp, user: User) -> None:
    from app.models import UserRole

    if camp.organizer_id != user.id and user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes.")


def _validate_updated_dates(camp: Camp, data: dict):
    start_date = data.get("start_date", camp.start_date)
    end_date = data.get("end_date", camp.end_date)
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{
                "type": "value_error",
                "loc": ["body", "end_date"],
                "msg": "Value error, end_date doit être supérieure ou égale à start_date",
                "input": end_date.isoformat(),
            }],
        )


@router.post("/camps", status_code=status.HTTP_201_CREATED)
def create_camp(
    payload: CampInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    if not data.get("name") or not data.get("start_date") or not data.get("end_date") or not data.get("capacity"):
        raise HTTPException(status_code=422, detail="name, dates et capacity sont obligatoires.")

    base_slug = _slugify(data["name"])
    slug = base_slug
    suffix = 2
    while db.query(Camp.id).filter(Camp.slug == slug).first() is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    age = data.get("age")
    camp = Camp(
        organizer_id=current_user.id,
        name=data["name"],
        slug=slug,
        description=data.get("description"),
        start_date=data["start_date"],
        end_date=data["end_date"],
        city=data.get("city") or "",
        min_age=data.get("min_age", age if age is not None else 0),
        max_age=data.get("max_age", age if age is not None else 0),
        capacity=data["capacity"],
        status=data.get("status") or CampStatus.DRAFT,
    )
    for modality_data in data.get("modalities", []):
        camp.modalities.append(CampModality(**modality_data))

    db.add(camp)
    db.commit()
    db.refresh(camp)
    return _camp_response(camp)


@router.get("/public/camps")
def list_public_camps(db: Session = Depends(get_db)):
    camps = db.query(Camp).options(joinedload(Camp.modalities)).filter(
        Camp.status == CampStatus.PUBLISHED
    ).all()
    return [_camp_response(camp, public=True) for camp in camps]


@router.get("/camps")
def list_camps(
    status_filter: CampStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Camp).options(joinedload(Camp.modalities))
    from app.models import UserRole

    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(Camp.organizer_id == current_user.id)
    if status_filter is not None:
        query = query.filter(Camp.status == status_filter)
    return [_camp_response(camp) for camp in query.all()]


@router.get("/camps/{slug}/public")
def get_public_camp(slug: str, db: Session = Depends(get_db)):
    camp = db.query(Camp).options(joinedload(Camp.modalities)).filter(Camp.slug == slug).first()
    if camp is None or camp.status != CampStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    return _camp_response(camp, public=True)


@router.patch("/camps/{camp_id}")
def update_camp(
    camp_id: uuid.UUID,
    payload: CampInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    camp = db.query(Camp).options(joinedload(Camp.modalities)).filter(Camp.id == camp_id).first()
    if camp is None:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    _ensure_camp_access(camp, current_user)
    data = payload.model_dump(exclude_unset=True)
    _validate_updated_dates(camp, data)
    for key in ("name", "description", "start_date", "end_date", "city", "capacity", "status"):
        if key in data:
            setattr(camp, key, data[key])
    if "age" in data:
        camp.min_age = camp.max_age = data["age"]
    if "min_age" in data:
        camp.min_age = data["min_age"]
    if "max_age" in data:
        camp.max_age = data["max_age"]
    if "modalities" in data:
        camp.modalities.clear()
        for modality_data in data["modalities"]:
            camp.modalities.append(CampModality(**modality_data))
    db.commit()
    db.refresh(camp)
    return _camp_response(camp)


@router.delete("/camps/{camp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camp(
    camp_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    camp = db.query(Camp).filter(Camp.id == camp_id).first()
    if camp is None:
        raise HTTPException(status_code=404, detail="Camp introuvable.")
    _ensure_camp_access(camp, current_user)
    db.delete(camp)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)