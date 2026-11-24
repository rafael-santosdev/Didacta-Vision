from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Film


class CatalogFilterTest(TestCase):
    def setUp(self):
        self.avengers = Film.objects.create(
            titulo='Vingadores',
            sinopse='Ação e ficção científica.',
            duracao=180,
            genero='Ação / Ficção Científica',
            tema='Cultura Pop',
            cartaz_horizontal='filmes/cartazes/horizontais/vingadores.jpg',
            ativo=True,
        )
        self.interstellar = Film.objects.create(
            titulo='Interestelar',
            sinopse='Uma viagem pelo espaço.',
            duracao=169,
            genero='Ficção Científica',
            tema='Astrofísica',
            cartaz_horizontal='filmes/cartazes/horizontais/interestelar.jpg',
            ativo=True,
        )
        self.drama = Film.objects.create(
            titulo='Drama',
            sinopse='Um drama.',
            duracao=100,
            genero='Drama',
            tema='Educação',
            cartaz_horizontal='filmes/cartazes/horizontais/drama.jpg',
            ativo=True,
        )

    def test_genre_filter_matches_component_of_compound_genre(self):
        response = self.client.get(reverse('didacta:index'), {'genero': 'Ação'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['page_obj'].object_list), [self.avengers])
        self.assertContains(response, 'Ação')

    def test_genre_filter_includes_compound_and_single_genres(self):
        response = self.client.get(reverse('didacta:index'), {'genero': 'Ficção Científica'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context['page_obj'].object_list),
            {self.avengers, self.interstellar},
        )
        self.assertNotContains(response, 'Nenhum filme encontrado nesta categoria')

    def test_genre_filter_features_latest_matching_film_and_its_horizontal_poster(self):
        agora = timezone.now()
        Film.objects.filter(pk=self.avengers.pk).update(created_at=agora - timedelta(days=1))
        Film.objects.filter(pk=self.interstellar.pk).update(created_at=agora)

        response = self.client.get(reverse('didacta:index'), {'genero': 'Ficção Científica'})

        self.assertEqual(response.context['destaque'], self.interstellar)
        self.assertContains(response, self.interstellar.cartaz_horizontal.url)

    def test_all_films_features_most_recent_film_and_its_horizontal_poster(self):
        agora = timezone.now()
        Film.objects.filter(pk=self.drama.pk).update(created_at=agora + timedelta(days=1))

        response = self.client.get(reverse('didacta:index'))

        self.assertEqual(response.context['destaque'], self.drama)
        self.assertContains(response, self.drama.cartaz_horizontal.url)

    def test_theme_filter_returns_only_matching_movies(self):
        response = self.client.get(reverse('didacta:index'), {'tema': 'Astrofísica'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['page_obj'].object_list), [self.interstellar])
        self.assertContains(response, 'Astrofísica')

    def test_unknown_genre_shows_filtered_empty_state(self):
        response = self.client.get(reverse('didacta:index'), {'genero': 'Categoria inexistente'})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['page_obj'].object_list)
        self.assertContains(response, 'Nenhum filme encontrado nesta categoria')
