"""
URL configuration for eidiv project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import index, api_mitglied_agt
from core.forms import StyledAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),

    # Auth
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=StyledAuthenticationForm
        ),
        name='login'
    ),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # API
    path('api/mitglied/<int:pk>/agt', api_mitglied_agt, name='api_mitglied_agt'),

    # Apps
    path('einsatz/', include('einsatz.urls')),
    path('dienst/', include('dienst.urls')),
]


