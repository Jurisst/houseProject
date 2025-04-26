from django.views.decorators.cache import cache_control
from django.views.generic import ListView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect,  get_object_or_404
from .forms import ProviderForm, ServiceForm, HouseForm, ConsumerForm, ApartmentForm, MeterForm, ApartmentForm2, \
    ServiceForm2, MeterForm2, IncomingBillForm, IncomingBillForm2, MeterReadingForm
from .models import Provider, Service, House, Consumer, Apartment, Meter, IncomingBill, MeterReading
from .forms import ProviderForm, ServiceForm, HouseForm, ConsumerForm, ApartmentForm, MeterForm, ApartmentForm2, \
    ServiceForm2, MeterForm2, IncomingBillForm, IncomingBillForm2, MeterReadingForm
from .models import Provider, Service, House, Consumer, Apartment, Meter, IncomingBill, MeterReading
from .help_functions import manage_db_table
from django.http import JsonResponse
from datetime import datetime
from .validations import invalid_meters_count, is_not_unique_incoming_bill
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Window, Sum
from django.db.models.functions import Lead, Lag
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
import calendar
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.lib.fonts import addMapping
import os
from django.conf import settings
from .calculations import (
    calculate_object_count_bills, 
    calculate_bills_for_person_count,
    calculate_volume_services,
    calculate_water_difference,
    calculate_area_services,
    check_apartment_water_meter_readings,
    SERVICE_TO_METER_TYPE
)


# Register DejaVu Sans font for Unicode support
FONT_PATH = os.path.join(settings.BASE_DIR, 'static', 'fonts')
pdfmetrics.registerFont(TTFont('DejaVuSans', os.path.join(FONT_PATH, 'DejaVuSans.TTF')))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', os.path.join(FONT_PATH, 'DejaVuSans-Bold.TTF')))

# Register font family
registerFontFamily('DejaVuSans',
    normal='DejaVuSans',
    bold='DejaVuSans-Bold'
)

# Add Unicode mapping for Latvian characters
addMapping('DejaVuSans', 0, 0, 'DejaVuSans')
addMapping('DejaVuSans', 0, 1, 'DejaVuSans-Bold')

# Define Unicode ranges for Latvian characters
LATVIAN_RANGES = [
    (0x0100, 0x0101),  # Ā, ā
    (0x010C, 0x010D),  # Č, č
    (0x0112, 0x0113),  # Ē, ē
    (0x0122, 0x0123),  # Ģ, ģ
    (0x012A, 0x012B),  # Ī, ī
    (0x0136, 0x0137),  # Ķ, ķ
    (0x013B, 0x013C),  # Ļ, ļ
    (0x0145, 0x0146),  # Ņ, ņ
    (0x014C, 0x014D),  # Ō, ō
    (0x0156, 0x0157),  # Ŗ, ŗ
    (0x0160, 0x0161),  # Š, š
    (0x016A, 0x016B),  # Ū, ū
    (0x017D, 0x017E),  # Ž, ž
]

# Add mapping for each Latvian character range
for start, end in LATVIAN_RANGES:
    for code in range(start, end + 1):
        addMapping('DejaVuSans', code, 0, 'DejaVuSans')
        addMapping('DejaVuSans', code, 1, 'DejaVuSans-Bold')

@login_required
def index(request, user_id=None):
    if user_id:
        user = get_object_or_404(User, id=user_id)
        return render(request, 'bills/index.html', {'user': user})
    else:
        return render(request, 'bills/index.html')

@login_required
def items(request):
    if request.user.is_superuser:
        return render(request, 'bills/items.html')
    else:
        return render(request, 'bills/index.html')

def success_add_provider(request, provider_id):
    provider = get_object_or_404(Provider, id=provider_id)

    return render(request, 'bills/sp_provider_add.html', {'provider': provider})


def success_add_service(request, house_id, service_id):
    service = get_object_or_404(Service, id=service_id)
    context = {'service': service}

    if house_id:
        house = get_object_or_404(House, id=house_id)
        context['house'] = house
    return render(request, 'bills/sp_service_add.html', context)
    

def success_add_house(request, house_id):
    house = get_object_or_404(House, id=house_id)
    return render(request, 'bills/sp_house_add.html', {'house': house})


def success_add_consumer(request, consumer_id):
    consumer = get_object_or_404(Consumer, id=consumer_id) 
    return render(request, 'bills/sp_consumer_add.html', {'consumer': consumer})


def success_add_apartment(request, house_id, apartment_id):
    house = get_object_or_404(House, id=house_id)
    apartment = get_object_or_404(Apartment, id=apartment_id)
    return render(request, 'bills/sp_apartment_add.html', {'house_id': house.id,  'apartment_id': apartment.id})


def success_add_meter(request, apartment_id, meter_id, house_id=None):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    meter = get_object_or_404(Meter, id=meter_id)
    if house_id:
        house = get_object_or_404(House, id=house_id)
    if apartment:
        return render(request, 'bills/sp_meter_add.html', {'apartment': apartment, 'meter': meter, 'house': house})
    else:
        return render(request, 'bills/sp_meter_add.html', {'meter': meter, 'house': house})


def success_add_incoming(request, house_id, incoming_bill_id):
    house = get_object_or_404(House, id=house_id)
    incoming_bill = get_object_or_404(IncomingBill, id=incoming_bill_id)
    return render(request, 'bills/sp_incoming_add.html', {'house': house.id, 'incoming_bill': incoming_bill.id})


class HouseListView(ListView):
    template_name = 'customers_list.html'
    model = House
    context_object_name = "houses"
    ordering = "address"

class HouseDetailView(DetailView):
    model = House
    template_name = 'bills/house_detail.html'
    context_object_name = 'house'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['edit_url'] = reverse_lazy('house_update', kwargs={'pk': self.object.pk})
        return context


class ProviderListView(ListView):
    model = Provider
    template_name = 'provider_list.html'
    context_object_name = "providers"


class ProviderDetailView(DetailView):
    model = Provider
    template_name = 'bills/provider_detail.html'
    context_object_name = 'provider'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['edit_url'] = reverse_lazy('provider_update', kwargs={'pk': self.object.pk})
        return context


class ServiceListView(ListView):
    model = Service
    template_name = 'service_list.html'
    context_object_name = "services"


class ServiceDetailView(DetailView):
    model = Service
    template_name = 'bills/service_detail.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house'] = self.object.house
        context['edit_url'] = reverse_lazy('service_update', kwargs={'pk': self.object.pk, 'house_id': self.object.house.id})
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the service and check if it belongs to the house
        service = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or service.house.id != int(house_id):
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class ApartmentListView(ListView):
    model = Apartment
    template_name = 'customers_list.html'
    context_object_name = "apartments"
    ordering = ['apartment_nr']


class ApartmentDetailView(DetailView):
    model = Apartment
    template_name = 'bills/apartment_detail.html'
    context_object_name = 'apartment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house'] = self.object.address
        context['edit_url'] = reverse_lazy('apartment_update', kwargs={
            'pk': self.object.pk,
            'house_id': self.object.address.id
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the apartment and check if it belongs to the house
        apartment = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or apartment.address.id != int(house_id):
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class ConsumerListView(ListView):
    model = Consumer
    template_name = 'customers_list.html'
    context_object_name = "consumers"


class ConsumerDetailView(DetailView):
    model = Consumer
    template_name = 'bills/consumer_detail.html'
    context_object_name = 'consumer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        house_id = self.kwargs.get('house_id')
        context['house_id'] = house_id
        context['edit_url'] = reverse_lazy('consumer_update', kwargs={
            'pk': self.object.pk,
            'house_id': house_id
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the consumer and check if they have apartments in the house
        consumer = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or not consumer.apartment_set.filter(address_id=house_id).exists():
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class MeterListView(ListView):
    model = Meter
    template_name = 'customers_list.html'
    context_object_name = "meters"


class MeterDetailView(DetailView):
    model = Meter
    template_name = 'bills/meter_detail.html'
    context_object_name = 'meter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house'] = self.object.apartment_number.address
        context['apartment'] = self.object.apartment_number
        context['edit_url'] = reverse_lazy('meter_update', kwargs={
            'pk': self.object.pk,
            'house_id': self.object.apartment_number.address.id
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the meter and check if it belongs to the house
        meter = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or meter.apartment_number.address.id != int(house_id):
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class IncomingBillListView(ListView):
    model = IncomingBill
    template_name = 'bills/incoming_bill_list.html'
    context_object_name = "incoming_bills"

    def get_queryset(self):
        # Get house_id from URL if it exists
        house_id = self.kwargs.get('house_id')
        if house_id:
            # Filter bills for specific house
            return IncomingBill.objects.filter(house_id=house_id)
        # Return all bills if no house_id (though this case should be rare/unused)
        return IncomingBill.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get house_id from URL if it exists
        house_id = self.kwargs.get('house_id')
        if house_id:
            context['house'] = House.objects.get(id=house_id)
        return context


class IncomingBillDetailView(DetailView):
    model = IncomingBill
    template_name = 'bills/incoming_bill_detail.html'
    context_object_name = 'bill'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house'] = self.object.house
        context['edit_url'] = reverse_lazy('incoming_bill_update', kwargs={
            'pk': self.object.pk,
            'house_id': self.object.house.id
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the bill and check if it belongs to the house
        bill = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or bill.house.id != int(house_id):
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class IncomingBillUpdateView(UpdateView):
    model = IncomingBill
    form_class = IncomingBillForm2
    template_name = 'bills/incoming_bill_update.html'
    context_object_name = 'bill'

    def get_success_url(self):
        return reverse_lazy('incoming_bill_detail', kwargs={
            'house_id': self.object.house.id,
            'pk': self.object.pk
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house'] = self.object.house
        return context


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
@login_required
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
@login_required
def add_service(request, text=None):

    services = Service.objects.all()

    services_list = []
    for s in services:
        name_type = s.house.id, s.name, s.service_type
        services_list.append(name_type)
    print(services_list)
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            name_n_type = int(form['house'].value()), form['name'].value(), form['service_type'].value()
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


@login_required
def add_service_to_house(request, house_id, text=None):
    house = get_object_or_404(House, id=house_id)
    services = Service.objects.filter(house=house.id)
    services_list = []
    for s in services:
        name_type = s.house.id, s.name, s.service_type
        services_list.append(name_type)
    if request.method == 'POST':
        form = ServiceForm2(request.POST)
        if form.is_valid():
            name_n_type = int(form['house'].value()), form['name'].value(), form['service_type'].value()
            # print(name_n_type)
            if name_n_type in services_list:
                text = f'Service name {form['name'].value().upper()} with type {form['service_type'].value().upper()} is already registered for this house'
            else:
                service = form.save(commit=False)
                service.house = house
                service.save()
                if service.get_name_display() == 'Cold water' or service.get_name_display() == 'Hot water':
                    return redirect('service_update', house_id=house.id, pk=service.id)  # Redirect to a success page
                else:
                    return redirect('success_service', house_id=house.id, service_id=service.id)  # Redirect to a success page
    else:
        form = ServiceForm2(initial={'house': house})
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_service.html', {'form': form, 'err': err, 'house': house})
    else:
        return render(request, 'add_service.html', {'form': form, 'house': house})


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
@login_required
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
@login_required
def add_consumer(request):
    consumers = Consumer.objects.all()
    consumers_list = []
    for consumer in consumers:
        name_mail = consumer.name, consumer.e_mail
        print(name_mail)
        consumers_list.append(name_mail)
    text = None
    if request.method == 'POST':
        form = ConsumerForm(request.POST)
        if form.is_valid():
            name_mail = form['name'].value(), form['e_mail'].value()
            print(name_mail)
            if name_mail in consumers_list:
                text = 'This consumer name is already registered'
            else:
                consumer = form.save()
                return redirect('success_consumer', consumer_id=consumer.id) 
    else:
        form = ConsumerForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_consumer.html', {'form': form, 'err': err})
    else:
        return render(request, 'add_consumer.html', {'form': form})


@cache_control(no_store=True, no_cache=True, must_revalidate=True)
@login_required
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
                apartment = form.save()
                return redirect('success_apartment', apartment_id=apartment.id) 
    else:
        form = ApartmentForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_apartment.html', {'form': form, 'err': err})
    else:
        return render(request, 'add_apartment.html', {'form': form})


@login_required
def add_apartment_to_house(request, house_id):
    house = get_object_or_404(House, id=house_id)
    apartments = Apartment.objects.filter(address=house)

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
                apartment = form.save(commit=False)
                apartment.address = house
                apartment.save()
                return redirect('success_apartment', house_id=house.id, apartment_id=apartment.id)
    else:
        form = ApartmentForm2(initial={'address': house})

    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'add_apartment.html', {'form': form, 'err': err, 'house': house})
    else:
        return render(request, 'add_apartment.html', {'form': form, 'house': house})


@login_required
@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def add_meter(request, house_id=None, apartment_id=None):
    if house_id:
        house = get_object_or_404(House, id=house_id)
    else:
        house = None
    if apartment_id:
        apartment = get_object_or_404(Apartment, id=apartment_id)
    else:
        apartment = None
    meters = Meter.objects.all()
    meters_list = []
    for meter in meters:
        manufacturer_and_number = meter.manufacturer, meter.series, meter.number
        meters_list.append(manufacturer_and_number)
    text = None
    if request.method == 'POST':
        form = MeterForm(request.POST)
        if form.is_valid():
            if (form['manufacturer'].value(), form['series'].value(), form['number'].value()) in meters_list:
                text = 'Meter is already registered'
            else:
                meter = form.save()  
                return redirect('success_meter', meter_id=meter.id, house_id=house_id, apartment_id=apartment_id) 
    else:
        form = MeterForm()
    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'bills/add_meter.html', {'form': form, 'err': err})
    else:
        return render(request, 'bills/add_meter.html', {'form': form})


@login_required
def houses_apartments(request, house_id):
    house = get_object_or_404(House, id=house_id)
    house_apartments = Apartment.objects.filter(address=house).order_by('apartment_nr')
    return render(request, 'bills/apartments_by_house.html', {'house': house, 'house_apartments': house_apartments})


@login_required
def houses_services(request, house_id):
    house = get_object_or_404(House, id=house_id)
    house_services = Service.objects.filter(house=house).order_by('name')
    return render(request, 'bills/services_by_house.html', {'house': house, 'house_services': house_services})


@login_required
def add_meter_to_apartment(request, house_id, apartment_id, text=None):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    meters = Meter.objects.filter(apartment_number=apartment.id)
    house = get_object_or_404(House, id=house_id)
    apartment_meters_list = []
    for meter in meters:
        meter_info = meter.manufacturer, meter.series, meter.number
        apartment_meters_list.append(meter_info)
    print(apartment_meters_list)
    if request.method == 'POST':
        form = MeterForm2(request.POST)
        if form.is_valid():
            meter_info = form['manufacturer'].value(), form['series'].value(), form['number'].value()
            print(meter_info)
            if meter_info in apartment_meters_list:
                text = 'Meter is already registered'
            elif not invalid_meters_count(form, meters, apartment):
                meter = form.save(commit=False)
                meter.apartment = apartment
                meter.save()
                return redirect('success_meter', apartment_id=apartment.id, meter_id=meter.id, house_id=house.id)
            else:
                text = invalid_meters_count(form, meters, apartment)
    else:
        form = MeterForm2(initial={'apartment_number': apartment, 'address': house})

    if text:
        err = f'<html><body><b> {text} </b></body>'
        return render(request, 'bills/add_meter.html', {'form': form, 'err': err, 'apartment': apartment, 'house': house})
    

@login_required
def meters_by_apartment(request, apartment_id, house_id):
    apartment = get_object_or_404(Apartment, id=apartment_id)
    house = get_object_or_404(House, id=house_id)
    
    # Verify apartment belongs to house
    if apartment.address.id != house.id:
        return redirect('index')
        
    apartment_meters = Meter.objects.filter(apartment_number=apartment.id)
    
    context = {
        'apartment': apartment,
        'apartment_meters': apartment_meters,
        'house': house
    }
    return render(request, 'bills/meters_by_apartment.html', context)


@login_required
def houses_meters(request, house_id):
    house = get_object_or_404(House, id=house_id)
    house_meters = Meter.objects.filter(apartment_number__address=house).order_by('verification_date')
    return render(request, 'bills/meters_by_house.html', {'house': house, 'house_meters': house_meters})


# @login_required
# def calculate_public_bills(request, house_id):
    house = get_object_or_404(House, id=house_id)
    apartments = Apartment.objects.filter(address=house)
    
    # Get the selected year and month from request parameters or use current date
    try:
        selected_month = int(request.GET.get('month', datetime.now().month))
        selected_year = int(request.GET.get('year', datetime.now().year))
    except (TypeError, ValueError):
        selected_month = datetime.now().month
        selected_year = datetime.now().year

    # Filter incoming bills by house, service type, and period
    incoming_bills = IncomingBill.objects.filter(
        house=house,
        service__service_type='object_count',
        year=selected_year,
        month=selected_month
    )
    
    # Create a dictionary to store bill details for each apartment
    apartment_bills = {}
    
    for apartment in apartments:
        bill_positions = []
        total_amount = 0
        
        for bill in incoming_bills:
            amount_to_pay = bill.amount / apartments.count()
            bill_positions.append({
                'service': bill.service.name,
                'amount': round(amount_to_pay, 2),
                'quantity': round(bill.quantity_received / apartments.count(), 3)
            })
            total_amount += amount_to_pay
            
        apartment_bills[apartment] = {
            'positions': bill_positions,
            'total': round(total_amount, 2)
        }

    # Get available years from incoming bills
    available_years = IncomingBill.objects.filter(
        house=house,
        service__service_type='object_count'
    ).values_list('year', flat=True).distinct().order_by('year')

    context = {
        'house': house,
        'apartment_bills': apartment_bills,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_years': available_years,
        'months': range(1, 13),
    }
    
    return render(request, 'bills/calculate_public_bills.html', context)

@login_required
def add_incoming_bill(request, house_id=None):
    if house_id:
        house = get_object_or_404(House, id=house_id)
    else:
        house = None
    existing_bills = IncomingBill.objects.filter(house=house)
    err = None
        
    if request.method == 'POST':
        form = IncomingBillForm2(request.POST, house=house)
        if form.is_valid():
            err = is_not_unique_incoming_bill(form, existing_bills)
            if not err:
                incoming_bill = form.save()  
                messages.success(request, 'Bill successfully created.', extra_tags='bill')
                return redirect('success_incoming', house.id, incoming_bill.id)
    else:
        form = IncomingBillForm2(house=house)
    
    return render(request, 'bills/incoming_bill_form.html', {'house': house, 'form': form, 'err': err})


@login_required
@require_http_methods(["GET", "POST"])
def add_meter_reading(request, meter_id, house_id=None, apartment_id=None):
    # Clear any existing success messages about bills
    storage = messages.get_messages(request)
    for message in storage:
        # Skip saving any messages about bills
        if 'bill' in str(message).lower():
            storage.used = True
            
    if house_id:
        house = get_object_or_404(House, id=house_id)
    else:
        house = None
    if apartment_id:
        apartment = get_object_or_404(Apartment, id=apartment_id)
    else:
        apartment = None
    meter = get_object_or_404(Meter, id=meter_id)
    
    if request.method == 'POST':
        form = MeterReadingForm(meter=meter, data=request.POST)
        if form.is_valid():
            reading_date = form.cleaned_data['reading_date']
            # Check if reading already exists for this month
            existing_reading = MeterReading.objects.filter(
                meter=meter,
                reading_date__year=reading_date.year,
                reading_date__month=reading_date.month
            ).exists()
            
            if existing_reading:
                form.add_error('reading_date', _('A reading for this month already exists.'))
            else:
                try:
                    reading = form.save()
                    messages.success(request, _('Reading added successfully.'), extra_tags='meter_reading')
                    if house and apartment:
                        return redirect('meters_by_apartment', apartment_id=apartment.id, house_id=house.id)
                    elif house and not apartment:
                        return redirect('meters_by_house', house_id=house.id)
                except ValidationError as e:
                    for field, error in e.message_dict.items():
                        form.add_error(field, error)
    else:
        form = MeterReadingForm(meter=meter)
    
    context = {
        'form': form,
        'meter': meter,
        'apartment': apartment,
        'apartment_id': meter.apartment_number.id,
        'house': house
    }
    return render(request, 'bills/meter_reading_form.html', context)

@login_required
def calculate_consumption(request, house_id):
    house = get_object_or_404(House, id=house_id)
    
    try:
        selected_month = int(request.GET.get('month', datetime.now().month))
        selected_year = int(request.GET.get('year', datetime.now().year))
    except (TypeError, ValueError):
        selected_month = datetime.now().month
        selected_year = datetime.now().year
    
    # Get all readings up to the end of the selected month
    end_date = datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
    
    # Calculate previous month
    if selected_month == 1:
        prev_month = 12
        prev_year = selected_year - 1
    else:
        prev_month = selected_month - 1
        prev_year = selected_year
    
    # Get current month readings
    current_readings = MeterReading.objects.filter(
        meter__apartment_number__address=house,
        reading_date__year=selected_year,
        reading_date__month=selected_month
    ).select_related('meter', 'meter__apartment_number')
    
    # Get previous month readings
    prev_readings = MeterReading.objects.filter(
        meter__apartment_number__address=house,
        reading_date__year=prev_year,
        reading_date__month=prev_month
    ).select_related('meter', 'meter__apartment_number')
    
    # Create a dictionary of previous readings for quick lookup
    prev_readings_dict = {
        reading.meter_id: reading.reading_value 
        for reading in prev_readings
    }
    
    # Calculate consumption for each reading
    readings_with_consumption = []
    monthly_consumption = 0
    for reading in current_readings:
        # Try to get previous month's reading, if not available use meter's default reading
        prev_reading = prev_readings_dict.get(reading.meter_id, reading.meter.reading_default)
        
        consumption = reading.reading_value - prev_reading
        monthly_consumption += consumption
        readings_with_consumption.append({
            'meter': reading.meter,
            'apartment': reading.meter.apartment_number,
            'previous_date': datetime(prev_year, prev_month, 1),
            'previous_value': prev_reading,
            'current_date': reading.reading_date,
            'current_value': reading.reading_value,
            'consumption': consumption,
        })
    
    # Get available years from meter readings
    current_year = datetime.now().year
    earliest_reading = MeterReading.objects.filter(
        meter__apartment_number__address=house
    ).order_by('reading_date').first()
    start_year = earliest_reading.reading_date.year if earliest_reading else current_year
    
    context = {
        'house': house,
        'consumption_data': readings_with_consumption,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_years': range(start_year, current_year + 1),
        'months': range(1, 13),
        'monthly_consumption': monthly_consumption
    }
    
    return render(request, 'bills/consumption_calculation.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'bills/login.html')

def logout_view(request):
    messages.get_messages(request).used = True  # Clear any existing messages
    logout(request)
    return redirect('login')


@login_required
def meter_readings(request, meter_id):
    meter = get_object_or_404(Meter, id=meter_id)
    readings = MeterReading.objects.filter(meter=meter).order_by('-reading_date')
    
    context = {
        'meter': meter,
        'readings': readings,
        'apartment': meter.apartment_number,
        'house': meter.apartment_number.address
    }
    return render(request, 'bills/meter_readings.html', context)


@login_required
def houses_consumers(request, house_id):
    house = get_object_or_404(House, id=house_id)
    # Get all apartments for this house with their consumers
    apartments = Apartment.objects.filter(
        address=house
    ).select_related('consumer').order_by('apartment_nr')
    
    # Create a dictionary of consumers and their apartments
    consumer_apartments = {}
    for apartment in apartments:
        if apartment.consumer:
            if apartment.consumer not in consumer_apartments:
                consumer_apartments[apartment.consumer] = []
            consumer_apartments[apartment.consumer].append(apartment)
    
    context = {
        'house': house,
        'consumer_apartments': consumer_apartments,
    }
    return render(request, 'bills/house_consumers.html', context)


def houses_providers(request, house_id):
    house = get_object_or_404(House, id=house_id)
    # Get providers through services
    providers = Provider.objects.filter(service__house=house).distinct()
    return render(request, 'bills/house_providers.html', {'house': house, 'providers': providers})

@login_required
def calculate_total_bills(request, house_id):
    house = get_object_or_404(House, id=house_id)
    apartments = Apartment.objects.filter(address=house)
    
    # Get the selected year and month from request parameters or use current date
    try:
        selected_month = int(request.GET.get('month', datetime.now().month))
        selected_year = int(request.GET.get('year', datetime.now().year))
    except (TypeError, ValueError):
        selected_month = datetime.now().month
        selected_year = datetime.now().year

    # Calculate previous month for consumption calculations
    if selected_month == 1:
        prev_month = 12
        prev_year = selected_year - 1
    else:
        prev_month = selected_month - 1
        prev_year = selected_year

    # Get all incoming bills for the selected period
    incoming_bills = IncomingBill.objects.filter(
        house=house,
        year=selected_year,
        month=selected_month
    )

    # Filter bills by service type
    living_person_bills = incoming_bills.filter(service__service_type='living_person_count')
    declared_person_bills = incoming_bills.filter(service__service_type='declared_person_count')
    object_count_bills = incoming_bills.filter(service__service_type='object_count')
    volume_bills = incoming_bills.filter(service__service_type='volume')
    area_bills = incoming_bills.filter(service__service_type='area')

    # Get current month readings for water meters
    current_readings = MeterReading.objects.filter(
        meter__apartment_number__address=house,
        meter__type__in=['cold', 'hot'],
        reading_date__year=selected_year,
        reading_date__month=selected_month
    ).select_related('meter', 'meter__apartment_number')
    
    # Get previous month readings for water meters
    prev_readings = MeterReading.objects.filter(
        meter__apartment_number__address=house,
        meter__type__in=['cold', 'hot'],
        reading_date__year=prev_year,
        reading_date__month=prev_month
    ).select_related('meter', 'meter__apartment_number')
    
    # Create a dictionary of previous readings for quick lookup
    prev_readings_dict = {
        reading.meter_id: reading.reading_value 
        for reading in prev_readings
    }

    # Calculate total house water consumption
    house_water_consumption = 0
    for reading in current_readings:
        prev_reading = prev_readings_dict.get(reading.meter_id, reading.meter.reading_default)
        consumption = reading.reading_value - prev_reading
        house_water_consumption += consumption

    apartments_with_meters = []
    for apartment in apartments:
        if apartment.cold_meters_count > 0 or apartment.hot_meters_count > 0:
            apartments_with_meters.append(apartment)
    print(f"Apartments with meters: {apartments_with_meters}")
    # Check for apartments with missing readings
    apartments_with_missing_readings = {}
    if house.water_calculation_type_1 == 'volume':
        for apartment in apartments:
            if apartment in apartments_with_meters:
                has_readings, missing_meters, last_reading_date, missing_readings_data = check_apartment_water_meter_readings(apartment, selected_year, selected_month)
                if not has_readings:
                    apartments_with_missing_readings[apartment] = {
                        'missing_meters': missing_meters,
                        'last_reading_date': last_reading_date,
                        'missing_readings_data': missing_readings_data
                    }
    print(f"Apartments with missing readings: {apartments_with_missing_readings}")  
    # Create a dictionary to store bill details for each apartment
    apartment_bills = {}

    for apartment in apartments:
        public_positions = []
        individual_positions = []
        monthly_consumption = 0        
        total_amount = 0

        # Calculate object count services (every apartment pays for the same amount)
        if object_count_bills:
            total_amount = calculate_object_count_bills(house, object_count_bills, public_positions, apartments, Service, total_amount)

        # Calculate living person count services  (for currently residing (living or declared) persons)
        if living_person_bills: 
            total_amount = calculate_bills_for_person_count(house, living_person_bills, public_positions, apartment, Service, total_amount)
        if declared_person_bills:
            total_amount = calculate_bills_for_person_count(house, declared_person_bills, public_positions, apartment, Service, total_amount)
        
        # Calculate area services (for total area or heated area of the apartment)
        if area_bills:
            total_amount = calculate_area_services(house, area_bills, apartment, public_positions, Service, total_amount)
        
        # Calculate volume (metered) services (for water, heat, etc.)
        if volume_bills:
            # Check if this apartment has meters
            if apartment in apartments_with_meters:

                # Check if this apartment has missing readings
                apartment_missing_readings = apartments_with_missing_readings.get(apartment)
                if apartment_missing_readings:
                    total_amount = calculate_water_difference(volume_bills, apartment, selected_year, selected_month, individual_positions, house_water_consumption, total_amount, Service, apartments_with_missing_readings)
                else:
                    # If all readings are present, calculate normally
                    total_amount, monthly_consumption, quantity_received = calculate_volume_services(
                        volume_bills,
                        apartment,
                        selected_year,
                        selected_month,
                        individual_positions,
                        Service,
                        total_amount,
                        monthly_consumption,
                    )
            else:
                if house.water_calculation_type_2 == 'living_person_count' or house.water_calculation_type_2 == 'declared_person_count':
                    total_amount = calculate_bills_for_person_count(house, volume_bills, public_positions, apartment, Service, total_amount)
                elif house.water_calculation_type_2 == 'object_count':
                    total_amount = calculate_object_count_bills(house, volume_bills, public_positions, apartment, Service, total_amount)

        apartment_bills[apartment] = {
            'public_positions': public_positions,
            'individual_positions': individual_positions,
            'total': round(total_amount, 2)
        }
        
    # Get available years from incoming bills
    available_years = list(IncomingBill.objects.filter(
        house=house
    ).values_list('year', flat=True).distinct().order_by('year'))
    
    # Add current year if not in the list
    current_year = datetime.now().year
    if current_year not in available_years:
        available_years.append(current_year)
        available_years.sort()

    context = {
        'house': house,
        'apartment_bills': apartment_bills,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_years': available_years,
        'months': range(1, 13),
        'house_water_consumption': house_water_consumption,
        'quantity_received': quantity_received,
        'difference': quantity_received - house_water_consumption,
        'norm_for_person': house.norm_for_person,
        'apartments_with_missing_readings': apartments_with_missing_readings
    }
    
    return render(request, 'bills/total_bills.html', context)


@login_required
def generate_apartment_bill_pdf(request, house_id, apartment_id, year, month):
    house = get_object_or_404(House, id=house_id)
    apartment = get_object_or_404(Apartment, id=apartment_id)
    
    # Get all incoming bills for the selected period
    incoming_bills = IncomingBill.objects.filter(
        house=house,
        year=year,
        month=month
    )
            
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='DejaVuSans',
        fontName='DejaVuSans',
        fontSize=12
    ))
    styles.add(ParagraphStyle(
        name='DejaVuSans-Bold',
        fontName='DejaVuSans-Bold',
        fontSize=12
    ))
    
    # Add title
    elements.append(Paragraph(f"Bill for Apartment {apartment.apartment_nr}", styles['DejaVuSans-Bold']))
    elements.append(Paragraph(f"Address: {house.address}", styles['DejaVuSans']))
    elements.append(Paragraph(f"Period: {year}-{month}", styles['DejaVuSans']))
    elements.append(Spacer(1, 20))
    
    # Prepare data for tables
    public_data = ['Service', 'Quantity', 'Units', 'Price/Unit', 'Amount']
    individual_data = ['Service', 'Meter', 'Consumption', 'Units', 'Price/Unit', 'Amount']
    monthly_consumption = 0    
    total_amount = 0
    
    # Object count services
    public_bills = incoming_bills.filter(service__service_type='object_count')
    apartments_count = Apartment.objects.filter(address=house).count()
    
    for bill in public_bills:
        amount = bill.amount / apartments_count
        public_data.append([
            dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
            f"{bill.quantity_received / apartments_count:.3f}",
            bill.service.measuring_units,
            f"{bill.service.price_per_unit:.2f}",
            f"{amount:.2f}"
        ])
        total_amount += amount

    # Add living person count services
    living_person_bills = incoming_bills.filter(service__service_type='living_person_count')
    total_living_persons = Apartment.objects.filter(address=house).aggregate(Sum('living_person_count'))['living_person_count__sum'] or 0
    
    if total_living_persons > 0:  # Only process if there are living persons
        for bill in living_person_bills:
            apartment_persons = apartment.living_person_count
            if apartment_persons > 0:  # Only calculate for apartments with living persons
                amount = (bill.amount / total_living_persons) * apartment_persons
                public_data.append([
                    dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                    f"{apartment_persons}",
                    "persons",
                    f"{bill.amount / total_living_persons:.2f}",
                    f"{amount:.2f}"
                ])
                total_amount += amount

    # Volume services
    volume_bills = incoming_bills.filter(service__service_type='volume')
    for bill in volume_bills:
        # Use the mapping to get the correct meter type
        meter_type = SERVICE_TO_METER_TYPE.get(bill.service.name)
        if meter_type:
            meters = Meter.objects.filter(
                apartment_number=apartment,
                type=meter_type
            )
            
            for meter in meters:
                # Get current month reading
                current_reading = MeterReading.objects.filter(
                    meter=meter,
                    reading_date__year=year,
                    reading_date__month=month
                ).first()
                
                # Get previous month reading
                if month == 1:
                    prev_month = 12
                    prev_year = year - 1
                else:
                    prev_month = month - 1
                    prev_year = year
                    
                prev_reading = MeterReading.objects.filter(
                    meter=meter,
                    reading_date__year=prev_year,
                    reading_date__month=prev_month
                ).first()
                
                if current_reading and prev_reading:
                    consumption = current_reading.reading_value - prev_reading.reading_value
                else:
                    consumption = 0
                    print(f"Missing readings for meter {meter.id}: Current: {bool(current_reading)}, Previous: {bool(prev_reading)}")
                
                amount = consumption * bill.service.price_per_unit
                individual_data.append([
                    dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                    f"{meter.manufacturer} {meter.number}",
                    f"{consumption:.3f}",
                    bill.service.measuring_units,
                    f"{bill.service.price_per_unit:.2f}",
                    f"{amount:.2f}"
                ])
                total_amount += amount
            
    
    # Create tables
    if len(public_data) > 1:
        elements.append(Paragraph("Object Count Services", styles['Heading2']))
        public_table = Table(public_data)
        public_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(public_table)
    print(len(public_data))
    print(len(individual_data))
    if len(individual_data) > 1:
        elements.append(Paragraph("Volume Services", styles['Heading2']))
        individual_table = Table(individual_data)
        individual_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(individual_table)
    
    # Add total amount
    elements.append(Paragraph(f"Total Amount: {total_amount:.2f}", styles['Heading2']))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bill_{apartment.apartment_nr}_{year}_{month}.pdf"'
    response.write(pdf)
    return response

class HouseUpdateView(UpdateView):
    model = House
    form_class = HouseForm
    template_name_suffix = "_update_form"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Calculate the number of apartments
        apartment_count = Apartment.objects.filter(address=self.object).count()
        # Set the initial value for the apartment_count field
        form.fields['apartment_count'].initial = apartment_count
        # Calculate total area from apartments
        total_area = Apartment.objects.filter(address=self.object).aggregate(Sum('area'))['area__sum'] or 0
        form.fields['area_of_apartments_total'].initial = total_area
        form.fields['area_of_apartments_total'].widget.attrs['readonly'] = True
        # Calculate total heated area from apartments
        total_heated_area = Apartment.objects.filter(address=self.object).aggregate(Sum('heated_area'))['heated_area__sum'] or 0
        form.fields['area_of_apartments_heated_total'].initial = total_heated_area
        form.fields['area_of_apartments_heated_total'].widget.attrs['readonly'] = True
        return form

    def get_success_url(self):
        return reverse_lazy('house_detail', kwargs={'pk': self.object.pk})

class ProviderUpdateView(UpdateView):
    model = Provider
    fields = '__all__'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('provider_detail', kwargs={'pk': self.object.pk})

class ServiceUpdateView(UpdateView):
    model = Service
    form_class = ServiceForm2
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('service_detail', kwargs={
            'pk': self.object.pk,
            'house_id': self.object.house.id
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house'] = self.object.house
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the service and check if it belongs to the house
        service = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or service.house.id != int(house_id):
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

class ApartmentUpdateView(UpdateView):
    model = Apartment
    form_class = ApartmentForm2
    template_name_suffix = "_update_form"
    context_object_name = 'apartment'

    def get_success_url(self):
        return reverse_lazy('apartment_detail', kwargs={
            'pk': self.object.pk,
            'house_id': self.object.address.id
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house'] = self.object.address
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the apartment and check if it belongs to the house
        apartment = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or apartment.address.id != int(house_id):
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

class ConsumerUpdateView(UpdateView):
    model = Consumer
    fields = '__all__'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('consumer_detail', kwargs={
            'pk': self.object.pk,
            'house_id': self.kwargs.get('house_id')
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house_id'] = self.kwargs.get('house_id')
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the consumer and check if they have apartments in the house
        consumer = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or not consumer.apartment_set.filter(address_id=house_id).exists():
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)

class MeterUpdateView(UpdateView):
    model = Meter
    fields = '__all__'
    template_name_suffix = "_update_form"

    def get_success_url(self):
        return reverse_lazy('meter_detail', kwargs={
            'pk': self.object.pk,
            'house_id': self.object.apartment_number.address.id,
            'apartment_id': self.object.apartment_number.id
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['house'] = self.object.apartment_number.address
        context['apartment'] = self.object.apartment_number
        return context

    def dispatch(self, request, *args, **kwargs):
        # Get the meter and check if it belongs to the house
        meter = self.get_object()
        house_id = self.kwargs.get('house_id')
        if not house_id or meter.apartment_number.address.id != int(house_id):
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)
