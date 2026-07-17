"""
adapters/inbound/rest/views/contest_views.py — Academic Service

POST/GET  /cohorts/<cohort_id>/contests/    ContestListCreateView
GET       /contests/<contest_id>/           GetContestView
POST/GET  /contests/<contest_id>/results/   ContestResultsView

GET+POST on `/cohorts/<id>/contests/` and POST+GET on
`/contests/<id>/results/` are combined into single classes — see
student_views.py's module docstring for why (Django's URL resolver
dispatches on pattern, not verb).

ContestResultsResponse needs a view-supplied `contestTitle` (see
serializers/contest.py docstring) — GetContestResultsUseCase only
returns the results list, so ContestResultsView.get() looks the contest
up via GetContestUseCase first for its title.
"""
from rest_framework import status
from rest_framework.response import Response

from application.use_cases.contest.create_contest import CreateContestCommand
from application.use_cases.contest.get_contest import GetContestCommand
from application.use_cases.contest.get_contest_results import (
    GetContestResultsCommand,
)
from application.use_cases.contest.list_contests import ListContestsCommand
from application.use_cases.contest.submit_contest_results import (
    ContestResultInput,
    SubmitContestResultsCommand,
)
from domain.enums import ContestStatus
from infrastructure.config.dependencies import (
    get_create_contest_use_case,
    get_get_contest_results_use_case,
    get_get_contest_use_case,
    get_list_contests_use_case,
    get_submit_contest_results_use_case,
)

from ..serializers import (
    ContestListResponseSerializer,
    ContestResponseSerializer,
    ContestResultsResponseSerializer,
    CreateContestSerializer,
    SubmitContestResultsSerializer,
)
from .base import BaseAcademicView


class ContestListCreateView(BaseAcademicView):

    def post(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = CreateContestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_create_contest_use_case()
            contest = use_case.execute(
                CreateContestCommand(
                    title=data["title"],
                    cohort_id=cohort_id,
                    external_contest_url=data["external_contest_url"],
                    scheduled_at=data["scheduled_at"],
                    problem_count=data.get("problem_count", 0),
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(
            ContestResponseSerializer(contest).data, status=status.HTTP_201_CREATED
        )

    def get(self, request, cohort_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        status_param = request.query_params.get("status")

        try:
            use_case = get_list_contests_use_case()
            contests = use_case.execute(
                ListContestsCommand(
                    cohort_id=cohort_id,
                    status=ContestStatus(status_param) if status_param else None,
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(ContestListResponseSerializer({"contests": contests}).data)


class GetContestView(BaseAcademicView):
    def get(self, request, contest_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            use_case = get_get_contest_use_case()
            contest = use_case.execute(GetContestCommand(contest_id=contest_id))
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(ContestResponseSerializer(contest).data)


class ContestResultsView(BaseAcademicView):

    def post(self, request, contest_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER")
        if forbidden:
            return forbidden

        serializer = SubmitContestResultsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            use_case = get_submit_contest_results_use_case()
            contest = use_case.execute(
                SubmitContestResultsCommand(
                    contest_id=contest_id,
                    results=[
                        ContestResultInput(
                            student_id=r["student_id"],
                            student_name=r.get("student_name", ""),
                            contest_rank=r["contest_rank"],
                            problems_solved=r["problems_solved"],
                            participated=r["participated"],
                        )
                        for r in data["results"]
                    ],
                )
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        return Response(ContestResponseSerializer(contest).data)

    def get(self, request, contest_id):
        payload = self.authenticate(request)
        forbidden = self.require_roles(payload, "ADMIN", "TEACHER", "STUDENT")
        if forbidden:
            return forbidden

        try:
            contest = get_get_contest_use_case().execute(
                GetContestCommand(contest_id=contest_id)
            )
            results = get_get_contest_results_use_case().execute(
                GetContestResultsCommand(contest_id=contest_id)
            )
        except Exception as exc:
            return self.handle_domain_exception(exc)

        body = {
            "contest_id": contest_id,
            "contest_title": contest.title,
            "results": results,
        }
        return Response(ContestResultsResponseSerializer(body).data)