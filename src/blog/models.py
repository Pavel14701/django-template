from django.db.models import Model, CharField, SlugField, ForeignKey, TextField,\
    ManyToManyField, BooleanField, DateTimeField, CASCADE 
from django.contrib.auth.models import User
from users.models import Profile
from pytils.translit import slugify


class Category(Model):
    name = CharField('category', max_length=20)
    slug = SlugField()
    class Meta:
        ordering = ['id']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    def __str__(self):
        return self.name


class Tag(Model):
    name = CharField('tag', max_length=20)
    slug = SlugField()

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Post(Model):
    owner = ForeignKey(Profile, null=True, blank=True, on_delete=CASCADE)
    title = CharField(max_length=150)
    slug = SlugField()
    text = TextField(max_length=2000)
    category = ForeignKey(Category, on_delete=CASCADE)
    tags = ManyToManyField(Tag, blank=True)
    published = DateTimeField(auto_now_add=True)
    likes = ManyToManyField(User, related_name='post_likes', blank=True)
    bookmarks = ManyToManyField(User, related_name='bookmarks', blank=True)

    def get_unique_slug(self):
        slug = slugify(self.title)
        unique_slug = slug
        num = 1
        while Post.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}{num}"
            num += 1
        return unique_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.get_unique_slug()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-published']
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'

    def __str__(self):
        return f'{self.owner} {self.title}'

    def number_of_likes(self):
        return '' if self.likes.count() == 0 else self.likes.count()

    def number_of_bookmarks(self):
        return '' if self.bookmarks.count() == 0 else self.bookmarks.count()

    def number_of_comments(self):
        return '' if self.comments.count() == 0 else self.comments.filter(approved=True).count()


class Comment(Model):
    post = ForeignKey(Post, on_delete=CASCADE, related_name='comments')
    owner = ForeignKey(Profile, null=True, blank=True, on_delete=CASCADE)
    text = TextField()
    published = DateTimeField(auto_now_add=True)
    approved = BooleanField(default=False)

    class Meta:
        ordering = ['-published']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def approve(self):
        self.approved = True
        self.save()

    def __str__(self):
        return self.text