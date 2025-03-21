from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator, MinValueValidator, RegexValidator
from datetime import date
from django.urls import reverse
from decimal import Decimal, ROUND_HALF_UP
from .validations import valid_provider_name, valid_reg_number, valid_bank_account, valid_meter_nr
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError
from django.db.models import Sum


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
    apartment_count = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    area_of_apartments_total = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    area_of_apartments_heated_total = models.IntegerField("Total heated area of apartments", validators=[MinValueValidator(0, 'Can not be negative number')])
    area_total = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])

    def update_apartment_count(self):
        self.apartment_count = Apartment.objects.filter(address=self).count()
        self.save(update_fields=['apartment_count'])

    def get_absolute_url(self):
        return reverse("house_update", kwargs={"pk": self.pk})

    def __str__(self):
        return str(self.address)


class Service(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, default=None)
    NAME_CHOICES = [('cold_water', 'Cold water'), ('electricity', 'Electricity'), ('hot_water', 'Hot water'), ('heat', 'Heat'), ('other', 'Other')]
    # name of the service
    name = models.CharField(max_length=30, choices=NAME_CHOICES, validators=[MinLengthValidator(3, 'Must be at least 3 characters')])
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, default=None)
    # type of the service (public/private)
    CHOICES = [('public', 'Public'), ('individual', 'Individual')]
    service_type = models.CharField(max_length=10, choices=CHOICES)
    # measuring units
    measuring_units = models.CharField(max_length=4, validators=[
        MinLengthValidator(1, 'Must be at least 1 character')
    ])
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
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
    area = models.IntegerField("Area of apartment", validators=[MinValueValidator(1, 'Must be at least 1')])
    heated_area = models.IntegerField("Heated area of apartment", validators=[MinValueValidator(1, 'Must be at least 1')])
    cold_meters_count = models.IntegerField("Count of cold water meters", validators=[MinValueValidator(0, 'Can not be negative number')])
    hot_meters_count = models.IntegerField("Count of hot water meters", validators=[MinValueValidator(0, 'Can not be negative number')])
    heat_meters_count = models.IntegerField("Count of heat meters", validators=[MinValueValidator(0, 'Can not be negative number')])
    person_count = models.IntegerField("Count of persons", validators=[MinValueValidator(0, 'Can not be negative number')])
    consumer = models.ForeignKey(Consumer, on_delete=models.PROTECT, default='')
    contract_nr = models.CharField(null=True, max_length=50, validators=[MinLengthValidator(2, 'Must be at least 2 characters')])

    def __str__(self):
        return 'Nr. ' + str(self.apartment_nr) + '  ' + str(self.address)

    def save(self, *args, **kwargs):
        if self.heated_area is None or self.heated_area == 0:
            self.heated_area = self.area
        super().save(*args, **kwargs)
        # Update the house's total apartment area
        total_area = Apartment.objects.filter(address=self.address).aggregate(Sum('area'))['area__sum'] or 0
        total_heated_area = Apartment.objects.filter(address=self.address).aggregate(Sum('heated_area'))['heated_area__sum'] or 0
        self.address.area_of_apartments_total = total_area
        self.address.area_of_apartments_heated_total = total_heated_area
        self.address.update_apartment_count()
        self.address.save(update_fields=['area_of_apartments_total', 'area_of_apartments_heated_total'])

    def delete(self, *args, **kwargs):
        house = self.address
        super().delete(*args, **kwargs)
        # Update the house's total apartment area after deletion
        total_area = Apartment.objects.filter(address=house).aggregate(Sum('area'))['area__sum'] or 0
        total_heated_area = Apartment.objects.filter(address=house).aggregate(Sum('heated_area'))['heated_area__sum'] or 0
        house.area_of_apartments_total = total_area
        house.area_of_apartments_heated_total = total_heated_area
        house.update_apartment_count()
        house.save(update_fields=['area_of_apartments_total', 'area_of_apartments_heated_total'])



class Meter(models.Model):
    CHOICES = [('cold', 'Cold water'), ('electricity', 'Electricity'), ('hot', 'Hot water'), ('heat', 'Heat'), ('other', 'Other')]
    type = models.CharField('Type of meter', max_length=15, choices=CHOICES)
    manufacturer = models.CharField('Manufacturer', default=" ", max_length=30, validators=[MinLengthValidator(2, 'Must be at least 2 characters')])
    series = models.CharField('Series (if applicable)', default=" ", max_length=5)
    number = models.CharField('Meter number', max_length=10, validators=[
        MinLengthValidator(2, 'Must be at least 2 digits'),
        valid_meter_nr
    ])
    # number = models.IntegerField(validators=[MinValueValidator(0, 'Can not be negative number')])
    reading_default = models.IntegerField('Default reading (on installation)', validators=[MinValueValidator(0, 'Can not be negative number')])
    verification_date = models.DateField("Verification date", default=date.today)
    address = models.ForeignKey(House, on_delete=models.PROTECT, verbose_name='House address')
    apartment_number = models.ForeignKey(Apartment, on_delete=models.PROTECT, default='', verbose_name='Apartment number')

    def __str__(self):
        return str(self.manufacturer) + '  ' + self.series + ' ' + self.number


class IncomingBill(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    house = models.ForeignKey(House, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(help_text="Format: YYYY",
                                       validators=[RegexValidator(r'^(202[1-9]|20[3-9])$')])
    month = models.PositiveSmallIntegerField(help_text="Format: MM",
                                             validators=[RegexValidator(r'^(0?[1-9]|1[0-2])$')])
    quantity_received = models.DecimalField(max_digits=10, decimal_places=3)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Apply mathematical rounding (ROUND_HALF_UP)
        if self.amount is not None:
            self.amount = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)

    @property
    def period(self):
        return f"{self.year}-{str(self.month).zfill(2)}"

    def __str__(self):
        return str(self.house) + '  ' + str(self.service) + ' ' + str(self.year) + ' ' + str(self.month)

    

class HouseManagement(models.Model):
    name = models.CharField(max_length=50, validators=[MinLengthValidator(5, 'Must be at least 5 characters')])
    reg_number = models.CharField(max_length=25, validators=[MinLengthValidator(11, 'Must be at least 11 characters')])
    address = models.CharField(max_length=50, validators=[MinLengthValidator(5, 'Must be at least 5 characters')])
    phone_number = models.CharField(max_length=15, validators=[MinLengthValidator(11, 'Must be at least 11 characters')])
    e_mail = models.EmailField()
    account = models.CharField(max_length=25, validators=[MinLengthValidator(10, 'Must be at least 10 characters')])


class OutgoingBill(models.Model):
    house_management = models.ForeignKey(HouseManagement, on_delete=models.CASCADE)
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    contract_nr = models.CharField(null=True, max_length=50, validators=[MinLengthValidator(2, 'Must be at least 2 characters')])
    year = models.PositiveIntegerField(help_text="Format: YYYY",
                                       validators=[RegexValidator(r'^(202[1-9]|20[3-9])$')])
    month = models.PositiveSmallIntegerField(help_text="Format: MM",
                                             validators=[RegexValidator(r'^(0?[1-9]|1[0-2])$')])
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
        

class MeterReading(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    reading_date = models.DateField()
    reading_value = models.DecimalField(max_digits=10, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Add this to enforce uniqueness
        unique_together = ['meter', 'reading_date']
        ordering = ['-reading_date']

    def __str__(self):
        return f"{self.meter} - {self.reading_date}: {self.reading_value}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Check if reading is greater than previous reading
        previous_readings = MeterReading.objects.all()
        print(previous_readings)
        if previous_readings:
            previous_reading = MeterReading.objects.filter(
                meter=self.meter,
                reading_date__lt=self.reading_date
            ).order_by('-reading_date').first()
            if previous_reading:
                if self.reading_value < previous_reading.reading_value:
                    raise ValidationError({
                        'reading_value': _("New reading cannot be less than previous reading")
                    })
        else:
            pass




        

