from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('success_provider/<int:provider_id>/', views.success_add_provider, name='success_provider'),
    path('success_service/<int:service_id>/', views.success_add_service, name='success_service'),
    path('success_house/<int:house_id>/', views.success_add_house, name='success_house'),
    path('success_consumer/<int:consumer_id>/', views.success_add_consumer, name='success_consumer'),
    path('success_apartment/<int:apartment_id>/', views.success_add_apartment, name='success_apartment'),
    path('success_meter/<int:meter_id>/', views.success_add_meter, name='success_meter'),
    
    
    
    path('add_provider', views.add_provider, name='add_provider'),
    path('add_service', views.add_service, name='add_service'),
    path('add_house', views.add_house, name='add_house'),
    path('add_consumer', views.add_consumer, name='add_consumer'),
    path('add_apartment', views.add_apartment, name='add_apartment'),
    path('add_meter', views.add_meter, name='add_meter'),


]