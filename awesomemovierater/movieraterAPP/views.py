from gc import get_objects

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
        exclude = ['id']
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
    instance = get_object_or_404(Movie, id=movie_id) if movie_id else None

    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            tmbd_id = form.cleaned_data.get('tmdb_id')
            if not movie_id and tmbd_id:
                messages.error(request, "Diesen Film hast du bereits bewertet, bitte Lösche ihn zuerst!")
            return render(request, 'upload.html', dict(form=form))

            movie = form.save(commit=False)
            # Prüfen ob eine TMDB Poster URL mitgesendet wurde
            poster_url = request.POST.get('tmdb_poster_url')
            if poster_url and not request.FILES.get('picture'):
                try:
                    response = requests.get(poster_url)
                    if response.status_code == 200:
                        file_name = f"poster_{movie.title.replace(' ', '_')}.jpg"
                        movie.picture.save(file_name, ContentFile(response.content),save=False)
                except Exception as e:
                    print(f"Fehler beim Herunterladen der Poster-URL: {e}")

            movie.save()
            return redirect('overview')
        return redirect('overview')

    else:
        form = ImageForm(instance=instance)
    return render(request, 'upload.html', dict(form=form))

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

