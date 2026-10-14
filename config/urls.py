from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from loja.views import RegistroView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/registro/", RegistroView.as_view(), name="registro"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include("loja.urls")),
]
