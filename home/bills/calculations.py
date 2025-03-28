from .models import IncomingBill, Apartment
# from .views import public_positions, individual_positions

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


def calculate_object_count_bills(house, bills, public_positions, apartments, Service, total_amount):
    for bill in bills:
        amount = bill.amount / apartments.count()
        public_positions.append({
            'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
            'amount': round(amount, 2),
            'quantity': round(bill.quantity_received / apartments.count(), 2),
            'price_per_unit': bill.service.price_per_unit,
            'measuring_units': bill.service.measuring_units
        })
        total_amount += amount


def calculate_bills_for_person_count(house, bills, public_positions, apartment, Service, total_amount): 
    for bill in bills:
        # pay for person count
        if bill.service.service_type == 'living_person_count':
            pay_for_person = bill.amount / house.living_person_count
            apartment_living_person_count = apartment.living_person_count
            amount = pay_for_person * apartment_living_person_count
            public_positions.append({
                'living_person_count': apartment_living_person_count,
                'quantity': round(bill.quantity_received / house.living_person_count * apartment.living_person_count, 2),                
                'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                'service_type': bill.service.service_type,
                'amount': round(amount, 2),
                'pay_for_person': round(pay_for_person, 2),

                'price_per_unit': bill.service.price_per_unit,
                'measuring_units': bill.service.measuring_units
            })
        if bill.service.service_type == 'declared_person_count':
            pay_for_person = bill.amount / house.declared_person_count
            amount = pay_for_person * apartment.declared_person_count
            public_positions.append({
                'declared_person_count': apartment.declared_person_count,
                'quantity': round(bill.quantity_received / house.declared_person_count * apartment.declared_person_count, 2),
                'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                'service_type': bill.service.service_type,
                'amount': round(amount, 2),
                'pay_for_person': round(pay_for_person, 2),
                'price_per_unit': bill.service.price_per_unit,
                'measuring_units': bill.service.measuring_units
            })
        total_amount += amount


