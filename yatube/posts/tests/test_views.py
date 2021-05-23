from collections import namedtuple
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post
from ..forms import PostForm

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostsPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        cls.empty_group = Group.objects.create(
            title='Пустая группа',
            slug='empty',
            description='empty'
        )
        cls.user = User.objects.create(username='user')
        small_png = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02'
                     b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\xf4"\x7f\x8a'
                     b'\x00\x00\x00\x11IDAT\x08\x99c```\xf8\xff\x9f\x81'
                     b'\xe1?\x00\t\xff\x02\xfe\xaa\x98\xdd\xaf\x00\x00'
                     b'\x00\x00IEND\xaeB`\x82')
        uploaded = SimpleUploadedFile(
            name='simple.png',
            content=small_png,
            content_type='image/png'
        )
        cls.post = Post.objects.create(
            text='Текст тестовой записи',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.number_of_posts = Post.objects.count()
        Follow.objects.create(
            user=User.objects.create(username='follower'), author=cls.user
        )
        Values = namedtuple('Values', 'alias template kwargs')
        cls.urls = {
            'posts:index': Values('posts:index', 'index.html', None),
            'posts:group': Values(
                'posts:group', 'group.html', {'slug': cls.group.slug}
            ),
            'posts:new_post': Values('posts:new_post', 'new_post.html', None),
            'posts:post': Values('posts:post', 'post.html', {
                'username': cls.user.username,
                'post_id': cls.post.id
            }),
            'posts:profile': Values(
                'posts:profile', 'profile.html',
                {'username': cls.user.username}
            ),
            'posts:post_edit': Values('posts:post_edit', 'new_post.html', {
                'username': cls.user.username,
                'post_id': cls.post.id
            }),
            'posts:follow_index': Values(
                'posts:follow_index', 'follow.html', None
            )
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTest.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        for alias, template, kwargs in PostsPagesTest.urls.values():
            with self.subTest(alias=alias):
                response = self.authorized_client.get(
                    reverse(alias, kwargs=kwargs)
                )
                self.assertTemplateUsed(response, template)

    def templates_shows_correct_post_context(self, response, key):
        """Объект Post корректно передается в шаблон"""
        if isinstance(response.context[key], Page):
            first_post_object = response.context[key][0]
        else:
            first_post_object = response.context[key]
        self.assertEqual(
            str(first_post_object.author),
            PostsPagesTest.user.username,
            msg=f'Check context for {response.templates[0].name}'
        )
        self.assertEqual(
            first_post_object.text,
            PostsPagesTest.post.text,
            msg=f'Check context for {response.templates[0].name}'
        )
        self.assertEqual(
            first_post_object.group,
            PostsPagesTest.group,
            msg=f'Check context for {response.templates[0].name}'
        )
        self.assertEqual(
            PostsPagesTest.post.pub_date, first_post_object.pub_date,
            msg=f'Check context for {response.templates[0].name}'
        )
        self.assertEqual(
            first_post_object.image,
            PostsPagesTest.post.image,
            msg=f'Check context for {response.templates[0].name}'
        )

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            PostsPagesTest.urls['posts:index'].alias))
        self.templates_shows_correct_post_context(response, 'page')

    def test_group_page_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            PostsPagesTest.urls['posts:group'].alias,
            kwargs=PostsPagesTest.urls['posts:group'].kwargs)
        )
        group_object = response.context['group']
        group_title = group_object.title
        group_slug = group_object.slug
        group_description = group_object.description
        self.templates_shows_correct_post_context(response, 'page')
        self.assertEqual(group_title, PostsPagesTest.group.title)
        self.assertEqual(group_slug, PostsPagesTest.group.slug)
        self.assertEqual(group_description, PostsPagesTest.group.description)

    def test_empty_group_does_not_have_posts(self):
        """
        Записи не попадают в группу, которая не была указана при их создании
        """
        response = self.authorized_client.get(reverse(
            PostsPagesTest.urls['posts:group'].alias,
            kwargs={'slug': PostsPagesTest.empty_group.slug})
        )
        self.assertEqual(len(response.context['page']), 0)

    def new_post_template_shows_correct_context(self, response, url):
        """Шаблон new_post сформирован с правильным контекстом"""
        self.assertIsInstance(
            response.context['form'], PostForm, msg='Проверь работу {url}'
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(
                    form_field,
                    expected,
                    msg=f'Проверь работу {url}'
                )

    def test_new_post_view_send_correct_context(self):
        """new_post view-функция отдает корректный контекст"""
        response = self.authorized_client.get(reverse(
            PostsPagesTest.urls['posts:new_post'].alias))
        self.new_post_template_shows_correct_context(
            response, PostsPagesTest.urls['posts:new_post'].alias
        )
        self.assertTrue(response.context['is_new'])

    def test_post_edit_view_send_correct_context(self):
        """post_edit view-функция отдает корректный контекст"""
        response = self.authorized_client.get(reverse(
            PostsPagesTest.urls['posts:post_edit'].alias,
            kwargs=PostsPagesTest.urls['posts:post_edit'].kwargs))
        self.new_post_template_shows_correct_context(
            response, PostsPagesTest.urls['posts:post_edit'].alias
        )
        self.assertFalse(response.context['is_new'])

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с корректным контекстом"""
        response = self.authorized_client.get(reverse(
            PostsPagesTest.urls['posts:profile'].alias,
            kwargs=PostsPagesTest.urls['posts:profile'].kwargs
        ))
        self.templates_shows_correct_post_context(response, 'page')
        self.assertEqual(
            response.context['author'],
            response.context['page'][0].author
        )
        self.assertEqual(
            response.context['page'].paginator.count,
            PostsPagesTest.number_of_posts
        )
        self.assertFalse(
            response.context['following'],
            msg='following flag should be False for non-follower'
        )

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с корректным контекстом"""
        response = self.authorized_client.get(reverse(
            PostsPagesTest.urls['posts:post'].alias,
            kwargs=PostsPagesTest.urls['posts:post'].kwargs))
        self.templates_shows_correct_post_context(response, 'post')
        self.assertEqual(
            response.context['author'],
            response.context['post'].author
        )
        self.assertEqual(
            response.context['posts_count'],
            PostsPagesTest.number_of_posts
        )
        self.assertIsInstance(
            response.context['form'].fields['text'],
            forms.fields.CharField
        )
        self.assertFalse(
            response.context['following'],
            msg='following flag should be False for non-follower'
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user')
        cls.follower = User.objects.create(username='follower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests',
            description='Описание тестовой группы'
        )
        Post.objects.bulk_create([Post(
            text='Текст тестовой записи',
            author=cls.user,
            group=cls.group
        ) for _ in range(13)])
        Follow.objects.create(user=cls.follower, author=cls.user)
        Values = namedtuple('Values', 'alias kwargs')
        cls.urls = {
            'posts:index': Values('posts:index', None),
            'posts:group': Values(
                'posts:group', {'slug': cls.group.slug}
            ),
            'posts:profile': Values(
                'posts:profile', {'username': cls.user.username}
            ),
        }
        cls.follow_url = {
            'posts:follow_index': Values('posts:follow_index', None)
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)
        self.follower_client = Client()
        self.follower_client.force_login(PaginatorViewsTest.follower)

    def test_first_index_page_contain_ten_records(self):
        """Первая страница шаблонов содержит 10 записей"""
        responses = [self.authorized_client.get(reverse(
            alias, kwargs=kwargs))
            for alias, kwargs in PaginatorViewsTest.urls.values()]
        follow_response = self.follower_client.get(reverse(
            PaginatorViewsTest.follow_url['posts:follow_index'].alias))
        responses.append(follow_response)
        for response in responses:
            with self.subTest(response=response.templates[0]):
                self.assertEqual(
                    len(response.context.get('page').object_list), 10)

    def test_second_index_page_contain_three_records(self):
        """Вторая страница шаблонов содержит 3 записи"""
        responses = [self.authorized_client.get(reverse(
            alias, kwargs=kwargs) + '?page=2')
            for alias, kwargs in PaginatorViewsTest.urls.values()]
        follow_response = self.follower_client.get(reverse(
            PaginatorViewsTest.follow_url['posts:follow_index'].alias)
            + '?page=2')
        responses.append(follow_response)
        for response in responses:
            with self.subTest(response=response.templates[0]):
                self.assertEqual(
                    len(response.context.get('page').object_list), 3)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create(username='follower')
        cls.following_user = User.objects.create(username='following_user')
        Follow.objects.create(user=cls.follower, author=cls.following_user)
        cls.following_post = Post.objects.create(
            author=cls.following_user,
            text='Текст тестовой записи'
        )
        Values = namedtuple('Values', 'alias kwargs')
        cls.urls = {
            'posts:follow_index': Values('posts:follow_index', None),
            'posts:profile_follow': Values(
                'posts:profile_follow', {'username': cls.following_user}
            ),
            'posts:profile_unfollow': Values(
                'posts:profile_unfollow', {'username': cls.following_user}
            )
        }

    def setUp(self):
        self.following_client = Client()
        self.following_client.force_login(FollowTest.following_user)
        self.follower_client = Client()
        self.follower_client.force_login(FollowTest.follower)

    def test_authorized_user_can_follow_and_unfollow_authors(self):
        """Авторизованный пользователь может отменять подписки"""
        follow_count = Follow.objects.count()
        alias, kwargs = FollowTest.urls['posts:profile_unfollow']
        self.follower_client.get(reverse(alias, kwargs=kwargs))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_authorized_user_can_follow_authors(self):
        """Авторизованный пользователь может оформлять подписки"""
        follow_count = Follow.objects.count()
        alias, kwargs = FollowTest.urls['posts:profile_follow']
        self.follower_client.get(reverse(alias, kwargs=kwargs))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_posts_does_not_shows_in_favorites_of_non_followers(self):
        """Запись не отображается в ленте неподписанных пользователей"""
        response = self.following_client.get(reverse(
            FollowTest.urls['posts:follow_index'].alias))
        self.assertEqual(len(response.context['page']), 0)

    def test_followers_see_posts_of_favorite_author(self):
        """Записи пользователя отображаются в ленте подписчиков"""
        response = self.follower_client.get(reverse(
            FollowTest.urls['posts:follow_index'].alias))
        self.assertGreater(len(response.context['page']), 0)
