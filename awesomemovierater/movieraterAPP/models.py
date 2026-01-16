from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Movie(models.Model):
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    actors = models.TextField()
    genre = models.CharField(max_length=100)
    picture = models.ImageField(upload_to='', blank=True, null=True)
    description = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def __str__(self):
        return self.title       #everytime the object is converted to str show:
