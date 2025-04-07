from .models import IncomingBill, Apartment, Meter, MeterReading
# from .views import public_positions, individual_positions

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


SERVICE_TO_METER_TYPE = {
    'cold_water': 'cold',
    'hot_water': 'hot',
    'electricity': 'electricity',
    'heat': 'heat',
    'other': 'other'
}



def calculate_vat(bill_data, total_amount):
    if bill_data.service.name == 'heat':
        vat_amount = '{:.2f}'.format(float(total_amount) * 0.12)
    else:
        vat_amount = '{:.2f}'.format(float(total_amount) * 0.21)
    return float(vat_amount)


def calculate_object_count_bills(house, bills, public_positions, apartments, Service, total_amount):
    for bill in bills:
        amount = bill.amount / apartments.count()
        vat_amount = calculate_vat(bill, amount)
        public_positions.append({
            'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
            'amount': round(amount, 2),
            'quantity': round(bill.quantity_received / apartments.count(), 2),
            'price_per_unit': bill.service.price_per_unit,
            'measuring_units': bill.service.measuring_units,
            'vat_amount': vat_amount,
            'total': round(float(amount) + vat_amount, 2)
        })
        total_amount += float(amount) + float(vat_amount)
    return total_amount


def calculate_bills_for_person_count(house, bills, public_positions, apartment, Service, total_amount): 
    for bill in bills:
        # pay for person count
        if bill.service.service_type == 'living_person_count':
            pay_for_unit = bill.amount / house.living_person_count
            amount = pay_for_unit * apartment.living_person_count
            vat_amount = calculate_vat(bill, amount)
            public_positions.append({
                'living_person_count': apartment.living_person_count,
                'quantity': round(bill.quantity_received / house.living_person_count * apartment.living_person_count, 2),                
                'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                'service_type': bill.service.service_type,
                'amount': round(amount, 2),
                'pay_for_unit': round(pay_for_unit, 2),
                'price_per_unit': bill.service.price_per_unit,
                'measuring_units': bill.service.measuring_units,
                'vat_amount': vat_amount,
                'total': round(float(amount) + vat_amount, 2)
            })
        if bill.service.service_type == 'declared_person_count':
            pay_for_unit = bill.amount / house.declared_person_count
            amount = pay_for_unit * apartment.declared_person_count
            vat_amount = calculate_vat(bill, amount)
            public_positions.append({
                'declared_person_count': apartment.declared_person_count,
                'quantity': round(bill.quantity_received / house.declared_person_count * apartment.declared_person_count, 2),
                'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                'service_type': bill.service.service_type,
                'amount': round(amount, 2),
                'pay_for_unit': round(pay_for_unit, 2),
                'price_per_unit': bill.service.price_per_unit,
                'measuring_units': bill.service.measuring_units,
                'vat_amount': vat_amount,
                'total': round(float(amount) + vat_amount, 2)
            })
        total_amount += float(amount) + float(vat_amount)
    return total_amount


def calculate_area_services(house, area_bills, apartment, public_positions, Service, total_amount):
    for bill in area_bills:
        pay_for_unit = bill.amount / house.area_of_apartments_total
        amount = pay_for_unit * apartment.area
        vat_amount = calculate_vat(bill, amount)
        public_positions.append({
            'area': apartment.area,
            'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
            'service_type': bill.service.service_type,
            'amount': round(amount, 2),
            'quantity': round(bill.quantity_received / house.area_of_apartments_total * apartment.area, 2),     
            'pay_for_unit': round(pay_for_unit, 2),
            'price_per_unit': bill.service.price_per_unit,
            'measuring_units': bill.service.measuring_units,
            'vat_amount': vat_amount,
            'total': round(float(amount) + vat_amount, 2)
        })
        total_amount += float(amount) + float(vat_amount)
    return total_amount

def calculate_volume_services(volume_bills, apartment, selected_year, selected_month, individual_positions, Service, total_amount, monthly_consumption):
    for bill in volume_bills:
        # Use the mapping to get the correct meter type
        meter_type = SERVICE_TO_METER_TYPE.get(bill.service.name)
        if meter_type:
            meters = Meter.objects.filter(
                apartment_number=apartment,
                type=meter_type
            )
        
            for meter in meters:
                default_reading = meter.reading_default
                # Get current month reading
                current_reading = MeterReading.objects.filter(
                    meter=meter,
                    reading_date__year=selected_year,
                    reading_date__month=selected_month
                ).first()
                
                # Get previous month reading
                if selected_month == 1:
                    prev_month = 12
                    prev_year = selected_year - 1
                else:
                    prev_month = selected_month - 1
                    prev_year = selected_year
                    
                prev_reading = MeterReading.objects.filter(
                    meter=meter,
                    reading_date__year=prev_year,
                    reading_date__month=prev_month
                ).first()
                
                if current_reading and prev_reading:
                    consumption = current_reading.reading_value - prev_reading.reading_value
                elif current_reading and not prev_reading:
                    # assume that the previous reading is missing and the current reading is the first reading
                    consumption = current_reading.reading_value - default_reading
                else:
                    consumption = 0
                    print(f"No consumption for {meter.apartment_number.apartment_nr} {meter.type} meter")

                monthly_consumption += consumption
                
                amount = consumption * bill.service.price_per_unit
                vat_amount = calculate_vat(bill, amount)
                individual_positions.append({
                    'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                    'meter': meter,
                    'consumption': round(consumption, 3),
                    'amount': round(amount, 2),
                    'price_per_unit': bill.service.price_per_unit,
                    'measuring_units': bill.service.measuring_units,
                    'current_reading': current_reading,
                    'prev_reading': prev_reading,
                    'default_reading': default_reading,
                    'vat_amount': vat_amount,
                    'total': round(float(amount) + vat_amount, 2)
                })
                if total_amount is None:
                    total_amount = 0.0
                total_amount += float(amount) + float(vat_amount)
                
    return total_amount, monthly_consumption

def calculate_house_total_consumption(volume_bills, house_total_consumption):
    for bill in volume_bills:
        house_total_consumption.append((bill.service.name, bill.quantity_received))
    return house_total_consumption

def calculate_meters_total_consumption(volume_bills, meters_total_consumption, selected_year, selected_month):
    for bill in volume_bills:
        meter_type = SERVICE_TO_METER_TYPE.get(bill.service.name)
        if meter_type:
            meters = Meter.objects.filter(
                type=meter_type
            )   
            for meter in meters:
                default_reading = meter.reading_default
                # Get current month reading
                current_reading = MeterReading.objects.filter(
                    meter=meter,
                    reading_date__year=selected_year,
                    reading_date__month=selected_month
                ).first()
                
                # Get previous month reading
                if selected_month == 1:
                    prev_month = 12
                    prev_year = selected_year - 1
                else:
                    prev_month = selected_month - 1
                    prev_year = selected_year
                    
                prev_reading = MeterReading.objects.filter(
                    meter=meter,
                    reading_date__year=prev_year,
                    reading_date__month=prev_month
                ).first()
                
                if current_reading and prev_reading:
                    consumption = current_reading.reading_value - prev_reading.reading_value
                elif current_reading and not prev_reading:
                    # assume that the previous reading is missing and the current reading is the first reading
                    consumption = current_reading.reading_value - default_reading
                else:
                    consumption = 0
                    print(f"No consumption for {meter.apartment_number.apartment_nr} {meter.type} meter")

                meters_total_consumption.append((meter_type, consumption))
            
    return meters_total_consumption

def calculate_water_difference(bills, individual_positions, total_consumption, total_amount, Service):
    for bill in bills:
        print(f"Bill: {bill.service.service_type}")
        house = bill.house
        if bill.service.name == 'cold_water':
            if bill.quantity_received > total_consumption:
                difference = (bill.quantity_received - total_consumption) / house.apartment_count
                amount = difference * bill.service.price_per_unit
                vat_amount = calculate_vat(bill, amount)
                individual_positions.append({
                    'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name) + ' (difference)',
                    'amount': round(amount, 2),
                    'vat_amount': vat_amount,
                    'total': round(float(amount) + vat_amount, 2)
                })
                total_amount += float(amount) + float(vat_amount)
    return total_amount
    