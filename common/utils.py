from functools import wraps
from typing import Tuple, Any
from django.core.cache import cache
from users.models import Profile, Interest
from blog.models import Tag, Post
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import BaseManager
from django.db.models import Q
from django.http import HttpRequest


def paginate_objects(request: HttpRequest, objects: Any, results: int) -> Tuple[range, Any]:
    page = request.GET.get('page', 1)
    paginator = Paginator(objects, results)
    try:
        objects = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        objects = paginator.page(1 if isinstance(page, str) and not page.isdigit() else paginator.num_pages)
    left_index = max(int(page) - 4, 1)
    right_index = min(int(page) + 5, paginator.num_pages + 1)
    custom_range = range(left_index, right_index)
    return custom_range, objects


def searchProfiles(request:HttpRequest) -> tuple[BaseManager[Profile], str|None]:
    search_query = ''
    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')
    interest = Interest.objects.filter(name__icontains=search_query)
    if request.user.is_authenticated:
        profiles = Profile.objects.exclude(user=request.user).distinct().filter(
        Q(name__icontains=search_query) |
        Q(summary__icontains=search_query) |
        Q(interest__in=interest)
    )
    else:
        profiles = Profile.objects.distinct().filter(
        Q(name__icontains=search_query) |
        Q(summary__icontains=search_query) |
        Q(interest__in=interest)
    )
    return profiles, search_query


def searchPosts(request:HttpRequest) -> tuple[BaseManager[Post], str|None]:
    profile = request.user.profile
    search_query = ''
    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')
    tags = Tag.objects.filter(name__icontains=search_query)
    posts = Post.objects.filter(
        owner__in=profile.follows.all()
    )
    posts = posts.distinct().filter(
        Q(title__icontains=search_query) |
        Q(text__icontains=search_query) |
        Q(owner__name__icontains=search_query) |
        Q(tags__in=tags)
    )
    return posts, search_query


def cache_query(timeout: int = 900):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = request.user.id
            method_name = view_func.__name__
            key = f"{method_name}_{user_id}"
            data = cache.get(key)
            if not data:
                data = view_func(request, *args, **kwargs)
                cache.set(key, data, timeout)
            return data
        return _wrapped_view
    return decorator