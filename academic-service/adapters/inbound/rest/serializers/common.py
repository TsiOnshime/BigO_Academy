"""
adapters/inbound/rest/serializers/common.py — Academic Service

Shared serializer building blocks used across every schema module.

Design notes (apply to every serializer in this package):

1. RESPONSE serializers use camelCase field names (matching the API spec
   in academics_service.yaml) with `source='snake_case_attr'` pointing at
   the domain dataclass attribute. DRF's Serializer works against either
   plain objects (via getattr) or dicts (via __getitem__), so the same
   serializer can render a `domain.models.Student` returned by a use case
   *or* a plain dict the view builds when a field needs data joined from
   more than one source (see "denormalized fields" below).

2. REQUEST serializers also use camelCase field names but with
   `source='snake_case_field'` — this means `serializer.validated_data`
   comes back already in snake_case, matching the use case Command
   dataclass field names 1:1. In most views this makes
   `SomeCommand(**serializer.validated_data)` just work.

3. Enum handling: domain enums are `class X(str, Enum)`. Do NOT rely on
   `str(enum_member)` for output — on this Python version (and many
   others) that returns `"ClassName.MEMBER"`, not the plain value. Use
   EnumValueField below for every response field backed by a domain enum.
   For request fields, use serializers.ChoiceField(choices=[...]); the
   view is responsible for turning the validated plain string back into
   the actual domain Enum when constructing a Command (serializers stay
   free of domain/application imports beyond enums' plain string values).

4. Denormalized fields — some response schemas include fields that don't
   live on the corresponding domain dataclass at all (e.g.
   StudentResponse.cohortName, MentorshipSessionResponse.teacherName,
   ContestResultsResponse.contestTitle). These are marked in comments as
   "view-supplied". The view (adapters/inbound/rest/views.py, next step)
   is responsible for building a dict with the extra key(s) added before
   handing data to the serializer — serializers never reach into repos
   themselves, that would break the hexagonal boundary.
"""
from rest_framework import serializers


class EnumValueField(serializers.Field):
    """
    Read-only field for rendering a domain Enum member as its plain string
    (or int, for YearPhase) value — e.g. StudentStatus.ACTIVE -> "ACTIVE".
    """

    def to_representation(self, value):
        return value.value if hasattr(value, "value") else value

    def to_internal_value(self, data):
        raise NotImplementedError(
            "EnumValueField is read-only. Use serializers.ChoiceField on "
            "request serializers instead."
        )


class PageMetaSerializer(serializers.Serializer):
    """
    Mirrors components.schemas.PageMeta. NOTE: none of the current
    application-layer list use cases (ListStudentsUseCase, etc.) return
    pagination metadata — they return a plain list. Building an actual
    PageMeta (page/size/totalElements/totalPages) is a views.py concern;
    this serializer just renders whatever the view computes and passes
    in, or is omitted from *ListResponse serializers when pagination
    isn't wired up yet.
    """

    page = serializers.IntegerField()
    size = serializers.IntegerField()
    totalElements = serializers.IntegerField(source="total_elements")
    totalPages = serializers.IntegerField(source="total_pages")