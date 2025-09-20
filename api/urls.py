# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import * 
    

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'crm',CrmViewSet,basename='crm')


urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view(), name='register'),
    path('login/', UserLoginAPIView.as_view(), name='login'),
    path('password-reset/', PasswordResetRequestAPIView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),
    path('', include(router.urls)),
]