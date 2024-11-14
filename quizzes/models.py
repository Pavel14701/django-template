from django.db.models import Model, CharField, DateTimeField, TextChoices, ForeignKey,\
    BooleanField, IntegerField, CASCADE
from django.contrib.auth.models import User


class Quiz(Model):
    name = CharField(max_length=120)
    published = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['published']
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'


class Question(Model):
    class qtype(TextChoices):
        single = 'single'
        multiple = 'multiple'
    name = CharField(max_length=350)
    qtype = CharField(max_length=8, choices=qtype.choices, default=qtype.single)
    quiz = ForeignKey(Quiz, on_delete=CASCADE)
    explanation = CharField(max_length=550)

    def get_answers(self):
        if self.qtype == 'single':
            return self.answer_set.filter(is_correct=True).first()
        qs = self.answer_set.filter(is_correct=True).values()
        return [i.get('name') for i in qs]

    def user_can_answer(self, user):
        user_choices = user.choice_set.all()
        done = user_choices.filter(question=self)
        print(done)
        return not done.exists()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'


class Answer(Model):
    question = ForeignKey(Question, on_delete=CASCADE)
    name = CharField(max_length=200)
    is_correct = BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'


class Choice(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    question = ForeignKey(Question, on_delete=CASCADE)
    answer = ForeignKey(Answer, on_delete=CASCADE)


class Result(Model):
    quiz = ForeignKey(Quiz, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)
    correct = IntegerField(default=0)
    wrong = IntegerField(default=0)



