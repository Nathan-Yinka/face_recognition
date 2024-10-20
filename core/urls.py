
from django.contrib import admin
from django.urls import path,include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Face Recognition API",
      default_version='v1',
      description="collect two images and compare them and then returns if they are alike or not",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="oludarenathaniel@gmail.com"),
      license=openapi.License(name="Nathan-Yinka"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/",include("face_rec.urls")),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
