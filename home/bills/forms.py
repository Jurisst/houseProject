from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Provider, Service, House, Consumer, Apartment, Meter, IncomingBill, MeterReading
from datetime import datetime


class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        fields = ['name', 'business_form', 'reg_number', 'account']


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = '__all__'


class ServiceForm2(forms.ModelForm):
    class Meta:
        model = Service
        # exclude = ('house',)
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'house' in self.fields:
            # self.fields['address'].widget = forms.HiddenInput()  # Hide the field
            self.fields['house'].widget = forms.HiddenInput()
        else:
            self.fields['house'].label_from_instance = lambda obj: obj.address


class HouseForm(forms.ModelForm):
    # apartment_count = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'readonly': 'readonly'}))

    class Meta:
        model = House
        fields = '__all__'
        widgets = {
            'area_of_apartments_total': forms.NumberInput(attrs={'readonly': 'readonly'})
        }
        help_texts = {
            'apartment_count': _('Automatically calculated'),
            'area_of_apartments_total': _('Automatically calculated from apartment areas'),
            'area_of_apartments_heated_total': _('Automatically calculated from apartment heated areas'),
            'living_person_count': _('Automatically calculated'),
            'declared_person_count': _('Automatically calculated')            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields read-only
        self.fields['area_of_apartments_total'].widget.attrs['readonly'] = True
        self.fields['area_of_apartments_heated_total'].widget.attrs['readonly'] = True
        self.fields['apartment_count'].widget.attrs['readonly'] = True
        self.fields['living_person_count'].widget.attrs['readonly'] = True
        self.fields['declared_person_count'].widget.attrs['readonly'] = True

        # Set initial values if it's a new instance
        if not self.instance.pk:
            self.fields['area_of_apartments_total'].initial = 0
            self.fields['area_of_apartments_heated_total'].initial = 0
            self.fields['apartment_count'].initial = 0
            self.fields['living_person_count'].initial = 0
            self.fields['declared_person_count'].initial = 0
    

    def clean(self):
        cleaned_data = super().clean()
        if 'area_of_apartments_total' not in cleaned_data or cleaned_data['area_of_apartments_total'] is None:
            cleaned_data['area_of_apartments_total'] = 0
        return cleaned_data


class ConsumerForm(forms.ModelForm):
    class Meta:
        model = Consumer
        fields = '__all__'


class ApartmentForm(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['address'].label_from_instance = lambda obj: obj.address
        self.fields['consumer'].label_from_instance = lambda obj: obj.name


class ApartmentForm2(forms.ModelForm):
    class Meta:
        model = Apartment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['consumer'].label_from_instance = lambda obj: obj.name
        
        # Always hide the address field and keep its value
        self.fields['address'].widget = forms.HiddenInput()
        
        # If we have an instance (editing existing apartment)
        if self.instance and self.instance.pk:
            # Lock the address field to the current value
            self.fields['address'].initial = self.instance.address
            self.fields['address'].disabled = True


class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = '__all__'
    series = forms.CharField(required=False)


class MeterForm2(forms.ModelForm):
    class Meta:
        model = Meter
        fields = '__all__'
    
    series = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'address' in self.fields:
            self.fields['address'].widget = forms.HiddenInput()
        if 'apartment_number' in self.fields:
            self.fields['apartment_number'].widget = forms.HiddenInput()


class IncomingBillForm(forms.ModelForm):
    class Meta:
        model = IncomingBill
        fields = ['provider', 'house', 'service', 'year', 'month', 'quantity_received', 'amount']
        widgets = {
            'year': forms.NumberInput(attrs={'placeholder': 'e.g. 2025'}),
            'month': forms.NumberInput(attrs={'placeholder': '01-12'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'})
        }


class IncomingBillForm2(forms.ModelForm):
    class Meta:
        model = IncomingBill
        fields = ['provider', 'service', 'year', 'month', 'amount', 'quantity_received', 'house']
        widgets = {
            'year': forms.NumberInput(attrs={'placeholder': 'e.g. 2025'}),
            'month': forms.NumberInput(attrs={'placeholder': '01-12'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'house': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        house = kwargs.pop('house', None)
        super().__init__(*args, **kwargs)
        
        if house:
            self.fields['house'].initial = house
            self.fields['service'].queryset = Service.objects.filter(house=house)
        elif self.instance and self.instance.house:
            self.fields['service'].queryset = Service.objects.filter(house=self.instance.house)
        
        # Add this to show verbose name in dropdown
        self.fields['service'].label_from_instance = lambda obj: f"{obj.name} ({obj.get_service_type_display()})"


class MeterReadingForm(forms.ModelForm):
    class Meta:
        model = MeterReading
        fields = ['reading_date', 'reading_value']
        widgets = {
            'reading_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reading_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'})
        }

    def __init__(self, meter=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if meter:
            self.instance.meter = meter
        self.fields['reading_date'].widget.attrs.update({
            'max': datetime.now().strftime('%Y-%m-%d')
        })

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('reading_date'):
            return cleaned_data
        return cleaned_data

