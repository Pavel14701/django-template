from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls')),    
    path('', include('users.urls')),
    path('', include('polls.urls')),
    path('', include('quizzes.urls')),
    
    
    path('', include('products.urls', namespace='mainapp')),
    path('', include('checkout.urls', namespace='checkout')),
    path('accounts/', include('allauth.urls')),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) +\
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)