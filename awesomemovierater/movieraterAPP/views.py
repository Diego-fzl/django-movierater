from django import forms
from django.shortcuts import render, redirect

from movieraterAPP.models import Movie

class ImageForm(forms.ModelForm):

    class Meta:
        model = Movie
        exclude = ['id']


# Create your views here.
def overview(request):
    all_movies = Movie.objects.all()
    count = Movie.objects.count()
    return render(request, 'overview.html', dict(movies=all_movies, count=count))

def upload(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('overview')


        return redirect('overview')
    else:
        form = ImageForm()
    return render(request, 'upload.html', dict(form=form))