from django.db.models import Model, CharField, DateTimeField, ForeignKey, IntegerField, CASCADE
from django.contrib.auth.models import User


class Question(Model):
    name = CharField(max_length=300)
    published = DateTimeField(auto_now_add=True)

    def user_voted(self, user):
        user_votes = user.vote_set.all()
        done = user_votes.filter(question=self)
        return not done.exists()
    
    class Meta:
        ordering = ['published']
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.name


class Choice(Model):
    question = ForeignKey(Question, on_delete=CASCADE)
    name = CharField(max_length=200)
    votes = IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Варианты'
        verbose_name_plural = 'Варианты'

    def __str__(self):
        return self.name

class Vote(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    question = ForeignKey(Question, on_delete=CASCADE)
    choice = ForeignKey(Choice, on_delete=CASCADE)

    class Meta:
        verbose_name = 'Голосование'
        verbose_name_plural = 'Голосования'

    def __str__(self):
        return f'{self.question.name[:15]} - {self.choice.name[:15]} - {self.user.username}'

