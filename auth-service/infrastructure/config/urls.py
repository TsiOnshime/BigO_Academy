from django.urls import include, path
 
urlpatterns = [
    path('api/v1/', include('adapters.inbound.rest.urls')),
]