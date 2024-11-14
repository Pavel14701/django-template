from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import Question, Vote
from django.contrib import messages
from common.utils import paginate_objects, cache_query 


@login_required()
@cache_query('questions_list', 60 * 15)
def questions(request:HttpRequest) -> HttpResponse:
    questions = Question.objects.all()
    custom_range, questions = paginate_objects(request, questions, 3)
    context = {
        'questions': questions, 
        'custom_range': custom_range, 
        'profile': request.user.profile
    }
    return render(request, 'polls/questions.html', context)


@login_required()
def question(request:HttpRequest, question_id:str) -> HttpResponse:
    context = {
        'question': Question.objects.get(pk=question_id), 
        'profile': request.user.profile
    }
    return render(request, 'polls/question.html', context)


@login_required()
def results(request:HttpRequest, question_id:str) -> HttpResponse:
    question = get_object_or_404(Question, pk=question_id)
    votes = question.choice_set.select_related('question').all() 
    labels, data = zip(*[(item.name, item.votes) for item in votes])
    context = {
        'question': question, 
        'profile': request.user.profile, 
        'labels': labels, 
        'data': data
    }    
    return render(request, 'polls/results.html', context)


@login_required
def vote(request: HttpRequest, question_id: str) -> HttpResponseRedirect|HttpResponse:
    profile = request.user.profile
    question = get_object_or_404(Question, pk=question_id)
    if request.method != 'POST':
        return render(request, 'polls/question.html', {'question': question, 'profile': profile})
    choice_id = request.POST.get('choice')
    if not choice_id:
        messages.error(request, 'Вы не выбрали вариант ответа!')
        return render(request, 'polls/question.html', {'question': question, 'profile': profile})
    user_choice = question.choice_set.filter(pk=choice_id).first()
    if not user_choice:
        messages.error(request, 'Выбранный вариант ответа не существует!')
        return render(request, 'polls/question.html', {'question': question, 'profile': profile})
    if question.user_voted(request.user):
        messages.error(request, 'Вы уже голосовали в этом опросе.')
        return render(request, 'polls/question.html', {'question': question, 'profile': profile})
    user_choice.votes += 1
    user_choice.save()
    Vote.objects.create(user=request.user, question=question, choice=user_choice)
    return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))