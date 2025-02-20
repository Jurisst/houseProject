from django.urls import path
from .views import (HouseListView, HouseUpdateView, ProviderListView, ProviderUpdateView,
                    ServiceListView, ServiceUpdateView, ApartmentListView, ApartmentUpdateView,
                    MeterListView, MeterUpdateView, ConsumerListView, ConsumerUpdateView,
                    houses_apartments, houses_services, add_apartment_to_house, add_meter_to_apartment,
                    meters_by_apartment)
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("providers/", ProviderListView.as_view(), name='providers'),
    path("houses/", HouseListView.as_view(), name='houses'),
    path("services/", ServiceListView.as_view(), name='services'),
    path("apartments/", ApartmentListView.as_view(), name='apartments'),
    path("consumers/", ConsumerListView.as_view(), name='consumers'),
    path("meters/", MeterListView.as_view(), name='meters'),

    # add new objects
    path('add_provider', views.add_provider, name='add_provider'),
    path('add_service', views.add_service, name='add_service'),
    path('add_house', views.add_house, name='add_house'),
    path('add_consumer', views.add_consumer, name='add_consumer'),
    path('add_apartment', views.add_apartment, name='add_apartment'),
    path('add_meter', views.add_meter, name='add_meter'),

    # success pages
    path('success_provider/<int:provider_id>/', views.success_add_provider, name='success_provider'),
    path('success_service/<int:service_id>/', views.success_add_service, name='success_service'),
    path('success_house/<int:house_id>/', views.success_add_house, name='success_house'),
    path('success_consumer/<int:consumer_id>/', views.success_add_consumer, name='success_consumer'),
    path('success_apartment/<int:house_id>/<int:apartment_id>/', views.success_add_apartment, name='success_apartment'),
    path('success_meter/<int:meter_id>/<int:apartment_id>/', views.success_add_meter, name='success_meter'),

    # update objects
    path("houses/update_house/<slug:pk>/", HouseUpdateView.as_view(), name='house_update'),
    path("providers/update_provider/<slug:pk>/", ProviderUpdateView.as_view(), name='provider_update'),
    path("services/update_service/<slug:pk>/", ServiceUpdateView.as_view(), name='service_update'),
    path("meters/update_meter/<slug:pk>/", MeterUpdateView.as_view(), name='meter_update'),
    path("apartments/update_apartment/<slug:pk>/", ApartmentUpdateView.as_view(), name='apartment_update'),
    path("consumers/update_consumer/<slug:pk>/", ConsumerUpdateView.as_view(), name='consumer_update'),

    path("houses/<int:house_id>/apartments/", views.houses_apartments, name='apartments_by_house'),
    path("houses/<int:house_id>/services/", views.houses_services, name='services_by_house'),
    # path("houses/<int:house_id>/consumers/", views.houses_consumers, name='consumers_by_house'),
    # path("houses/<int:house_id>/providers/", views.houses_providers, name='providers_by_house'),
    # path("houses/<int:house_id>/meters/", views.houses_meters, name='meters_by_house'),

    path('houses/<int:house_id>/add_apartment', views.add_apartment_to_house, name='add_apartment_here'),
    path('houses/<int:house_id>/add_service', views.add_service_to_house, name='add_service_here'),

    path('apartment/<int:apartment_id>/add-meter/', views.add_meter_to_apartment, name='add_meter_to_apartment'),
    path('apartment/<int:apartment_id>/meters/', meters_by_apartment, name='meters_by_apartment'),

]