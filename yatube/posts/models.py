from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='Группа', max_length=200
    )
    slug = models.SlugField(max_length=100, db_index=True, unique=True)
    description = models.TextField()

    def __repr__(self):
        return f'Group: {self.title}'

    def __str__(self):
        return self.title[:30]


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts'
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, blank=True,
        null=True, related_name='posts',
        verbose_name='Группа'
    )
    image = models.ImageField(
        upload_to='posts/', blank=True, null=True, verbose_name='Изображение')

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date']


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments',
        verbose_name='Комментарий'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments'
    )
    text = models.TextField()
    created = models.DateTimeField('date published', auto_now_add=True)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="follower", verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="following", verbose_name='Автор'
    )

    def __str__(self):
        return f'Подписчики {self.author}'
