from http import HTTPStatus

from django.contrib.auth import get_user_model
# from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Group, Post


User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        cls.post = Post.objects.create(
            text='Текст тестовой записи',
            author=cls.user,
        )
        cls.slugs = {
            'index': '/',
            'group': f'/group/{cls.group.slug}/',
            'profile': f'/{cls.user}/',
            'post': f'/{cls.user}/{cls.post.id}/',
            'new_post': '/new/',
            'post_edit': f'/{cls.user}/{cls.post.id}/edit/'
        }
        cls.public_url = {
            cls.slugs['index']: 'index.html',
            cls.slugs['group']: 'group.html',
            cls.slugs['profile']: 'profile.html',
            cls.slugs['post']: 'post.html',
        }
        cls.private_url = {
            cls.slugs['new_post']: 'new_post.html',
            cls.slugs['post_edit']: 'new_post.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.forign_user = User.objects.create(username='foreign')
        self.authorized_foreign_client = Client()
        self.authorized_foreign_client.force_login(self.forign_user)
        self.authorized_client = Client()
        self.authorized_client.force_login(URLTests.user)

    def test_urls_are_available_without_authorization(self):
        """
        Проверка доступности главной страницы, страныцы группы,
        профиля пользователя, страницы поста
        """
        for page in URLTests.public_url.keys():
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_pages_available_to_authoriaed_users(self):
        """Проверка доступности публичных url авторизованным пользователям"""
        for page in URLTests.public_url.keys():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_redirects_guests_to_signup_page(self):
        """Проверяет редирект с /new/ для неавторизованных пользователей"""
        response = self.guest_client.get(
            URLTests.slugs['new_post'], follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next={URLTests.slugs["new_post"]}'
        )

    def test_templates(self):
        """URL-адрес использует соответствующий шаблон"""
        for slug, template in URLTests.public_url.items():
            with self.subTest(slug=slug):
                response = self.guest_client.get(slug)
                self.assertTemplateUsed(response, template)
        for slug, template in URLTests.private_url.items():
            with self.subTest(slug=slug):
                response = self.authorized_client.get(slug)
                self.assertTemplateUsed(response, template)

    def test_post_edit_redirects_non_author_and_guests(self):
        """
        Страница редактирования записи перенаправляет пользователей,
        не являющихся автором
        """
        non_author = self.authorized_foreign_client.get(
            URLTests.slugs['post_edit'], follow=True
        )
        guest = self.guest_client.get(URLTests.slugs['post_edit'], follow=True)
        self.assertRedirects(non_author, URLTests.slugs['post'])
        self.assertRedirects(
            guest,
            f'/auth/login/?next={URLTests.slugs["post_edit"]}'
        )

    def test_post_edit_available_for_author(self):
        """Страница редактирования записи доступна для автора"""
        response = self.authorized_client.get(URLTests.slugs["post_edit"])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_page_returns_correct_status(self):
        """Страницы ошибок возвращают корректный статус"""
        response = self.guest_client.get('uninplemented_url/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
