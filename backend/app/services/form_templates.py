"""
Ready-made form templates (skjemamaler) — starting points for the builder,
Tally-style. Each template is a portable form definition (same shape as the
import/export format) that creates a draft the user can then tweak.
"""
from typing import List, Optional

# Each template: key, title, description, access_mode, fields[]. Field dicts use
# the same shape as FormFieldIn (field_type, label, help_text, required, options).
FORM_TEMPLATES: List[dict] = [
    {
        "key": "medlemsundersokelse",
        "title": "Medlemsundersøkelse",
        "description": "Kartlegg trivsel og innspill fra medlemmene.",
        "access_mode": "begge",
        "fields": [
            {"field_type": "kort_tekst", "label": "Navn", "required": False,
             "help_text": "Valgfritt – du kan svare anonymt."},
            {"field_type": "skala", "label": "Hvor fornøyd er du med klubben?",
             "required": True, "options": {"min": 1, "max": 5, "min_label": "Lite fornøyd", "max_label": "Svært fornøyd"}},
            {"field_type": "flervalg", "label": "Hvilke aktiviteter ønsker du mer av?",
             "required": False, "options": ["Trening", "Konkurranser", "Sosialt", "Kurs", "Dugnad"]},
            {"field_type": "lang_tekst", "label": "Har du forslag til forbedringer?", "required": False},
        ],
    },
    {
        "key": "arrangement_pamelding",
        "title": "Påmelding til arrangement",
        "description": "Samle påmeldinger med kontaktinfo og valg.",
        "access_mode": "begge",
        "fields": [
            {"field_type": "kort_tekst", "label": "Fullt navn", "required": True},
            {"field_type": "epost", "label": "E-post", "required": True},
            {"field_type": "enkeltvalg", "label": "Jeg melder meg på", "required": True,
             "options": ["Ja, jeg kommer", "Kanskje", "Nei, dessverre"]},
            {"field_type": "tall", "label": "Antall personer (inkl. deg)", "required": False},
            {"field_type": "lang_tekst", "label": "Allergier eller andre hensyn", "required": False},
        ],
    },
    {
        "key": "trening_tilbakemelding",
        "title": "Tilbakemelding etter trening",
        "description": "Kort evaluering medlemmene kan fylle ut anonymt.",
        "access_mode": "offentlig",
        "fields": [
            {"field_type": "skala", "label": "Hvordan var økta?", "required": True,
             "options": {"min": 1, "max": 5}},
            {"field_type": "ja_nei", "label": "Følte du deg ivaretatt?", "required": True},
            {"field_type": "lang_tekst", "label": "Hva var bra / hva kan bli bedre?", "required": False},
        ],
    },
    {
        "key": "kursevaluering",
        "title": "Kursevaluering",
        "description": "Evaluer et kurs eller en samling.",
        "access_mode": "begge",
        "fields": [
            {"field_type": "kort_tekst", "label": "Hvilket kurs?", "required": True},
            {"field_type": "skala", "label": "Faglig utbytte", "required": True, "options": {"min": 1, "max": 5}},
            {"field_type": "skala", "label": "Instruktør", "required": True, "options": {"min": 1, "max": 5}},
            {"field_type": "enkeltvalg", "label": "Vil du anbefale kurset?", "required": True,
             "options": ["Ja", "Kanskje", "Nei"]},
            {"field_type": "lang_tekst", "label": "Kommentarer", "required": False},
        ],
    },
    {
        "key": "kontakt",
        "title": "Kontaktskjema",
        "description": "La folk ta kontakt med klubben.",
        "access_mode": "offentlig",
        "fields": [
            {"field_type": "kort_tekst", "label": "Navn", "required": True},
            {"field_type": "epost", "label": "E-post", "required": True},
            {"field_type": "enkeltvalg", "label": "Hva gjelder henvendelsen?", "required": True,
             "options": ["Bli medlem", "Utstyr", "Trening", "Annet"]},
            {"field_type": "lang_tekst", "label": "Melding", "required": True},
        ],
    },
]

_BY_KEY = {t["key"]: t for t in FORM_TEMPLATES}


def list_templates() -> List[dict]:
    """Lightweight metadata for the template gallery."""
    return [
        {
            "key": t["key"],
            "title": t["title"],
            "description": t.get("description"),
            "access_mode": t.get("access_mode", "begge"),
            "field_count": len(t.get("fields", [])),
        }
        for t in FORM_TEMPLATES
    ]


def get_template(key: str) -> Optional[dict]:
    return _BY_KEY.get(key)
