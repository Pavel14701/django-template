from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from common.utils import paginate_objects
from django.contrib.auth.decorators import login_required
from django.db.models import F
from .models import Quiz, Question, Answer, Choice, Result
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from common.utils import cache_query
from django.db.models import QuerySet


@login_required
@cache_query(60*15)
def quizzes(request:HttpRequest) -> HttpResponse:
    profile = request.user.profile
    quizzes = Quiz.objects.all()
    custom_range, quizzes = paginate_objects(request, quizzes, 3)
    context = {
        'quizzes': quizzes,
        'profile': profile, 
        'custom_range': custom_range
    }
    return render(request, 'quizzes/quizzes.html', context)


@login_required
@cache_query(60*15)
def display_quiz(request:HttpRequest, quiz_id:int) -> HttpResponseRedirect:
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    question = quiz.question_set.first()
    return redirect(reverse('quizzes:display_question', 
        kwargs={'quiz_id': quiz_id, 
        'question_id': question.pk}))


@login_required
@cache_query(60*15)
def display_question(request:HttpRequest, quiz_id:int, question_id:int) -> HttpResponse:
    profile = request.user.profile
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.question_set.all()
    current_question, next_question = None, None
    for ind, question in enumerate(questions):
        if question.pk == question_id:
            current_question = question
            if ind != len(questions) - 1:
                next_question = questions[ind + 1]
    context = {
        'quiz': quiz, 
        'question': current_question, 
        'next_question': next_question, 
        'profile': profile
    }
    return render(request,'quizzes/display.html',context)


@login_required
@cache_query(60*15)
def grade_question(request:HttpRequest, quiz_id:int, question_id:int) -> HttpResponse:
    question = get_object_or_404(Question, pk=question_id)
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    if not question.user_can_answer(request.user):
        return render(request, 'quizzes/partial.html', {
            'question': question,
            'error_message': 'Вы уже отвечали на этот вопрос.'
        })
    correct_answer = question.get_answers()
    is_correct = False
    try:
        is_correct = _process_answer(request, question, correct_answer)
        _update_result(request.user, quiz, is_correct)
    except (Answer.DoesNotExist, ValueError) as e:
        return render(request, 'quizzes/partial.html', {'question': question})
    return render(request, 'quizzes/partial.html', {
        'is_correct': is_correct,
        'correct_answer': correct_answer,
        'question': question
    })


def _process_answer(request:HttpRequest, question:Question, correct_answer:str) -> bool:
    if question.qtype == 'multiple':
        answers_ids = request.POST.getlist('answer')
        user_answers = [Answer.objects.get(pk=answer_id).name for answer_id in answers_ids]
        for answer_id in answers_ids:
            user_answer = Answer.objects.get(pk=answer_id)
            _save_choice(request.user, question, user_answer)
        return correct_answer == user_answers
    elif question.qtype == 'single':
        user_answer = question.answer_set.get(pk=request.POST['answer'])
        _save_choice(request.user, question, user_answer)
        return correct_answer == user_answer


def _save_choice(user:str, question:str, answer:str) -> None:
    choice = Choice(user=user, question=question, answer=answer)
    choice.save()


def _update_result(user:str, quiz:Quiz, is_correct:bool) -> None:
    result, created = Result.objects.get_or_create(user=user, quiz=quiz)
    if is_correct:
        result.correct = F('correct') + 1
    else:
        result.wrong = F('wrong') + 1
    result.save()


@login_required
@cache_query(60*15)
def quiz_results(request:HttpRequest, quiz_id:int) -> HttpResponse:
    profile = request.user.profile
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.question_set.all()
    results = Result.objects.filter(user=request.user, quiz=quiz).values()
    correct = [i['correct'] for i in results][0]
    wrong = [i['wrong'] for i in results][0]
    context = {
        'quiz': quiz, 
        'profile': profile, 
        'correct': correct, 
        'wrong': wrong, 
        'number': len(questions), 
        'skipped': len(questions) - (correct + wrong)
    }
    return render(request, 'quizzes/results.html', context)