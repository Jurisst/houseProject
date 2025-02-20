from django import forms
from .models import Provider, Service, House, Consumer, Apartment, Meter


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
        if 'address' in self.fields:
            # self.fields['address'].widget = forms.HiddenInput()  # Hide the field
            self.fields['address'].widget = forms.HiddenInput()
        else:
            self.fields['address'].label_from_instance = lambda obj: obj.address
        self.fields['consumer'].label_from_instance = lambda obj: obj.name


class MeterForm(forms.ModelForm):
    class Meta:
        model = Meter
        fields = '__all__'
    series = forms.CharField(required=False)

