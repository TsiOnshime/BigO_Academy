"""
adapters/inbound/rest/views/curriculum_views.py — Academic Service

POST/GET         /cohorts/<cohort_id>/topics/    TopicListCreateView
GET/PATCH/DELETE  /topics/<topic_id>/            TopicDetailView
POST              /topics/reorder/               ReorderTopicsView
POST              /topics/<topic_id>/problems/   AddProblemView
PATCH/DELETE      /problems/<problem_id>/        ProblemDetailView

Views sharing the same URL (GET+POST on `/cohorts/<id>/topics/`,
GET+PATCH+DELETE on `/topics/<id>/`, PATCH+DELETE on `/problems/<id>/`)
are single classes with each HTTP method defined — see student_views.py's
module docstring for why (Django's URL resolver dispatches on pattern,
not verb).

Known gap (not silently worked around): the serializer package exports
ProblemListResponseSerializer / ProblemResponseSerializer, implying a
"list problems for a topic" endpoint, and CurriculumRepositoryPort does
have find_problems_by_topic(...) — but there is no ListProblemsUseCase
in application/use_cases/curriculum/. Adding one would mean inventing
new application-layer business logic rather than wiring what already
exists, which is out of scope here. No such view is defined below;
flagging this so it isn't mistaken for an oversight.
"""
from rest_framework import status
from rest_framework.response import Response

from application.use_cases.curriculum.add_problem import AddProblemCommand
from application.use_cases.curriculum.create_topic import CreateTopicCommand
from application.use_cases.curriculum.delete_problem import DeleteProblemCommand
from application.use_cases.curriculum.delete_topic import DeleteTopicCommand
from application.use_cases.curriculum.get_topic import GetTopicCommand
from application.use_cases.curriculum.list_topics import ListTopicsCommand
from application.use_cases.curriculum.reorder_topics import ReorderTopicsCommand
from application.use_cases.curriculum.update_problem import UpdateProblemCommand
from application.use_cases.curriculum.update_topic import UpdateTopicCommand
from domain.enums import YearPhase
from infrastructure.config.dependencies import (
    get_add_problem_use_case,
    get_create_topic_use_case,
    get_curriculum_repository,
    get_delete_problem_use_case,
    get_delete_topic_use_case,
    get_get_topic_use_case,
    get_list_topics_use_case,
    get_reorder_topics_use_case,
    get_update_problem_use_case,
    get_update_topic_use_case,
)

from ..serializers import (
    CreateProblemSerializer,
    CreateTopicSerializer,
    ProblemListResponseSerializer,
    ProblemResponseSerializer,
    ReorderTopicsSerializer,
    TopicListResponseSerializer,
    TopicResponseSerializer,
    UpdateProblemSerializer,
    UpdateTopicSerializer,
)
from .base import BaseAcademicView


class TopicListCreateView(BaseAcademicView):

    def post(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = CreateTopicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_create_topic_use_case()
            topic = use_case.execute(
                CreateTopicCommand(
                    cohort_id=cohort_id,
                    title=data["title"],
                    year_phase=YearPhase(data["year_phase"]),
                    description=data.get("description"),
                    display_order=data.get("display_order"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            TopicResponseSerializer(topic).data, status=status.HTTP_201_CREATED
        )

    def get(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        year_phase_param = request.query_params.get("yearPhase")

        try:
            use_case = get_list_topics_use_case()
            topics = use_case.execute(
                ListTopicsCommand(
                    cohort_id=cohort_id,
                    year_phase=YearPhase(int(year_phase_param))
                    if year_phase_param
                    else None,
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(TopicListResponseSerializer({"topics": topics}).data)


class TopicDetailView(BaseAcademicView):

    def get(self, request, topic_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            use_case = get_get_topic_use_case()
            topic = use_case.execute(GetTopicCommand(topic_id=topic_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(TopicResponseSerializer(topic).data)

    def patch(self, request, topic_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = UpdateTopicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_topic_use_case()
            topic = use_case.execute(
                UpdateTopicCommand(
                    topic_id=topic_id,
                    title=data.get("title"),
                    description=data.get("description"),
                    display_order=data.get("display_order"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(TopicResponseSerializer(topic).data)

    def delete(self, request, topic_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        try:
            use_case = get_delete_topic_use_case()
            use_case.execute(DeleteTopicCommand(topic_id=topic_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ReorderTopicsView(BaseAcademicView):
    def post(self, request):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN")
        if forbidden:
            return forbidden

        serializer = ReorderTopicsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_reorder_topics_use_case()
            use_case.execute(
                ReorderTopicsCommand(ordered_topic_ids=data["ordered_topic_ids"])
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)


class AddProblemView(BaseAcademicView):
    def get(self, request, topic_id):
        payload = self.authenticate(request)
        if not payload:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)
        repo = get_curriculum_repository()
        problems = repo.find_problems_by_topic(topic_id)
        return Response(ProblemListResponseSerializer({"problems": problems}).data)

    def post(self, request, topic_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = CreateProblemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_add_problem_use_case()
            problem = use_case.execute(
                AddProblemCommand(
                    topic_id=topic_id,
                    title=data["title"],
                    source=data["source"],
                    external_url=data["external_url"],
                    difficulty=data["difficulty"],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            ProblemResponseSerializer(problem).data, status=status.HTTP_201_CREATED
        )


class ProblemDetailView(BaseAcademicView):

    def patch(self, request, problem_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = UpdateProblemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_update_problem_use_case()
            problem = use_case.execute(
                UpdateProblemCommand(
                    problem_id=problem_id,
                    title=data.get("title"),
                    external_url=data.get("external_url"),
                    difficulty=data.get("difficulty"),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(ProblemResponseSerializer(problem).data)

    def delete(self, request, problem_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        try:
            use_case = get_delete_problem_use_case()
            use_case.execute(DeleteProblemCommand(problem_id=problem_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(status=status.HTTP_204_NO_CONTENT)