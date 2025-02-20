from django.views.decorators.cache import cache_control
from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect,  get_object_or_404
from .forms import ProviderForm, ServiceForm, HouseForm, ConsumerForm, ApartmentForm, MeterForm, ApartmentForm2, ServiceForm2, MeterForm2
from .models import Provider, Service, House, Consumer, Apartment, Meter
from .help_functions import manage_db_table
from django.http import JsonResponse



def index(request):
    return render(request, 'index.html')


def success_add_provider(request, provider_id):
    provider = get_object_or_404(Provider, id=provider_id)  # Get the product instance
    return render(request, 'bills/sp_provider_add.html', {'provider': provider})


def success_add_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)  # Get the product instance
    return render(request, 'bills/sp_service_add.html', {'service': service})


def success_add_house(request, house_id):
    house = get_object_or_404(House, id=house_id)  # Get the product instance
    return render(request, 'bills/sp_house_add.html', {'house': house})


def success_add_consumer(request, consumer_id):
    consumer = get_object_or_404(Consumer, id=consumer_id)  # Get the product instance
    return render(request, 'bills/sp_consumer_add.html', {'consumer': consumer})


def success_add_apartment(request, house_id, apartment_id):
    house = get_object_or_404(House, id=house_id)  # Get the product instance
    apartment = get_object_or_404(Apartment, id=apartment_id)  # Get the product instance
    return render(request, 'bills/sp_apartment_add.html', {'house_id': house.id,  'apartment_id': apartment.id})


def success_add_meter(request, apartment_id, meter_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    meter = get_object_or_404(Meter, id=meter_id)
    return render(request, 'bills/sp_meter_add.html', {'apartment': apartment, 'meter': meter})


class HouseListView(ListView):
    template_name = 'customers_list.html'
    model = House
    context_object_name = "houses"


class HouseUpdateView(UpdateView):
    model = House
    fields = '__all__'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('houses')


class ProviderListView(ListView):
    model = Provider
    template_name = 'provider_list.html'
    context_object_name = "providers"


class ProviderUpdateView(UpdateView):
    model = Provider
    fields = '__all__'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('providers')


class ServiceListView(ListView):
    model = Service
    template_name = 'service_list.html'
    context_object_name = "services"


class ServiceUpdateView(UpdateView):
    model = Service
    fields = '__all__'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('services')


class ApartmentListView(ListView):
    model = Apartment
    template_name = 'customers_list.html'
    context_object_name = "apartments"
    ordering = ['apartment_nr']


class ApartmentUpdateView(UpdateView):
    model = Apartment
    fields = '__all__'
    template_name_suffix = "_update_form"
    context_object_name = 'apartment'

    def get_success_url(self):
        return reverse_lazy('apartments')


class ConsumerListView(ListView):
    model = Consumer
    template_name = 'customers_list.html'
    context_object_name = "consumers"


class ConsumerUpdateView(UpdateView):
    model = Consumer
    fields = '__all__'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('consumers')


class MeterListView(ListView):
    model = Meter
    template_name = 'customers_list.html'
    context_object_name = "meters"


class MeterUpdateView(UpdateView):
    model = Meter
    fields = '__all__'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('meters')



@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_provider(request):
    providers = Provider.objects.all()
    # assuming provider does not exist
    providers_list = []     # list to store tuples with existing providers' names and business form included
    reg_numbers = []     # list to store existing providers' registration numbers
    text = None     # to store error text
    for p in providers:
        company = p.name, p.business_form
        providers_list.append(company)
        reg_numbers.append(p.reg_number)

    if request.method == 'POST':
        form = ProviderForm(request.POST)
        if form.is_valid():
            name = form['name'].value()
            business_form = form['business_form'].value()
            name_and_form = name, business_form
            reg_number = form['reg_number'].value()
            if name_and_form in providers_list:
                text = f'Provider name {name.upper()} {business_form.upper()} is already registered'
            elif reg_number in reg_numbers:
                p = reg_numbers.index(reg_number)
                text = (f'Provider registration nr. {reg_number} is registered for company '
                        f'{providers_list[p][0].upper()} {providers_list[p][1].upper()}')
            if not text:
                provider = form.save()  # Saves the new object to the database
                return redirect('success_provider', provider_id=provider.id)  # Redirect to a success page

    else:
        form = ProviderForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_provider.html', {'form': form, 'err': err})
    else:
        return render(request, 'add_provider.html', {'form': form})


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_service(request):

    services = Service.objects.all()

    services_list = []
    for s in services:
        name_type = s.house.id, s.name, s.service_type
        services_list.append(name_type)
    print(services_list)
    text = None
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            name_n_type = int(form['house'].value()), form['name'].value(), form['service_type'].value()
            print(name_n_type)
            if name_n_type in services_list:
                text = f'Service name {form['name'].value().upper()} with type {form['service_type'].value().upper()} is already registered for this house'
            else:
                service = form.save()  # Saves the new object to the database
                return redirect('success_service', service_id=service.id)  # Redirect to a success page

    else:
        form = ServiceForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_service.html', {'form': form, 'err': err})
    else:
        return render(request, 'add_service.html', {'form': form})


def add_service_to_house(request, house_id):
    house = get_object_or_404(House, id=house_id)
    services = Service.objects.filter(house=house.id)
    services_list = []
    for s in services:
        name_type = s.house.id, s.name, s.service_type
        services_list.append(name_type)
    text = None
    if request.method == 'POST':
        form = ServiceForm2(request.POST)
        if form.is_valid():
            name_n_type = int(form['house'].value()), form['name'].value(), form['service_type'].value()
            # print(name_n_type)
            if name_n_type in services_list:
                text = f'Service name {form['name'].value().upper()} with type {form['service_type'].value().upper()} is already registered for this house'
            else:
                service = form.save(commit=False)
                service.house = house.address
                service.save()
                return redirect('success_service', house_id=house.id, service_id=service.id)  # Redirect to a success page
    else:
        form = ServiceForm2(initial={'house': house})
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_service.html', {'form': form, 'err': err, 'house': house})
    else:
        return render(request, 'add_service.html', {'form': form, 'house': house})


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_house(request):
    houses = House.objects.all()
    houses_list = []
    for house in houses:
        houses_list.append(house.address)
    text = None
    if request.method == 'POST':
        form = HouseForm(request.POST)
        if form.is_valid():
            if form['address'] in houses_list:
                text = 'House address already registered'
            else:
                house = form.save()  # Saves the new object to the database
                return redirect('success_house', house_id=house.id)  # Redirect to a success page
    else:
        form = HouseForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_house.html', {'form': form, 'err': err})
    else:
        return render(request, 'add_house.html', {'form': form})


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_consumer(request):
    consumers = Consumer.objects.all()
    consumers_contracts_list = []
    for consumer in consumers:
        consumers_contracts_list.append(consumer.contract_nr)
    text = None
    if request.method == 'POST':
        form = ConsumerForm(request.POST)
        if form.is_valid():
            if form['name'] in consumers_contracts_list:
                text = 'This consumer name is already registered'
            else:
                consumer = form.save()  # Saves the new object to the database
                return redirect('success_consumer', consumer_id=consumer.id)  # Redirect to a success page
    else:
        form = ConsumerForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_consumer.html', {'form': form, 'err': err})
    else:
        return render(request, 'add_consumer.html', {'form': form})


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_apartment(request, **kwargs):
    apartments = Apartment.objects.all()

    house_apartments_list = []
    for apartment in apartments:
        house_apartment = str(apartment.address.id), str(apartment.apartment_nr)
        house_apartments_list.append(house_apartment)
    text = None
    if request.method == 'POST':
        form = ApartmentForm(request.POST)
        if form.is_valid():
            house_apartment = form['address'].value(), form['apartment_nr'].value()
            if house_apartment in house_apartments_list:
                text = 'Apartment is already registered'
            else:
                apartment = form.save()  # Saves the new object to the database
                return redirect('success_apartment', apartment_id=apartment.id)  # Redirect to a success page
    else:
        form = ApartmentForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_apartment.html', {'form': form, 'err': err})
    else:
        return render(request, 'add_apartment.html', {'form': form})


# @cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_apartment_to_house(request, house_id):
    house = get_object_or_404(House, id=house_id)
    print(house)
    apartments = Apartment.objects.filter(address=house.id)
    print(apartments)

    house_apartments_list = []
    for apartment in apartments:
        house_apartment = str(house_id), str(apartment.apartment_nr)
        house_apartments_list.append(house_apartment)
    text = None
    if request.method == 'POST':
        form = ApartmentForm2(request.POST)
        if form.is_valid():
            house_apartment = str(house_id), form['apartment_nr'].value()
            if house_apartment in house_apartments_list:
                text = 'Apartment is already registered'
            else:
                apartment = form.save(commit=False)  # Saves the new object to the database
                apartment.address = house
                apartment.save()
                return redirect('success_apartment', house_id=house.id, apartment_id=apartment.id)  # Redirect to a success page
    else:
        form = ApartmentForm2(initial={'house': house})

    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_apartment.html', {'form': form, 'err': err, 'house': house})
    else:
        return render(request, 'add_apartment.html', {'form': form, 'house': house})



@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_meter(request):
    meters = Meter.objects.all()
    meters_list = []

    for meter in selection:
        manufacturer_and_number = meter.manufacturer, meter.series, meter.number
        meters_list.append(manufacturer_and_number)
    text = None
    if request.method == 'POST':
        form = MeterForm(request.POST)
        if form.is_valid():
            print(form['manufacturer'].value(), form['number'].value())
            if (form['manufacturer'].value(), form['series'].value(), form['number'].value()) in meters_list:
                text = 'Meter is already registered'
            else:
                meter = form.save()  # Saves the new object to the database
                return redirect('success_meter', meter_id=meter.id)  # Redirect to a success page
    else:
        form = MeterForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'bills/add_meter.html', {'form': form, 'err': err})
    else:
        return render(request, 'bills/add_meter.html', {'form': form})


def houses_apartments(request, house_id):
    house = get_object_or_404(House, id=house_id)
    house_apartments = Apartment.objects.filter(address=house).order_by('apartment_nr')
    return render(request, 'bills/apartments_by_house.html', {'house': house, 'house_apartments': house_apartments})


def houses_services(request, house_id):
    house = get_object_or_404(House, id=house_id)
    house_services = Service.objects.filter(house=house).order_by('name')
    return render(request, 'bills/services_by_house.html', {'house': house, 'house_services': house_services})


def add_meter_to_apartment(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    meters = Meter.objects.filter(apartment_number=apartment.id)
    house = get_object_or_404(House, id=apartment.address.id)

    apartment_meters_list = []
    for meter in meters:
        meter_info = (meter.manufacturer, meter.series, meter.number)
        apartment_meters_list.append(meter_info)
    
    text = None
    if request.method == 'POST':
        form = MeterForm2(request.POST)
        if form.is_valid():
            meter_info = (form['manufacturer'].value(), form['series'].value(), form['number'].value())
            if meter_info in apartment_meters_list:
                text = 'Meter is already registered'
            else:
                meter = form.save(commit=False)
                meter.apartment = apartment
                meter.save()
                return redirect('success_meter', apartment_id=apartment.id, meter_id=meter.id)
    else:
        form = MeterForm2(initial={'apartment_number': apartment, 'address': house})

    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'bills/add_meter.html', {'form': form, 'err': err, 'apartment': apartment, 'house': house})
    else:
        return render(request, 'bills/add_meter.html', {'form': form, 'apartment': apartment})


def meters_by_apartment(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    apartment_meters = Meter.objects.filter(apartment_number=apartment.id)
    
    context = {
        'apartment': apartment,
        'apartment_meters': apartment_meters,
    }
    return render(request, 'bills/meters_by_apartment.html', context)

