from django.core.urlresolvers import reverse

from . import AppEngineTestCase


class PasteListTestCase(AppEngineTestCase):
    def test_shows_list_of_pastes(self):
        url = reverse('paste_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
