import movieraterAPP.views
from django.conf import settings
from django.conf.urls.static import static

"""
URL configuration for awesomemovierater project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import movieraterAPP.views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("",movieraterAPP.views.overview, name='overview'),
    path("upload/",movieraterAPP.views.upload, name='upload'),
    path("edit/<int:movie_id>/", movieraterAPP.views.upload, name='edit_movie'),
    path("delete/<int:movie_id>/", movieraterAPP.views.delete_movie, name='delete_movie'),
    path("searchMovie/", movieraterAPP.views.searchMovie, name='searchMovie'),
    path("movie-credits/<int:tmdb_id>/", movieraterAPP.views.get_movie_credits, name='movie_credits')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
