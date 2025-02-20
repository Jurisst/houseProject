from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator
from datetime import date
from django.urls import reverse
from .validations import valid_provider_name, valid_reg_number, valid_bank_account, valid_meter_nr


# needs validations for fields
class Provider(models.Model):
    # name of provider of the service
    name = models.CharField(max_length=50, validators=[
        MinLengthValidator(2, 'Must be at least 2 characters'),
        MaxLengthValidator(50, 'Max length is 50 characters'),
        valid_provider_name
    ])
    # enterprise format (SIA, AS, IU etc)
    CHOICES = [('SIA', 'SIA'), ('SIA', 'AS'), ('IU', 'IU'), ('SDV', 'SDV')]
    business_form = models.CharField(max_length=15, choices=CHOICES)
    # registration number of provider (e.g. LV4000045678))
    reg_number = models.CharField(max_length=25, validators=[
        MinLengthValidator(11, 'Must be at least 11 characters'),
        MaxLengthValidator(25, 'Max length is 25 characters'),
        valid_reg_number
    ])
    #  current bank account of provider (e.g. LV27HABA1222200045678)
    account = models.CharField(max_length=25, validators=[
        MinLengthValidator(10, 'Must be at least 10 characters'),
        MaxLengthValidator(25, 'Max length is 25 characters'),
        valid_bank_account
    ])

    def __str__(self):
        return self.name + ' ' + self.business_form

class House(models.Model):
    address = models.CharField(max_length=50, validators=[
        MinLengthValidator(6, 'Must be at least 6 characters'),
        MaxLengthValidator(50, 'Max length is 50 characters')
    ])
    apartment_count = models.IntegerField(validators=[MinValueValidator(1, 'Must be at least 1')])
    area_of_apartments_total = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    area_total = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])

    def get_absolute_url(self):
        return reverse("house_update", kwargs={"pk": self.pk})

    def __str__(self):
        return str(self.address)


class Service(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, default=None)
    # name of the service
    name = models.CharField(max_length=30, validators=[MinLengthValidator(3, 'Must be at least 3 characters')])
    # type of the service (public/private)
    CHOICES = [('public', 'Public'), ('individual', 'Individual')]
    service_type = models.CharField(max_length=10, choices=CHOICES)
    # measuring units
    measuring_units = models.CharField(max_length=4, validators=[
        MinLengthValidator(1, 'Must be at least 1 character')
    ])
    # presence of meters of the service (boolean, True/False)
    CHOICES_BOOL = [(True, 'With Meters'), (False, 'No Meters')]
    meters_of_volume = models.BooleanField(choices=CHOICES_BOOL, default=True)

    def __str__(self):
        return self.name + '  ' + self.service_type


class Consumer(models.Model):
    name = models.CharField(max_length=50, validators=[MinLengthValidator(5, 'Must be at least 5 characters')])
    # address = models.ForeignKey(House, on_delete=models.CASCADE) # Is it necessary?
    e_mail = models.EmailField()
    billing_address = models.CharField(max_length=50, validators=[MinLengthValidator(5, 'Must be at least 5 characters')])

    def __str__(self):
        return self.name + '  ' + self.e_mail



class Apartment(models.Model):
    address = models.ForeignKey(House, on_delete=models.CASCADE)
    apartment_nr = models.IntegerField(validators=[MinValueValidator(1, 'Must be at least 1')])
    area = models.IntegerField(validators=[MinValueValidator(1, 'Must be at least 1')])
    wm_count = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    hm_count = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    person_count = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    consumer = models.ForeignKey(Consumer, on_delete=models.PROTECT, default='')
    contract_nr = models.CharField(null=True, max_length=50, validators=[MinLengthValidator(2, 'Must be at least 2 characters')])

    def __str__(self):
        return 'Nr. ' + str(self.apartment_nr) + '  ' + str(self.address)



class Meter(models.Model):
    CHOICES = [('Cold water', 'cold'), ('Hot water', 'hot'), ('Heat', 'heat'), ('Other', 'other')]
    type = models.CharField(max_length=10, choices=CHOICES)
    manufacturer = models.CharField(default=" ", max_length=30, validators=[MinLengthValidator(2, 'Must be at least 2 characters')])
    series = models.CharField(default=" ", max_length=5)
    number = models.CharField(max_length=10, validators=[
        MinLengthValidator(2, 'Must be at least 2 digits'),
        valid_meter_nr
    ])
    # number = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    reading_default = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    verification_date = models.DateField("Verification date", default=date.today)
    address = models.ForeignKey(House, on_delete=models.PROTECT, default='')
    apartment_number = models.ForeignKey(Apartment, on_delete=models.PROTECT)

    def __str__(self):
        return str(self.manufacturer) + '  ' + self.series + ' ' + self.number


