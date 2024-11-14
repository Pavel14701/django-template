from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Tag, Category
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from users.models import Profile
from .forms import PostForm, CommentForm
from common.utils import searchPosts, paginate_objects, cache_query
from django.db.models import QuerySet


@login_required
@cache_query(60*15)
def createPost(request:HttpRequest) -> HttpResponseRedirect|HttpResponse:
    profile = request.user.profile
    form = PostForm()
    if request.method == 'POST':
        request.POST.getlist('tags')
        newtags = request.POST.get('newtags').replace(',',  " ").split()
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save()
            post.owner = profile
            post.save()
            for tag in newtags:
                tag, created = Tag.objects.get_or_create(name=tag)
                post.tags.add(tag)
            return redirect("blog:my-blog")
    context = {'form': form}
    return render(request, "blog/post_form.html", context)


@login_required
@cache_query(60*15)    
def userBlog(request:HttpRequest, username:str):
    profile = Profile.objects.get(username=username)
    posts = profile.post_set.all()
    tags, categories = get_tags_categories(posts)
    custom_range, posts = paginate_objects(request, posts, 3)    
    context = {
        'profile': profile,
        'posts': posts,
        'tags': tags,
        'categories': categories,
        'custom_range': custom_range
    }
    return render(request, "blog/user-blog.html", context)


@login_required
@cache_query(60*15)
def post(request:HttpRequest, post_slug:str) -> HttpResponseRedirect|HttpResponse:
    post = Post.objects.get(slug=post_slug)
    profile = request.user.profile
    comments = post.comments.filter(approved=True)
    form = CommentForm()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        comment = form.save(commit=False)
        comment.post = post
        comment.owner = request.user.profile
        comment.save()
        messages.success(request, 'Ваш комментарий появится после проверки модератором')
        return redirect('blog:post', post_slug=post.slug)    
    return render(
        request, 'blog/single-post.html', {
            'post': post, 
            'profile': profile, 
            'comments': comments, 
            'form': form
        }
    )


def get_tags_categories(posts:QuerySet[Post]) -> tuple[QuerySet[Post], QuerySet[Post]]:
    categories = set()
    tags = set()
    for post in posts:
        categories.add(post.category)
        for tag in post.tags.all():
            tags.add(tag)
    return tags, categories


@login_required
@cache_query(60*15)
def myBlog(request:HttpRequest) -> HttpResponse:
    profile = request.user.profile
    posts = profile.post_set.all()
    tags, categories = get_tags_categories(posts)
    custom_range, posts = paginate_objects(request, posts, 3)
    context = {
        'profile': profile,
        'posts': posts, 
        'custom_range': custom_range,
        'tags': tags, 
        'categories': categories
    }
    return render(request, 'blog/my-blog.html', context)


@login_required
@cache_query(60 * 15)
def updatePost(request: HttpRequest, pk: int) -> HttpResponseRedirect | HttpResponse:
    profile = request.user.profile
    post = get_object_or_404(profile.post_set, id=pk)
    form = PostForm(instance=post)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            update_post_tags(post, request.POST.get('newtags'))
            return redirect('blog:my-blog')
    context = {'form': form, 'post': post}
    return render(request, "blog/post_form.html", context)


def update_post_tags(post: Post, newtags: None|str) -> None:
    if newtags:
        tags = newtags.replace(',', " ").split()
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(name=tag)
            post.tags.add(tag_obj)


@login_required
@cache_query(60*15)
def deletePost(request:HttpRequest, pk:int) -> HttpResponseRedirect|HttpResponse:
    profile = request.user.profile
    post = profile.post_set.get(id=pk)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:my-blog')
    context = {'object': post}
    return render(request, 'delete_template.html', context)


@login_required
@cache_query(60*15)
def like_post(request:HttpRequest, post_id:int) -> HttpResponseRedirect:
    if request.method == "POST":
        post = get_object_or_404(Post, pk=post_id)
        if not post.likes.filter(id=request.user.id).exists():
            post.likes.add(request.user)
        else:
            post.likes.remove(request.user)
        post.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
@cache_query(60*15)
def bookmark_post(request:HttpRequest, post_id:int) -> HttpResponseRedirect:
    if request.method == "POST":
        post = get_object_or_404(Post, pk=post_id)
        if not post.bookmarks.filter(id=request.user.id).exists():
            post.bookmarks.add(request.user)
        else:
            post.bookmarks.remove(request.user)            
        post.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))            


@login_required
@cache_query(60*15)
def friends(request:HttpRequest) -> HttpResponse:
    profile = request.user.profile
    posts = Post.objects.filter(owner__in=profile.follows.all())
    tags, categories = get_tags_categories(posts)
    posts, search_query = searchPosts(request)
    custom_range, posts = paginate_objects(request, posts, 3)
    context = {
        'profile': profile,
        'posts': posts,
        'search_query': search_query,
        'custom_range': custom_range,
        'tags': tags,
        'categories': categories
    }
    return render(request, 'blog/post_list.html', context)


@login_required
@cache_query(60*15)
def user_bookmarks(request:HttpRequest) -> HttpResponse:
    profile = request.user.profile
    user = request.user
    posts = Post.objects.filter(bookmarks__in=[user])
    tags, categories = get_tags_categories(posts)
    custom_range, posts = paginate_objects(request, posts, 3)
    context = {
        'profile': profile,
        "posts": posts, 
        'custom_range': custom_range,
        'tags': tags,
        'categories': categories
    }
    return render(request, "blog/post_list.html", context)


@login_required
@cache_query(60*15)
def posts_by_category(request:HttpRequest, category_slug:str) -> HttpResponse:
    profile = request.user.profile
    category = get_object_or_404(Category, slug=category_slug)
    posts = Post.objects.filter(category__slug__contains = category_slug)  
    tags, categories = get_tags_categories(posts)
    custom_range, posts = paginate_objects(request, posts, 3)
    context = {
        'profile': profile,
        'posts': posts,
        'custom_range': custom_range,
        'tags': tags,
        'category': category,
        'categories': categories
    }
    return render(request, "blog/post_list.html", context)  


@login_required
def posts_by_tag(request:HttpRequest, tag_slug:str) -> HttpResponse:
    profile = request.user.profile
    tag = get_object_or_404(Tag, slug=tag_slug)
    posts = Post.objects.filter(tags__in=[tag])
    tags, categories = get_tags_categories(posts)
    custom_range, posts = paginate_objects(request, posts, 3)
    context = {
        'profile': profile,
        'posts': posts,
        'custom_range': custom_range,
        'tags': tags,
        'tag': tag,
        'categories': categories
    }
    return render(request, "blog/post_list.html", context)     