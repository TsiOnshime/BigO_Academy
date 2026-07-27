"""
URL configuration for config project.

NOTE: no app URLs are wired in yet — this project currently has domain/
and application/ layers only (no adapters/inbound/rest yet), so there are
no views to route to. This file will grow a
`path('api/v1/', include('adapters.inbound.rest.urls'))` line once that
layer exists, mirroring academic-service/config/urls.py.
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
