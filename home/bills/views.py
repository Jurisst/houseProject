from django.views.decorators.cache import cache_control
from django.shortcuts import render, redirect,  get_object_or_404
from .forms import ProviderForm, ServiceForm, HouseForm, ConsumerForm, ApartmentForm, MeterForm
from .models import Provider, Service, House, Consumer, Apartment, Meter
from .help_functions import manage_db_table


def index(request):
    return render(request, 'base_t.html')


def success_add_provider(request, provider_id):
    provider = get_object_or_404(Provider, id=provider_id)  # Get the product instance
    return render(request, 'sp_provider_add.html', {'provider': provider})


def success_add_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)  # Get the product instance
    return render(request, 'sp_service_add.html', {'service': service})


def success_add_house(request, house_id):
    house = get_object_or_404(House, id=house_id)  # Get the product instance
    return render(request, 'sp_house_add.html', {'house': house})


def success_add_consumer(request, consumer_id):
    consumer = get_object_or_404(Consumer, id=consumer_id)  # Get the product instance
    return render(request, 'sp_consumer_add.html', {'consumer': consumer})


def success_add_apartment(request, apartment_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)  # Get the product instance
    return render(request, 'sp_apartment_add.html', {'apartment': apartment})


def success_add_meter(request, meter_id):
    meter = get_object_or_404(Meter, id=meter_id)  # Get the product instance
    return render(request, 'sp_meter_add.html', {'meter': meter})


providers = Provider.objects.all()
services = Service.objects.all()
houses = House.objects.all()
consumers = Consumer.objects.all()
apartments = Apartment.objects.all()
meters = Meter.objects.all()


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_provider(request):
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
    services_list = []
    for s in services:
        name_type = s.name, s.service_type
        services_list.append(name_type)
    text = None
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            name_n_type = form['name'].value(), form['service_type'].value()
            if name_n_type in services_list:
                text = f'Service name {form['name'].value().upper()} with type {form['service_type'].value().upper()} is already registered'
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


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_house(request):
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
    consumers_contracts_list = []
    for consumer in consumers:
        consumers_contracts_list.append(consumer.contract_nr)
    text = None
    if request.method == 'POST':
        form = ConsumerForm(request.POST)
        if form.is_valid():
            if form['contract_nr'] in consumers_contracts_list:
                text = 'This contract number is already registered'
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
def add_apartment(request):
    house_apartments_list = []
    for apartment in apartments:
        house_apartment = str(apartment.houseLocation.id), str(apartment.apartment_nr)
        house_apartments_list.append(house_apartment)
    text = None
    if request.method == 'POST':
        form = ApartmentForm(request.POST)
        if form.is_valid():
            house_apartment = form['houseLocation'].value(), form['apartment_nr'].value()
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


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_meter(request):
    text = None
    if request.method == 'POST':
        form = MeterForm(request.POST)
        if form.is_valid():
            meter = form.save()  # Saves the new object to the database
            return redirect('success_meter', meter_id=meter.id)  # Redirect to a success page
        else:
            text = 'ERROR IN FORM'
    else:
        form = MeterForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_meter.html', {'form': form, 'err': err})
    else:
        return render(request, 'add_meter.html', {'form': form})


