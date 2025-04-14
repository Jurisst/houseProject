import re
from django.core.exceptions import ValidationError

def valid_provider_name(form_input):
    form_input = form_input.strip()
    allowed_symbols = r"""'.', ',', ';', ':', '...', '!', '?', '-', '(', ')', '"', ''', '..', '&', '@', '%', '+', '='"""
    pattern = rf"^[a-zA-Z0-9{re.escape('āčēģīķļņšūžĀČĒĢĪĶĻŅŠŪŽ')}{re.escape(allowed_symbols)}]+$"
    if not re.match(pattern, form_input):
        raise ValidationError(f"Forbidden characters in {form_input}")


def valid_reg_number(form_input):
    pattern = r'^[A-Z]{2}\d*$'
    if not re.match(pattern, form_input):
        raise ValidationError(f"Wrong format: {form_input}, must be like LV900...045")


def valid_bank_account(form_input):
    pattern = r'^[A-Z]{2}\d{2}[A-Z]{4}\d{7,20}$'
    if not re.match(pattern, form_input):
        raise ValidationError(f"Wrong format: {form_input}, must be like LV79HABA...045")


def valid_meter_nr(form_input):
    form_input = form_input.strip()
    try:
        form_input = int(form_input)
    except ValueError:
        raise ValidationError("Must be a number")


def invalid_meters_count(form, meters, apartment):
    meter_type = form.cleaned_data['type']
    dynamic_field = f"{meter_type}_meters_count"
    current_meters_count = meters.filter(
        apartment_number=apartment,
        type=meter_type
    ).count()
    print('current count:' + str(current_meters_count))

    if hasattr(apartment, dynamic_field):
        value = getattr(apartment, dynamic_field)
        print('dynamic ' + str(value))
        if current_meters_count >= value:
            text = f'Cannot add meters of this type. Allowed for apartment: {getattr(apartment, dynamic_field)}'
            print(text)
            return text
        else:
            pass

def is_not_unique_incoming_bill(form, existing_bills):
    provider = form.cleaned_data['provider']
    number = form.cleaned_data['number']
    house = form.cleaned_data['house']
    service = form.cleaned_data['service']
    year = form.cleaned_data['year']
    month = form.cleaned_data['month']
    if existing_bills.filter(provider=provider, number=number, house=house, service=service, year=year, month=month).exists():
        return 'Incoming bill for this period and service is already registered. Please check the data.'
    else:
        return None
