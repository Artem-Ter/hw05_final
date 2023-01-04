from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from .models import Post, Group, Follow, User
from .utils import split_pages
from .forms import PostForm, CommentForm


VIEW_ELEMENTS = 10


# Главная страница
def index(request):
    '''Передаёт в шаблон posts/index.html
    десять объектов модели Post на каждой странице.'''
    template = 'posts/index.html'
    post_list = Post.objects.all()
    context = {
        'page_obj': split_pages(request, post_list, VIEW_ELEMENTS),
    }
    return render(request, template, context)


# Страница с групповыми постами
def group_posts(request, slug):
    '''Передаёт в шаблон posts/group_list.html
    десять объектов модели Post на каждой странице,
    отфильтрованных по полю group,
    и содержимое для тега <title>.'''
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': split_pages(request, post_list, VIEW_ELEMENTS),
    }
    return render(request, template, context)


def profile(request, username):
    """Передает автора с указнным username в шаблон posts/profile
    и его посты по 10 штук на страницу"""
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists())
    context = {
        'page_obj': split_pages(request, post_list, VIEW_ELEMENTS),
        'author': author,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Передает пост с указанной post_id в шабон posts/post_detail"""
    template = 'posts/post_detail.html'
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'),
        id=post_id
    )
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'page_obj': split_pages(request, comments, VIEW_ELEMENTS)
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Передает форму из PostForm в шаблон posts/create_post.html
    если форма заполнена верно,
    переводит пользователя на страницу с его профилем"""
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
        return render(request, template, {'form': form})

    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """Передает пост с указанным post_id в
    шаблон posts/create_post.html для редактирования.
    Если user не является авторам поста,
    переводит его на странцу с деталями этого поста"""
    post = get_object_or_404(Post, id=post_id)
    is_edit = True
    template = 'posts/create_post.html'

    if request.method == 'GET':
        if request.user != post.author:
            return redirect('posts:post_detail', post_id=post.id)
        form = PostForm(
            instance=post
        )

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post.id)

    context = {
        'form': form,
        'is_edit': is_edit,
        'post': post,
    }

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    """Добавляет комментарий к выбранному посту"""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post.id)


@login_required
def follow_index(request):
    """Выведит посты авторов, на которых подписан текущий пользователь"""
    template = 'posts/follow.html'
    following = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author')
    context = {
        'page_obj': split_pages(request, following, VIEW_ELEMENTS)
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if request.user.id != author.id:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
