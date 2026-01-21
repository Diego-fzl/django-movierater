from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Movie(models.Model):


    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movies',null=True, blank=True)
    title = models.CharField(max_length=255)
    tmdb_id = models.IntegerField(null=True, blank=True) #Für duplikate check
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)])
    release_date = models.DateField()
    actors = models.TextField()
    genre = models.CharField(max_length=100, blank=True)
    picture = models.ImageField(upload_to='', blank=True, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title       #everytime the object is converted to str show:
