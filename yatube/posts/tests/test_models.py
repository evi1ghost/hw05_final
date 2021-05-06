from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Post, Group


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        user = User.objects.create(username='test_user')
        cls.post = Post.objects.create(
            text='Проверка работы модели Post',
            author=user
        )

    def test_object_name_is_text_field(self):
        """__str__  post - это первые 15 символов post.text"""
        post = PostModelTest.post
        expected_value = post.text[:15]
        self.assertEqual(
            expected_value,
            str(post),
            msg='Проверьте правильность вывода Post.__str__'
        )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа с количеством символов больше 30',
            slug='test',
            description='Описание тестовой группы'
        )

    def test_object_name_is_group_title_field(self):
        """__str__  group - это первые 30 символов group.title"""
        group = GroupModelTest.group
        expected_value = group.title[:30]
        self.assertEqual(
            expected_value,
            str(group),
            msg='Проверьте правильность вывода Group.__str__'
        )
