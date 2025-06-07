from django.urls import path

from api.urls import router
from .views import GenerateAddendumPDF, SicoobRequestViewSet


router.register("sicoob-requests", SicoobRequestViewSet, basename="sicoob-request")

urlpatterns = [
    path(
        "generate-addendum-pdf/",
        GenerateAddendumPDF.as_view(),
        name="generate-addendum-pdf",
    ),
]
