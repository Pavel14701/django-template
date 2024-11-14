from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from .models import Profile, Interest, User
from .forms import CustomUserCreationForm, ProfileForm, InterestForm, MessageForm
from common.utils import paginate_objects, searchProfiles
from django.db.models import Q
from django.db import IntegrityError
from django.db.models.query import QuerySet
from common.utils import cache_query
# TO DO Add email auth requests
from django.conf import settings
from django.core.mail import send_mail


def landing(request: HttpRequest) -> HttpResponseRedirect|HttpResponse:
    if request.user.is_authenticated:
        return redirect('profiles')
    profiles, search_query = searchProfiles(request)
    custom_range, profiles = paginate_objects(request, profiles, 3)
    context = {
        'profiles': profiles, 
        'search_query': search_query,
        'custom_range': custom_range
    }
    return render(request, 'landing.html', context)


def landingLogin(request:HttpRequest) -> HttpResponseRedirect|HttpResponse:
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = User.objects.get(username=username)
        except Exception:
            messages.error(request, 'Такого пользователя нет в системе')
        user:User = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(
                request.GET['next'] if 'next' in request.GET else 'account'
            )
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return redirect('landing')


def profiles(request: HttpRequest) -> HttpResponse:
    profiles, search_query = searchProfiles(request)
    custom_range, profiles = paginate_objects(request, profiles, 3)
    context = {
        'profiles': profiles, 
        'search_query': search_query,
        'custom_range': custom_range
    }
    return render(request, 'users/profiles.html', context)


def loginUser(request: HttpRequest) -> HttpResponseRedirect|HttpResponse:
    if request.user.is_authenticated:
        return redirect('profiles')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            user = User.objects.get(username=username)
        except Exception:
            messages.error(request, 'Такого пользователя нет в системе')
        user = authenticate(request, 
            username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET['next'] if 'next' in request.GET else 'account')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'users/login_register.html')


def logoutUser(request:HttpRequest) -> HttpResponseRedirect:
    logout(request)
    messages.info(request, 'Вы вышли из учетной записи')
    return redirect('login')


def registerUser(request: HttpRequest) -> HttpResponseRedirect|HttpResponse:
    page = 'register'
    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            return _extracted_from_registerUser_7(form, request)
        else:
            messages.success(request, 'Во время регистрации возникла ошибка')
    context = {'page': page, 'form': form}
    return render(request, 
        'users/login_register.html', context)


def _extracted_from_registerUser_7(form:CustomUserCreationForm, request:HttpRequest) -> HttpResponseRedirect:
    user:User = form.save(commit=False)
    user.username = user.username.lower()
    user.save()
    messages.success(request, 'Аккаунт успешно создан!')
    login(request, user)
    return redirect('edit-account')


def userProfile(request:HttpRequest, username:str) -> HttpResponse:
    profile = Profile.objects.get(username=username)
    interests:QuerySet[Interest] = profile.interest_set.all()
    profiles:QuerySet[Profile] = profile.follows.all()
    custom_range, profiles = paginate_objects(request, 
        profiles, 3)
    context = {
        'profile': profile,
        'profiles': profiles,
        'interests': interests,
        'custom_range': custom_range
    }
    return render(request, 'users/user-profile.html', context)


@login_required 
def profiles_by_interest(request:HttpRequest, interest_slug:str) -> HttpResponse:
    interest = Interest.objects.filter(slug__icontains=interest_slug)
    profiles = Profile.objects.exclude(user=request.user).distinct()
    context = {'profiles': profiles.filter(Q(interest__in=interest))}
    return render(request, 'users/profiles.html', context)


@login_required
def userAccount(request:HttpRequest) -> HttpResponse:
    profile:Profile = request.user.profile
    interests = profile.interest_set.all()
    profiles = profile.follows.all()
    custom_range, profiles = paginate_objects(request, profiles, 3)
    context = {'profile': profile, 'profiles': profiles,
    'interests': interests, 'custom_range': custom_range}
    return render(request, 'users/account.html', context)


@login_required
def editAccount(request:HttpRequest) -> HttpResponseRedirect|HttpResponse:
    profile:str = request.user.profile
    form = ProfileForm(instance=profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, 
            instance=profile)
        if form.is_valid():
            form.save()
            return redirect('account')
    context = {'form': form}
    return render(request, 'users/profile_form.html', context)


@login_required
def createInterest(request: HttpRequest) -> HttpResponseRedirect|HttpResponse:
    profile:str = request.user.profile
    form = InterestForm()
    if request.method == 'POST':
        form = InterestForm(request.POST)
        if form.is_valid():
            interest:Interest = form.save(commit=False)
            interest.description = request.POST.get('description')
            interest.profile = profile
            try:
                interest.save()
                messages.success(request, 'Интерес добавлен')
                return redirect('account')
            except IntegrityError:
                form.add_error('name', 'У вас уже есть интерес с таким именем и слагом')
    context = {'form': form}
    return render(request, 'users/interest_form.html', context)


@login_required
def updateInterest(request: HttpRequest, interest_slug:str) -> HttpResponseRedirect|HttpResponse:
    profile:str = request.user.profile
    interest:str = profile.interest_set.get(slug=interest_slug)
    form = InterestForm(instance=interest)
    if request.method == 'POST':
        form = InterestForm(request.POST, instance=interest)
        if form.is_valid():
            form.save()
            messages.success(request, 'Интерес успешно обновлен')
            return redirect('account')
    context = {'form': form}
    return render(request, 'users/interest_form.html', context)


@login_required
def deleteInterest(request:HttpRequest, interest_slug:str) -> HttpResponseRedirect|HttpResponse:
    profile = request.user.profile
    interest = profile.interest_set.get(slug=interest_slug)
    if request.method == 'POST':
        interest.delete()
        messages.success(request, 'Интерес успешно удален')
        return redirect('account')
    context = {'object': interest}
    return render(request, 'delete_template.html', context)


@login_required
def inbox(request:HttpRequest) -> HttpResponse:
    profile = request.user.profile
    messageRequests = profile.messages.all()
    unreadCount = messageRequests.filter(is_read=False).count()
    context = {'messageRequests': messageRequests, 
    'unreadCount': unreadCount}
    return render(request, 'users/inbox.html', context)


@login_required
def viewMessage(request, pk):
    profile = request.user.profile
    message = profile.messages.get(id=pk)
    if message.is_read is False:
        message.is_read = True
        message.save()
    context = {'message': message}
    return render(request, 'users/message.html', context)



def createMessage(request:HttpRequest, username:str) -> HttpResponseRedirect|HttpResponse:
    recipient = Profile.objects.get(username=username)
    form = MessageForm()
    try:
        sender = request.user.profile
    except Exception:
        sender = None
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            return _extracted_from_createMessage_11(form, sender, recipient, request)
    context = {'recipient': recipient, 'form': form}
    return render(request, 'users/message_form.html', context)    


def _extracted_from_createMessage_11(
    form:MessageForm, sender:str, recipient:str, request:HttpRequest) -> HttpResponseRedirect:
    message = form.save(commit=False)
    message.sender = sender
    message.recipient = recipient
    if sender:
        message.name = sender.name
        message.email = sender.email
    message.save()
    messages.success(request, 
        'Сообщение успешно отправлено!')
    return redirect('user-profile', username=recipient.username)    


@login_required
def follow_unfollow(request:HttpRequest, username:str) -> HttpResponseRedirect:
    profile = Profile.objects.get(username=username)
    if request.method == 'POST':
        current_user_profile = request.user.profile
        data = request.POST
        action = data.get('follow')
        if action == 'follow':
            current_user_profile.follows.add(profile)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        elif action == 'unfollow':
            current_user_profile.follows.remove(profile)
        current_user_profile.save()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))