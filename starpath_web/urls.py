"""
URL configuration for starpath_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from mi_app.views.landing_page.landing_page_views import LandingPage
from mi_app.views.chatbot.chatbot_api import ChatAPIView
from mi_app.views.chatbot.services.kb_api import KBItemAPIView


urlpatterns = [
    #path('admin/', admin.site.urls),
    path("", LandingPage.as_view(), name="home"),
    path("api/chat/", ChatAPIView.as_view(), name="api_chat"),
    path("api/kb/item/<str:item_id>/", KBItemAPIView.as_view(), name="api_kb_item"),
]
