from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post


User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')
    return render(
        request,
        'new_post.html',
        {'form': form, 'is_new': True}
    )


def profile(request, username):
    user = get_object_or_404(
        User.objects.prefetch_related('posts'), username=username
    )
    post_list = user.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user in [
        follower.user for follower in Follow.objects.filter(author=user)
    ]:
        following = True
    return render(
        request, 'profile.html',
        {'page': page, 'author': user, 'following': following}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author').filter(
            author__username=username, id=post_id
        ))
    posts_count = Post.objects.filter(author__username=username).count()
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    following = False
    if request.user in [
        follower.user for follower in Follow.objects.filter(
            author=post.author
        )
    ]:
        following = True
    return render(
        request, 'post.html', {
            'author': post.author, 'post': post, 'posts_count': posts_count,
            'form': form, 'comments': comments, 'following': following
        }
    )


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        return redirect('posts:post', username, post_id)
    post = get_object_or_404(Post, id=post_id, author=author)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post', username, post_id)
    return render(request, 'new_post.html', {
        'form': form, 'is_new': False, 'post': post}
    )


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post_id = post_id
        comment.author = request.user
        comment.save()
    return redirect('posts:post', username, post_id)


@login_required
def follow_index(request):
    authors = [
        author.author for author in
        Follow.objects.filter(user=request.user)
    ]
    post_list = Post.objects.filter(author__in=authors)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'follow.html',
        {'page': page, 'follow': True}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(
        User.objects.prefetch_related('following').filter(username=username)
    )
    if request.user not in [
        follower.user for follower in author.following.all()
    ] and request.user != author:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.filter(
        user=request.user, author__username=username
    )
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
