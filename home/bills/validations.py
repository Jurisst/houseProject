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