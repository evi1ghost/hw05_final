from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.templates_and_names = {
            'about/author.html': 'about:author',
            'about/tech.html': 'about:tech'
        }

    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        """
        URL, генерируемый при помощи имени about:author
        и about:tech, доступены.
        """
        for name in StaticViewsTests.templates_and_names.values():
            with self.subTest(name=name):
                response = self.guest_client.get(reverse(name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_author_page_uses_correct_template(self):
        """При запросе к about:author и about:tech
        применяются ожидаемые шаблоны"""
        for template, name in StaticViewsTests.templates_and_names.items():
            with self.subTest(name=name):
                response = self.guest_client.get(reverse(name))
                self.assertTemplateUsed(response, template)
