from django.db.models import Model, CharField, BooleanField, ImageField, SlugField, ForeignKey,\
    TextField, FloatField, CASCADE
from django.urls import reverse


class Category(Model):
    title = CharField(max_length=300)
    primaryCategory = BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Категории"


class Product(Model):
    mainimage = ImageField(upload_to='products/', blank=True)
    name = CharField(max_length=300)
    slug = SlugField()
    category = ForeignKey(Category, on_delete=CASCADE)
    preview_text = TextField(max_length=200, verbose_name='Краткое описание')
    detail_text = TextField(max_length=1000, verbose_name='Описание')
    price = FloatField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("mainapp:product", kwargs={
            'slug': self.slug
        })
