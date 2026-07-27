"""
adapters/inbound/rest/views/teacher_views.py — Academic Service

POST/GET  /teachers/                       TeacherListCreateView
GET/PATCH /teachers/<teacher_id>/          TeacherDetailView
POST      /teachers/<teacher_id>/activate/    ActivateTeacherView
POST      /teachers/<teacher_id>/deactivate/  DeactivateTeacherView

GET+POST on `/teachers/` and GET+PATCH on `/teachers/<id>/` are combined
into single classes — see student_views.py's module docstring for why
(Django's URL resolver dispatches on pattern, not verb).

TeacherResponseSerializer needs no view-supplied fields — every field
(including assignedCohortIds) is already on domain.Teacher — so these
views render the domain object directly, no dict assembly needed.
"""
from rest_framework import status
from rest_framework.response import Response

from application.use_cases.teacher.activate_teacher import ActivateTeacherCommand
from application.use_cases.teacher.create_teacher import CreateTeacherCommand
from application.use_cases.teacher.deactivate_teacher import DeactivateTeacherCommand
from application.use_cases.teacher.get_teacher import GetTeacherCommand
from application.use_cases.teacher.list_teachers import ListTeachersCommand
from application.use_cases.teacher.update_teacher import UpdateTeacherCommand
from domain.enums import TeacherStatus
from infrastructure.config.dependencies import (
    get_activate_teacher_use_case,
    get_create_teacher_use_case,
    get_deactivate_teacher_use_case,
    get_get_teacher_use_case,
    get_list_teachers_use_case,
    get_update_teacher_use_case,
)

from ..serializers import (
    CreateTeacherSerializer,
    TeacherListResponseSerializer,
    TeacherResponseSerializer,
    UpdateTeacherSerializer,
)
from .base import BaseAcademicView


class TeacherListCreateView(BaseAcademicView):

    def post(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = CreateTeacherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_create_teacher_use_case()
            result = use_case.execute(
                CreateTeacherCommand(
                    user_id=data["user_id"],
                    full_name=data["full_name"],
                    email=data["email"],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            TeacherResponseSerializer(result.teacher).data,
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        status_param = request.query_params.get("status")

        try:
            use_case = get_list_teachers_use_case()
            teachers = use_case.execute(
                ListTeachersCommand(
                    status=TeacherStatus(status_param) if status_param else None
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(TeacherListResponseSerializer({"teachers": teachers}).data)


class TeacherDetailView(BaseAcademicView):

    def get(self, request, teacher_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            use_case = get_get_teacher_use_case()
            teacher = use_case.execute(GetTeacherCommand(teacher_id=teacher_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(TeacherResponseSerializer(teacher).data)

    def patch(self, request, teacher_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = UpdateTeacherSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_teacher_use_case()
            teacher = use_case.execute(
                UpdateTeacherCommand(
                    teacher_id=teacher_id,
                    full_name=data.get("full_name"),
                    email=data.get("email"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(TeacherResponseSerializer(teacher).data)


class ActivateTeacherView(BaseAcademicView):
    def post(self, request, teacher_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        try:
            use_case = get_activate_teacher_use_case()
            teacher = use_case.execute(ActivateTeacherCommand(teacher_id=teacher_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(TeacherResponseSerializer(teacher).data)


class DeactivateTeacherView(BaseAcademicView):
    def post(self, request, teacher_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        try:
            use_case = get_deactivate_teacher_use_case()
            teacher = use_case.execute(
                DeactivateTeacherCommand(teacher_id=teacher_id)
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(TeacherResponseSerializer(teacher).data)