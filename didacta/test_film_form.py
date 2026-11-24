from django.test import SimpleTestCase

from .formularios import FilmForm
from .models import Film


class FilmFormPosterFieldsTest(SimpleTestCase):
    def test_create_requires_vertical_and_horizontal_posters_without_url_field(self):
        form = FilmForm()

        self.assertTrue(form.fields['cartaz'].required)
        self.assertTrue(form.fields['cartaz_horizontal'].required)
        self.assertNotIn('cartaz_url', form.fields)

    def test_edit_keeps_existing_posters_and_requires_missing_horizontal(self):
        filme = Film(
            pk=1,
            cartaz='filmes/cartazes/vertical.jpg',
        )

        form = FilmForm(instance=filme)

        self.assertFalse(form.fields['cartaz'].required)
        self.assertTrue(form.fields['cartaz_horizontal'].required)

    def test_edit_does_not_require_reupload_of_existing_posters(self):
        filme = Film(
            pk=1,
            cartaz='filmes/cartazes/vertical.jpg',
            cartaz_horizontal='filmes/cartazes/horizontais/horizontal.jpg',
        )

        form = FilmForm(instance=filme)

        self.assertFalse(form.fields['cartaz'].required)
        self.assertFalse(form.fields['cartaz_horizontal'].required)
