from django import forms
import requests
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from awesomemovierater import settings
from movieraterAPP.models import Movie

class ImageForm(forms.ModelForm):

    class Meta:
        model = Movie
        exclude = ['id', 'picture' ]
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
def overview(request):
    all_movies = Movie.objects.all()
    count = Movie.objects.count()
    return render(request, 'overview.html', dict(movies=all_movies, count=count))

def upload(request, movie_id=None):
    #Falls movie_id Übergeben, lade Objekt -> sonst None
    if movie_id:
        instance = get_object_or_404(Movie, id=movie_id)
    else:
        instance = None

    if request.method == 'POST':
        # instance=instance damit Django weiß: Das ist ein Update, kein neuer Film
        form = ImageForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            movie = form.save(commit=False)
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

    return render(request, 'upload.html', {'form': form, 'is_edit': bool(movie_id)})

def searchMovie(request):
    query = request.GET.get('query')
    if not query:
        return JsonResponse({'results': []})

    api_key = settings.TMDB_API_KEY
    url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}' #&language=de-DE  maybe

    try:
        response = requests.get(url)
        response.raise_for_status()
        return JsonResponse(response.json())
    except requests.RequestException:
        return JsonResponse({'error': 'Fehler bei der API Anfrage'}, status = 500)

def delete_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == 'POST':
        movie.delete()
        messages.success(request, f"'{movie.title}' wurde gelöscht.")
    return redirect('overview')