from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Movie(models.Model):
    #Globale Filmdaten (einmalig Speichern)
    tmdb_id = models.IntegerField(unique=True) #Für duplikate check
    title = models.CharField(max_length=255)
    release_date = models.DateField()
    actors = models.TextField()
    genre = models.CharField(max_length=100, blank=True)
    picture = models.ImageField(upload_to='', blank=True, null=True)
    description = models.TextField()


    def __str__(self):
        return self.title       #everytime the object is converted to str show:



class Rating(models.Model):
    #User -> Film
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')

    #personal data user -> Film
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie') #1 User kann nur 1 gleichen Film bewerten

    def __str__(self):
        return f'{self.user.username} bewertete {self.movie.title} mit {self.rating} /10'