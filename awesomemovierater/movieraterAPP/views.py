from django import forms
import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from awesomemovierater import settings
from movieraterAPP.models import Movie

api_key = settings.TMDB_API_KEY
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

@login_required
def overview(request):
    all_movies = Movie.objects.filter(user=request.user).order_by('-created_at')
    count = all_movies.count()

    trending_movies = []
    recommendations=[]
    last_movie = None

    #get Trending Movies
    try:
        trending_url = f'https://api.themoviedb.org/3/trending/movie/week?api_key={api_key}'
        r = requests.get(trending_url)
        if r.status_code == 200:
            trending_movies = r.json().get('results', [])[:6]
    except:
        pass

    #get recommendations (based on last movie added)
    if count > 0:
        last_movie = all_movies[0]
        if last_movie.tmdb_id:
            try:
                rec_url = f"https://api.themoviedb.org/3/movie/{last_movie.tmdb_id}/recommendations?api_key={api_key}"
                r = requests.get(rec_url)
                if r. status_code == 200:
                    recommendations = r.json().get('results', [])[:6]
            except:
                pass

    content = {
        'movies' : all_movies,
        'count' : count,
        'trending_movies' : trending_movies,
        'recommendations' : recommendations,
        'last_movie' : last_movie,
        }

    return render(request, 'overview.html', content)

@login_required
def upload(request, movie_id=None):
    #Falls movie_id Übergeben, lade Objekt -> sonst None
    if movie_id:
        instance = get_object_or_404(Movie, id=movie_id, user=request.user)
    else:
        instance = None

    if request.method == 'POST':
        # instance=instance damit Django weiß: Das ist ein Update, kein neuer Film
        form = ImageForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            tmdb_id = form.cleaned_data.get('tmdb_id')

            #Hier neuer Duplikat check -> nichtmehr unique in datamodel

            if not movie_id and tmdb_id:
                if Movie.objects.filter(user=request.user, tmdb_id=tmdb_id).exists():
                    messages.error(request, "Diesen Film hast du bereits bewertet!")
                    return render(request, 'upload.html', {'form': form, 'is_edit': False})

            movie = form.save(commit=False)
            movie.user = request.user

            poster_url = request.POST.get('tmdb_poster_url')
            # Nur herunterladen, wenn eine URL da ist UND (es ein neuer Film ist ODER die URL sich geändert hat)
            if poster_url:
                try:
                    response = requests.get(poster_url)
                    if response.status_code == 200:
                        file_name = f"poster_{movie.tmdb_id}.jpg"
                        movie.picture.save(file_name, ContentFile(response.content), save=False)
                except Exception as e:
                    print(f"Fehler beim Poster-Download: {e}")

            movie.save()
            return redirect('overview')

    else:
        form = ImageForm(instance=instance)

    # WICHTIG: IDs für das rote Markieren in der Suche (nur vom aktuellen User)
    existing_ids = list(Movie.objects.filter(user=request.user).values_list('tmdb_id', flat=True))

    return render(request, 'upload.html', {'form': form, 'is_edit': bool(movie_id), 'existing_ids': existing_ids})

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


def delete_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == 'POST':
        movie.delete()
        messages.success(request, f"'{movie.title}' wurde gelöscht.")
    return redirect('overview')