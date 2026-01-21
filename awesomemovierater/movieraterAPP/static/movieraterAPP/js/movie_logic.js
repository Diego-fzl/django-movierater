let timeout = null;
const genreMap = {
        28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
        80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
        14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
        9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
        10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
};

// 300ms nach Eingabe warten wegen API Limits
function debouncedSearch() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
        searchMovie();
    }, 300);
}

async function fillForm(movie) {
    // NEU: Anzeige-Texte im Info-Bereich befüllen
    if (document.getElementById('display-title')) document.getElementById('display-title').innerText = movie.title;
    if (document.getElementById('display-year')) document.getElementById('display-year').innerText = movie.release_date?.split('-')[0] || 'N/A';
    if (document.getElementById('display-description')) document.getElementById('display-description').innerText = movie.overview || movie.description;

    document.getElementById('movie-details-info').style.display = 'block';

    // easy daten
    if (document.getElementById('id_title')) document.getElementById('id_title').value = movie.title;
    if (document.getElementById('id_tmdb_id')) document.getElementById('id_tmdb_id').value = movie.id;
    if (document.getElementById('id_description')) document.getElementById('id_description').value = movie.overview;
    if (document.getElementById('id_release_date')) document.getElementById('id_release_date').value = movie.release_date;

    // Genres
    let ids = movie.genre_ids || (movie.genres ? movie.genres.map(g => g.id) : []);
    if (ids.length > 0) {
        const names = ids.map(id => genreMap[id]).filter(n => n).join(', ');
        if (document.getElementById('id_genre')) document.getElementById('id_genre').value = names;
        if (document.getElementById('display-genre')) document.getElementById('display-genre').innerText = names;
    }

    // Poster
    if (movie.poster_path) {
        const fullImageUrl = `https://image.tmdb.org/t/p/w500${movie.poster_path}`;
        document.getElementById('tmdb_poster_url').value = fullImageUrl;
        document.getElementById('preview-img').src = fullImageUrl;
        document.getElementById('poster-preview').style.display = 'block';
    }

    // Schauspieler nachladen, neuer fetch
    try {
        const res = await fetch(`/movie-credits/${movie.id}/`);
        const data = await res.json();
        if (document.getElementById('id_actors')) document.getElementById('id_actors').value = data.actors;
        if (document.getElementById('display-actors')) document.getElementById('display-actors').innerText = data.actors;
    } catch (e) { console.error("Credits Fehler", e); }

    document.getElementById('tmdb-search-input').value = movie.title;
}

// befüllen wenn URL mit tmdb ID ist
document.addEventListener('DOMContentLoaded', async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const tmdbId = urlParams.get('tmdb_id');

    if (tmdbId) {
        try {
            const response = await fetch(`/movie-details/${tmdbId}/`);
            const movie = await response.json();
            fillForm(movie);
        } catch (error) {
            console.error("Fehler beim Laden der URL-ID:", error);
        }
    }
});

// APi aufruf mit fillform
async function searchMovie() {
    const input = document.getElementById('tmdb-search-input');
    const query = input.value;
    const resultsDiv = document.getElementById('search-results');
    const existingIds = JSON.parse(input.getAttribute('data-existing-ids') || '[]');

    if (query.length < 2) return;

    try {
        const response = await fetch(`/searchMovie/?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        resultsDiv.innerHTML = '';
        resultsDiv.style.display = 'block';

        data.results.forEach(movie => {
            const isAlreadyRated = existingIds.includes(movie.id);
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            
            let content = `${movie.title} (${movie.release_date?.split('-')[0] || 'N/A'})`;
            if (isAlreadyRated) {
                content += ' <span class="badge bg-success rounded-pill">Bereits bewertet</span>';
                item.disabled = true;
            }
            
            item.innerHTML = content;

            // fillform
            if (!isAlreadyRated) {
                item.onclick = () => {
                    fillForm(movie);
                    resultsDiv.style.display = 'none';
                };
            }
            resultsDiv.appendChild(item);
        });
    } catch (error) { console.error('Suche Fehler:', error); }
}

// Schließen der Suchergebnisse beim Klicken außerhalb
document.addEventListener('click', function(event) {
    const resultsDiv = document.getElementById('search-results');
    if (resultsDiv && !event.target.closest('.input-group') && !event.target.closest('#search-results')) {
        resultsDiv.style.display = 'none';
    }
});

function updateRatingDisplay(val) {
    const display = document.getElementById('rating-value');
    if (display) {
        display.innerText = val;
    }
}

// Setze den initialen Wert beim Laden der Seite
document.addEventListener('DOMContentLoaded', () => {
    const slider = document.querySelector('input[type="range"]');
    if (slider) {
        updateRatingDisplay(slider.value);
    }
});
