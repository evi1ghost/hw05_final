from django import forms
from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    text = forms.fields.CharField(
        label='Текст записи',
        widget=forms.Textarea,
        error_messages={'required': 'Пожалуйста введите текст сообщения'}
    )

    class Meta:
        model = Post
        fields = ['group', 'text', 'image']


class CommentForm(ModelForm):
    text = forms.fields.CharField(
        label='Текст комментария',
        widget=forms.Textarea,
        error_messages={'required': 'Пожалуйста введите текст комментария'}
    )

    class Meta:
        model = Comment
        fields = ['text']
