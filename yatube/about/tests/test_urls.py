from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов /about/"""
        urls = ['/about/author/', '/about/tech/']
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_author_url_uses_correct_template(self):
        """Проверка шаблонов для адресов /about/"""
        templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for url, template in templates.items():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
