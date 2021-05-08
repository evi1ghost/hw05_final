from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post


User = get_user_model()


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.post = Post.objects.create(
            text='Текст тестовой записи',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()

    def test_index_page_cache(self):
        """Главная страница кэшируется"""
        self.guest_client.get(reverse('posts:index'))
        key = make_template_fragment_key('index_page', [1])
        value = cache.get(key)
        self.assertIsNotNone(value)
