from django.contrib.auth.models import User
from pytils.translit import slugify
from django.core.validators import RegexValidator
from django.db.models import Model, OneToOneField, CharField, ManyToManyField,\
    BooleanField, EmailField, TextField, ImageField, ForeignKey, BooleanField,\
        SlugField, DateTimeField, CASCADE, SET_NULL 


class Profile(Model):
    user = OneToOneField(User, on_delete=CASCADE)
    name = CharField(max_length=50, blank=True, null=True)
    email = EmailField(max_length=50, blank=True, null=True)
    phone_number = CharField(
        max_length=15, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: \
                    '+999999999'. Up to 15 digits allowed."
            )
        ],
        null=True
    )
    username = CharField(max_length=50, blank=True, null=True)
    summary = CharField(max_length=100, blank=True, null=True)
    city = CharField(max_length=20, blank=True, null=True)
    profession = CharField(max_length=50, blank=True, null=True)
    about = TextField(blank=True, null=True)
    image = ImageField(
        null=True, 
        blank=True, 
        upload_to='profile_images', 
        default='profile_images/default.jpg'
    )
    follows = ManyToManyField(
        'self', related_name='followed_by', 
        symmetrical=False, blank=True
    )


    class Meta:
        ordering = ['created']
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return self.user.username


class Interest(Model):
    name = CharField(max_length=50, blank=True, null=True)
    slug = SlugField()
    description = TextField(null=True, blank=True)
    created = DateTimeField(auto_now_add=True)
    profile = ForeignKey(Profile, null=True, blank=True, on_delete=CASCADE)

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['created']
        verbose_name = 'Интерес'
        verbose_name_plural = 'Интересы'
        unique_together = ('name', 'slug', 'profile')

    def __str__(self):
        return self.name


class Message(Model):
    sender = ForeignKey(Profile, on_delete=SET_NULL, null=True, blank=True)
    recipient = ForeignKey(
        Profile, on_delete=SET_NULL, null=True,
        blank=True, related_name='messages'
    )
    name = CharField(max_length=200, null=True, blank=True)
    email = EmailField(max_length=200, null=True, blank=True)
    subject = CharField(max_length=200, null=True, blank=True)
    body = TextField()
    is_read = BooleanField(default=False, null=True)
    created = DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject


    class Meta:
        ordering = ['is_read', '-created']
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'