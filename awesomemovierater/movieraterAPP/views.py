from django import forms
import requests
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from awesomemovierater import settings
from movieraterAPP.models import Movie, Rating

api_key = settings.TMDB_API_KEY

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating']
        widgets = {
            'rating': forms.NumberInput(
                attrs={
                    'class': 'w-100',
                    'type' : 'range',
                    'min' : '1',
                    'max' : '10',
                    'step' :'1',
                    'oninput' : 'updateRatingDisplay(this.value)'
                    }),
        }

class ImageForm(forms.ModelForm):

    class Meta:
        model = Movie
        exclude = ['id', 'picture', 'user' ]
        widgets = {
            'tmdb_id': forms.HiddenInput(), #versteckt ID im HTML - USer soll es nicht sheen
            'title': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'rating': forms.NumberInput(attrs={
                'class': 'form-range',
                'type': 'range',
                'min': '1',
                'max': '10',
                'step': '1',
                'oninput': 'updateRatingDisplay(this.value)'
            }),            'release_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actors': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'genre': forms.TextInput(attrs={'class': 'form-control'}),
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



# Create your views here.
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) #user direkt einloggen
            messages.success(request, f'Account erfolgreich erstellt! Du bist nun eingeloggt.')
            return redirect('overview')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})



@login_required
def overview(request):

    user_ratings = Rating.objects.filter(user=request.user).order_by('-created_at')
    count = user_ratings.count()

    trending_movies = []
    recommendations=[]
    last_movie = None

    #get Trending Movies
    try:
        trending_url = f'https://api.themoviedb.org/3/trending/movie/week?api_key={api_key}&language=de-DE'
        r = requests.get(trending_url)
        if r.status_code == 200:
            trending_movies = r.json().get('results', [])[:6]
    except:
        pass

    #get recommendations (based on last movie added)
    if count > 0:
        last_rating = user_ratings[0]
        last_movie = last_rating.movie
        try:
            rec_url = f"https://api.themoviedb.org/3/movie/{last_movie.tmdb_id}/recommendations?api_key={api_key}&language=de-DE"
            r = requests.get(rec_url)
            if r. status_code == 200:
                recommendations = r.json().get('results', [])[:6]
        except:
            pass

    content = {
        'movies' : user_ratings,
        'count' : count,
        'trending_movies' : trending_movies,
        'recommendations' : recommendations,
        'last_movie' : last_movie,
    }
    return render(request, 'overview.html', content)

@login_required
def upload(request, rating_id=None):
    #alles auf rating ändern nichtmehr Movie
    instance = get_object_or_404(Rating, id=rating_id, user=request.user) if rating_id else None

    if request.method == 'POST':
        form = RatingForm(request.POST, instance=instance)
        if form.is_valid():
            #aus hidden Inputs Filmdaten holen
            tmdb_id = request.POST.get('tmdb_id')

            #Film aus Movie Tabelle holen oder Film erstellen
            movie, created = Movie.objects.get_or_create(
                tmdb_id=tmdb_id,
                defaults={
                    'title': request.POST.get('title'),
                    'release_date': request.POST.get('release_date'),
                    'description': request.POST.get('description'),
                    'actors': request.POST.get('actors'),
                    'genre': request.POST.get('genre'),
                }
            )

            #beim ersten mal Poster runterladen:
            poster_url = request.POST.get('tmdb_poster_url')
            if created and poster_url:
                try:
                    response = requests.get(poster_url)
                    if response.status_code == 200:
                        file_name = f"poster_{movie.tmdb_id}.jpg"
                        movie.picture.save(file_name, ContentFile(response.content), save=True)
                except:
                    pass

            #Rating speicher -> verknüpfen
            rating = form.save(commit=False)
            rating.user = request.user
            rating.movie = movie

            #Duplikaten Check (pro User film nur 1 mal bewerten)
            if not rating_id and Rating.objects.filter(user=request.user, movie=movie).exists():
                messages.error(request, "Du hast diesen Film bereits bewertet!")
                return redirect('overview')

            rating.save()
            return redirect('overview')

    else:
        form = RatingForm(instance=instance)

    #ID's rot Markieren
    existing_ids = list(Rating.objects.filter(user=request.user).values_list('movie__tmdb_id', flat=True))

    return render(request, 'upload.html', {
        'form': form,
        'is_edit': bool(rating_id),
        'existing_ids': existing_ids,
        'movie_instance': instance.movie if instance else None,
    })

def searchMovie(request):
    query = request.GET.get('query')
    if not query:
        return JsonResponse({'results': []})

    url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}' #&language=de-DE  maybe

    try:
        response = requests.get(url)
        response.raise_for_status()
        return JsonResponse(response.json())
    except requests.RequestException:
        return JsonResponse({'error': 'Fehler bei der API Anfrage'}, status = 500)

def get_movie_credits(request, tmdb_id):
    url = f'https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={api_key}'
    response = requests.get(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        #nur ersten 5 + formatieren
        cast = data.get('cast', [])[:5]
        formatted_actors = [f"{c['character']} :-> {c['name']}" for c in cast]

        return JsonResponse({'actors':"\n".join(formatted_actors)})
    except requests.RequestException:
        return JsonResponse({'error': 'Fehler bei der API Anfrage'}, status = 500)

def get_movie_details(request, tmdb_id):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&language=de-DE"
    try:
        response = requests.get(url)
        return JsonResponse(response.json())
    except:
        return JsonResponse({'error': 'Fehler bei der API Anfrage'}, status = 500)


def delete_movie(request, rating_id):
    rating = get_object_or_404(Rating,id=rating_id, user=request.user)
    if request.method == 'POST':
        title = rating.movie.title
        rating.delete()
        messages.success(request, f"Bewertung für '{title}' gelöscht.")
    return redirect('overview')