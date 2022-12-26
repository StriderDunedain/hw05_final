from datetime import datetime as dt

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

PPG = settings.POSTS_PER_PAGE
User = get_user_model()


# Technical Functions:
def paginator_func(posts, request):
    paginator = Paginator(posts, PPG)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


# Main Page
@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    page_obj = paginator_func(posts, request)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


# Group Posts
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_func(posts, request)
    context = {
        'page_obj': page_obj,
        'group': group
    }
    return render(request, 'posts/group_list.html', context)


# Profile
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = paginator_func(posts, request)
    following = request.user.is_authenticated and author.following.filter(
        user=request.user
    ).exists()
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


# Post Details
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


# Post Creator
@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    context = {
        'form': form,
        'is_edit': False
    }
    if form.is_valid():
        temp_form = form.save(commit=False)
        temp_form.author = request.user
        temp_form.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', context)


# Post Editing
@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        post.edited = dt.now()
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


# Comment Creation
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


# Author's Posts
@login_required
def follow_index(request):
    posts_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_func(posts_list, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


# Subscription
@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.update_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


# Unsubscribtion
@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(author=author, user=request.user)
    if follow.exists():
        follow.delete()
    return redirect('posts:profile', username)
