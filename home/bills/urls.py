from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'),
    path('items/', views.items, name='items'),
    path("providers/", views.ProviderListView.as_view(), name='providers'),
    path("houses/", views.HouseListView.as_view(), name='houses'),
    path("services/", views.ServiceListView.as_view(), name='services'),
    path("apartments/", views.ApartmentListView.as_view(), name='apartments'),
    path("consumers/", views.ConsumerListView.as_view(), name='consumers'),
    path("meters/", views.MeterListView.as_view(), name='meters'),
    path("incoming_bills/", views.IncomingBillListView.as_view(), name='incoming_bills'),

    # add new objects
    path('add_provider', views.add_provider, name='add_provider'),
    path('add_service', views.add_service, name='add_service'),
    path('add_house', views.add_house, name='add_house'),
    path('add_consumer', views.add_consumer, name='add_consumer'),
    path('add_apartment', views.add_apartment, name='add_apartment'),
    path('add_meter', views.add_meter, name='add_meter'),
    path('add_incoming_bill', views.add_incoming_bill, name='add_incoming'), 


    # success pages
    path('success_provider/<int:provider_id>/', views.success_add_provider, name='success_provider'),
    path('success_service/<int:service_id>/', views.success_add_service, name='success_service'),
    path('success_service/<int:house_id>/<int:service_id>/', views.success_add_service, name='success_service'),
    path('success_house/<int:house_id>/', views.success_add_house, name='success_house'),
    path('success_consumer/<int:consumer_id>/', views.success_add_consumer, name='success_consumer'),
    path('success_apartment/<int:house_id>/<int:apartment_id>/', views.success_add_apartment, name='success_apartment'),
    path('success_meter/<int:meter_id>/<int:apartment_id>/', views.success_add_meter, name='success_meter'),
    path('success_meter/<int:meter_id>/<int:apartment_id>/<int:house_id>/', views.success_add_meter, name='success_meter'),
    path('success_incoming/<int:house_id>/<int:incoming_bill_id>/', views.success_add_incoming, name='success_incoming'),

    # update objects
    path("houses/update_house/<slug:pk>/", views.HouseUpdateView.as_view(), name='house_update'),
    path("providers/update_provider/<slug:pk>/", views.ProviderUpdateView.as_view(), name='provider_update'),
    path("services/update_service/<slug:pk>/", views.ServiceUpdateView.as_view(), name='service_update'),
    path("meters/update_meter/<slug:pk>/", views.MeterUpdateView.as_view(), name='meter_update'),
    path("consumers/update_consumer/<slug:pk>/", views.ConsumerUpdateView.as_view(), name='consumer_update'),
    path("apartments/update_apartment/<slug:pk>/", views.ApartmentUpdateView.as_view(), name='apartment_update'),
    path('incoming-bill/update/<int:pk>', views.IncomingBillUpdateView.as_view(), name='incoming_bill_update'),

    # house related urls
    path("houses/<int:house_id>/apartments/", views.houses_apartments, name='apartments_by_house'),
    path("houses/<int:house_id>/services/", views.houses_services, name='services_by_house'),
    path('apartment/<int:apartment_id>/meters/', views.meters_by_apartment, name='meters_by_apartment'),
    path('houses/<int:house_id>/meters/', views.houses_meters, name='meters_by_house'),
    path("houses/<int:house_id>/incoming_bills/", views.IncomingBillListView.as_view(), name='incoming_bills'),
    path("houses/<int:house_id>/consumers/", views.houses_consumers, name='consumers_by_house'),
    path("houses/<int:house_id>/providers/", views.houses_providers, name='providers_by_house'),

    path('houses/<int:house_id>/add_apartment', views.add_apartment_to_house, name='add_apartment_here'),
    path('houses/<int:house_id>/add_service', views.add_service_to_house, name='add_service_here'),
    path('apartment/<int:apartment_id>/add_meter/', views.add_meter_to_apartment, name='add_meter_to_apartment'),
    path('houses/<int:house_id>/add_incoming_bill/', views.add_incoming_bill, name='add_incoming'),
    path('meter/<int:meter_id>/readings/add/', views.add_meter_reading, name='add_meter_reading'),
    path('meter/<int:meter_id>/readings/add/<int:house_id>/', views.add_meter_reading, name='add_meter_reading'),
    path('meter/<int:meter_id>/readings/add/<int:house_id>/<int:apartment_id>/', views.add_meter_reading, name='add_meter_reading'),


    path('houses/<int:house_id>/calculate-public-bills/', views.calculate_public_bills, name='calculate_public_bills'),


    path('incoming-bill/<int:pk>/', views.IncomingBillDetailView.as_view(), name='incoming_bill_detail'),
    

    path('houses/<int:house_id>/consumption/', views.calculate_consumption, name='calculate_consumption'),

    path('meter/<int:meter_id>/readings/', views.meter_readings, name='meter_readings'),

    path("houses/<int:house_id>/apartments/update_apartment/<int:pk>/", 
         views.ApartmentUpdateView.as_view(), 
         name='apartment_update'),

    path('houses/<int:house_id>/total-bills/', views.calculate_total_bills, name='total_bills'),
    path('houses/<int:house_id>/total-bills/<int:year>/<int:month>/', views.calculate_total_bills, name='total_bills_with_date'),
    path('houses/<int:house_id>/apartments/<int:apartment_id>/bill/<int:year>/<int:month>/pdf/', 
         views.generate_apartment_bill_pdf, name='generate_apartment_bill_pdf'),

]