from django.core.urlresolvers import reverse

from . import AppEngineTestCase


class PasteListTestCase(AppEngineTestCase):
    def test_shows_list_of_pastes(self):
        url = reverse('paste_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class ApiStarTestCase(AppEngineTestCase):
    def test_star_a_paste(self):
        url = reverse('api_star')

        paste = Paste.objects.create()

        data = {
            'paste': paste.pk,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)

