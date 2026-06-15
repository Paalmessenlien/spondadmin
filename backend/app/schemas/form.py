"""
Pydantic schemas for the feedback / questionnaire system (skjema).
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.form import (
    FORM_ACCESS_MODES, FORM_FIELD_TYPES, FORM_STATUSES,
)

_STATUS_PATTERN = r"^(" + "|".join(FORM_STATUSES) + r")$"
_ACCESS_PATTERN = r"^(" + "|".join(FORM_ACCESS_MODES) + r")$"
_FIELD_TYPE_PATTERN = r"^(" + "|".join(FORM_FIELD_TYPES) + r")$"


# ---- fields -----------------------------------------------------------------

class FormFieldIn(BaseModel):
    """A field as sent by the builder. Order is the array index."""
    field_type: str = Field(pattern=_FIELD_TYPE_PATTERN)
    label: str = Field(min_length=1)
    help_text: Optional[str] = None
    required: bool = False
    options: Optional[Any] = None
    settings: Optional[dict] = None


class FormFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    field_type: str
    label: str
    help_text: Optional[str] = None
    required: bool
    options: Optional[Any] = None
    settings: Optional[dict] = None


# ---- forms (admin) ----------------------------------------------------------

class FormCreate(BaseModel):
    title: str = Field(default="Nytt skjema", min_length=1, max_length=255)
    description: Optional[str] = None
    access_mode: str = Field(default="begge", pattern=_ACCESS_PATTERN)
    one_response_per_user: bool = False
    settings: Optional[dict] = None


class FormUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    access_mode: Optional[str] = Field(default=None, pattern=_ACCESS_PATTERN)
    one_response_per_user: Optional[bool] = None
    settings: Optional[dict] = None


class FormFieldsUpdate(BaseModel):
    fields: List[FormFieldIn]


class FormDetail(BaseModel):
    """Full form for the builder/management UI."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    slug: str
    status: str
    access_mode: str
    one_response_per_user: bool
    settings: Optional[dict] = None
    created_by_admin_id: Optional[int] = None
    created_by_name: Optional[str] = None
    published_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    fields: List[FormFieldResponse] = []
    response_count: int = 0


class FormListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    status: str
    access_mode: str
    field_count: int = 0
    response_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None


class FormListResponse(BaseModel):
    forms: List[FormListItem]
    total: int


# ---- public fill ------------------------------------------------------------

class PublicFormField(BaseModel):
    """Field as exposed to a (possibly anonymous) respondent — no internal data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    field_type: str
    label: str
    help_text: Optional[str] = None
    required: bool
    options: Optional[Any] = None
    settings: Optional[dict] = None


class PublicForm(BaseModel):
    """Safe subset served to the public fill page."""
    id: int
    title: str
    description: Optional[str] = None
    slug: str
    status: str
    access_mode: str
    settings: Optional[dict] = None
    fields: List[PublicFormField] = []


class SubmitAnswer(BaseModel):
    field_id: int
    value: Any = None


class FormSubmission(BaseModel):
    answers: List[SubmitAnswer] = []
    # Optional name/email captured for an anonymous respondent.
    respondent_label: Optional[str] = Field(default=None, max_length=255)


# ---- responses + reports ----------------------------------------------------

class AnswerView(BaseModel):
    field_id: Optional[int] = None
    value: Any = None
    value_text: Optional[str] = None


class ResponseRow(BaseModel):
    id: int
    respondent_admin_id: Optional[int] = None
    respondent_name: Optional[str] = None
    is_anonymous: bool
    respondent_label: Optional[str] = None
    submitted_at: datetime
    answers: List[AnswerView] = []


class FormResponsesList(BaseModel):
    form_id: int
    title: str
    fields: List[FormFieldResponse] = []
    responses: List[ResponseRow] = []
    total: int
    skip: int
    limit: int


class QuestionReport(BaseModel):
    field_id: int
    label: str
    field_type: str
    answered_count: int = 0
    # Shape depends on field_type:
    #  - choice types: {"options": [{label, value, count, pct}], "other": [..]}
    #  - skala/tall:   {"avg", "min", "max", "distribution": {value: count}}
    #  - ja_nei:       {"ja": n, "nei": n}
    #  - text/dato/epost: {"samples": [str, ...], "total": n}
    summary: dict = {}


class FormReport(BaseModel):
    form_id: int
    title: str
    status: str
    response_count: int
    questions: List[QuestionReport] = []
