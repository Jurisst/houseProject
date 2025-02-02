from django import forms
from .models import Provider, Service, House, Consumer, Apartment, Meter


class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        fields = ['name', 'business_form', 'reg_number', 'account']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'service_type', 'measuring_units', 'meters_of_volume']


class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        fields = '__all__'
    area_total = forms.IntegerField(required=False)


class ConsumerForm(forms.ModelForm):
    class Meta:
        model = Consumer
        fields = '__all__'


class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = '__all__'


class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['apartment_number'].label_from_instance = lambda obj: obj.apartment_nr