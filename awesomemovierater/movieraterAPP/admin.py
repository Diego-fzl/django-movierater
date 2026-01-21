from django.contrib import admin
from django.contrib.auth.models import User

from movieraterAPP.models import Movie, Rating

# Register your models here.

admin.site.register(Movie)
admin.site.register(Rating)