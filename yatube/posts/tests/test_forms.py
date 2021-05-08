from collections import namedtuple
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post


User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostCreateFormTest(TestCase):
    @staticmethod
    def get_temp_image():
        small_png = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02'
                     b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\xf4"\x7f\x8a'
                     b'\x00\x00\x00\x11IDAT\x08\x99c```\xf8\xff\x9f\x81'
                     b'\xe1?\x00\t\xff\x02\xfe\xaa\x98\xdd\xaf\x00\x00'
                     b'\x00\x00IEND\xaeB`\x82')
        temp_name = next(tempfile._get_candidate_names()) + '.png'
        uploaded = SimpleUploadedFile(
            name=temp_name,
            content=small_png,
            content_type='image/png'
        )
        ImageFile = namedtuple('ImageFile', 'name file')
        return ImageFile(temp_name, uploaded)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Описание тестовой группы'
        )
        image = cls.get_temp_image()
        cls.post = Post.objects.create(
            text='Текст тестовой записи',
            author=cls.user,
            group=cls.group,
            image=image.file
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTest.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post_without_group(self):
        """
        Форма создает новую запись с изображением при незаполненом поле group
        """
        posts_count = Post.objects.count()
        image = PostCreateFormTest.get_temp_image()
        form_fields = {
            'text': 'Test post',
            'image': image.file
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse('posts:index'))
        self.assertTrue(
            Post.objects.filter(
                author=self.user,
                text=form_fields['text'],
                image=f'posts/{image.name}'
            ).exists()
        )

    def test_create_post_with_group(self):
        """Форма создает новую запись с указанием group"""
        posts_count = PostCreateFormTest.group.posts.count()
        image = PostCreateFormTest.get_temp_image()
        form_fields = {
            'group': PostCreateFormTest.group.id,
            'text': 'Test post',
            'image': image.file
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_fields,
            follow=True
        )
        self.assertEqual(
            PostCreateFormTest.group.posts.count(),
            posts_count + 1
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertTrue(
            PostCreateFormTest.group.posts.filter(
                author=PostCreateFormTest.user,
                text=form_fields['text'],
                image=f'posts/{image.name}'
            ).exists()
        )

    def test_post_will_not_be_created_without_text(self):
        """Невозможно создать запись с без текста"""
        posts_count = Post.objects.count()
        form_fields = {
            'text': ' '
        }
        response = self.authorized_client.post(
            reverse('posts:new_post'),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response, 'form', 'text', 'Пожалуйста введите текст сообщения'
        )

    def test_post_edit_page_does_not_create_new_post(self):
        """
        Запись может быть изменена через страницу /<username>/<post_id>/edit/.
        При этом не создается новых записей
        """
        posts_count = Post.objects.count()
        image = PostCreateFormTest.get_temp_image()
        form_fields = {
            'text': 'Test post',
            'image': image.file
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'username': PostCreateFormTest.user.username,
                    'post_id': PostCreateFormTest.post.id
                }
            ),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, reverse(
            'posts:post', kwargs={
                'username': PostCreateFormTest.user.username,
                'post_id': PostCreateFormTest.post.id
            }))
        self.assertTrue(
            Post.objects.filter(
                author=PostCreateFormTest.user,
                text=form_fields['text'],
                image=f'posts/{image.name}'
            ).exists()
        )

    def test_unauthorized_user_can_not_create_post(self):
        """Неавторизованный пользователь не может создать запись"""
        posts_count = Post.objects.count()
        form_fields = {
            'text': 'Test'
        }
        self.guest_client.post(
            reverse('posts:new_post'),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)


class CommentCreateFormTest(TestCase):
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
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentCreateFormTest.user)

    def test_comment_can_be_created_through_form(self):
        """Комментарий может быть создан через форму на странице поста"""
        comments_count = Comment.objects.filter(
            post=CommentCreateFormTest.post).count()
        form_fields = {
            'text': 'Test comment',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'username': CommentCreateFormTest.user.username,
                    'post_id': CommentCreateFormTest.post.id
                }
            ),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Comment.objects.filter(
            post=CommentCreateFormTest.post).count(), comments_count + 1)
        self.assertRedirects(response, reverse(
            'posts:post', kwargs={
                'username': CommentCreateFormTest.user.username,
                'post_id': CommentCreateFormTest.post.id
            }))
        self.assertTrue(
            Comment.objects.filter(
                author=CommentCreateFormTest.user,
                text=form_fields['text']
            ).exists()
        )

    def test_guest_user_can_not_comment_posts(self):
        """Неавторизованный пользователь не может оставлять комментарии"""
        comments_count = Comment.objects.filter(
            post=CommentCreateFormTest.post).count()
        form_fields = {
            'text': 'Test comment',
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'username': CommentCreateFormTest.user.username,
                    'post_id': CommentCreateFormTest.post.id
                }
            ),
            data=form_fields,
            follow=True
        )
        self.assertEqual(Comment.objects.filter(
            post=CommentCreateFormTest.post).count(), comments_count)
