from .models import IncomingBill, Apartment, Meter, MeterReading

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from datetime import datetime


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
    print(f"Calculating object count")
    # Handle both QuerySet and single Apartment object cases
    apartments_count = apartments.count() if hasattr(apartments, 'count') else 1
    
    for bill in bills:
        amount = bill.amount / apartments_count
        vat_amount = calculate_vat(bill, amount)
        public_positions.append({
            'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
            'amount': round(amount, 2),
            'quantity': round(bill.quantity_received / apartments_count, 2),
            'price_per_unit': bill.service.price_per_unit,
            'measuring_units': bill.service.measuring_units,
            'vat_amount': vat_amount,
            'total': round(float(amount) + vat_amount, 2),
            'living_person_count': 1,  # For object count bills, each apartment counts as 1
            'declared_person_count': 1,  # For object count bills, each apartment counts as 1
            'area': 1  # For object count bills, each apartment counts as 1
        })
        total_amount += float(amount) + float(vat_amount)
    return total_amount


def calculate_bills_for_person_count(house, bills, public_positions, apartment, Service, total_amount): 
    print(f"Calculating bills for person count")
    monthly_consumption = 0
    for bill in bills:
        bill_type = bill.service.service_type
        # pay for person count
        if bill_type == 'volume' and house.water_calculation_type_2 == 'living_person_count':
            bill_type = 'living_person_count'
        if bill_type == 'volume' and house.water_calculation_type_2 == 'declared_person_count':
            bill_type = 'declared_person_count'
        if bill_type == 'living_person_count':
            amount = float(house.norm_for_person * bill.service.price_per_unit * apartment.living_person_count)
            monthly_consumption = float(house.norm_for_person) * float(apartment.living_person_count)
            vat_amount = calculate_vat(bill, amount)
            public_positions.append({
                'area': apartment.area, 
                'living_person_count': apartment.living_person_count,
                'declared_person_count': apartment.declared_person_count,
                'quantity': monthly_consumption,
                'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                'service_type': bill.service.service_type,
                'amount': round(amount, 2),
                'norm_for_person': round(house.norm_for_person, 2),
                'price_per_unit': bill.service.price_per_unit,
                'measuring_units': bill.service.measuring_units,
                'vat_amount': vat_amount,
                'total': round(float(amount) + vat_amount, 2)
            })
        if bill_type == 'declared_person_count':
            amount = house.norm_for_person * bill.service.price_per_unit * apartment.declared_person_count
            monthly_consumption = house.norm_for_person * apartment.declared_person_count
            vat_amount = calculate_vat(bill, amount)
            public_positions.append({
                'area': apartment.area, 
                'living_person_count': apartment.living_person_count,
                'declared_person_count': apartment.declared_person_count,
                'quantity': monthly_consumption,
                'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                'service_type': bill.service.service_type,
                'amount': round(amount, 2),
                'pay_for_person': round(house.pay_for_person, 2),
                'price_per_unit': bill.service.price_per_unit,
                'measuring_units': bill.service.measuring_units,
                'vat_amount': vat_amount,
                'total': round(float(amount) + vat_amount, 2)
            })
            total_amount += float(amount) + float(vat_amount)
    return total_amount, monthly_consumption


def calculate_area_services(house, area_bills, apartment, public_positions, Service, total_amount):
    print(f"Calculating area services")
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

def get_current_reading(meter, year, month):
    current_reading = MeterReading.objects.filter(
        meter=meter,
        reading_date__year=year,
        reading_date__month=month
    ).first()
    return current_reading

def get_previous_reading(meter, year, month):
    prev_month = month - 1
    prev_year = year
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    prev_reading = MeterReading.objects.filter(
        meter=meter,
        reading_date__year=prev_year,
        reading_date__month=prev_month
    ).first()
    return prev_reading

def get_last_reading(meter, year, month):
    last_reading = MeterReading.objects.filter(
        meter=meter,
        reading_date__lt=datetime(year, month, 1)
    ).order_by('-reading_date').first()
    return last_reading

# executed in calculate_total_bills, apartment scope
def calculate_volume_services(volume_bills, apartment, selected_year, selected_month, individual_positions, Service, total_amount, monthly_consumption):
    print(f"Calculating volume services")
    quantity_received = 0
    for bill in volume_bills:
        quantity_received = bill.quantity_received
        print(f"Quantity received: {quantity_received}")
        # Use the mapping to get the correct meter type
        meter_type = SERVICE_TO_METER_TYPE.get(bill.service.name)
        if meter_type:
            meters = Meter.objects.filter(
                apartment_number=apartment,
                type=meter_type
            )
        
            for meter in meters:
                default_reading = meter.reading_default
                # Get previous reading for this meter
                last_reading = get_last_reading(meter, selected_year, selected_month)
                # print(f"Last reading for {meter.apartment_number.apartment_nr} {meter.type} {meter.number} meter: {last_reading}")
                # Get current month reading
                current_reading = get_current_reading(meter, selected_year, selected_month)
                # print(f"Current reading for {meter.apartment_number.apartment_nr} {meter.type} {meter.number} meter: {current_reading}")
                # Get previous month reading
                prev_reading = get_previous_reading(meter, selected_year, selected_month)
                # print(f"Previous reading for {meter.apartment_number.apartment_nr} {meter.type} {meter.number} meter: {prev_reading}")
                
                
                if current_reading and prev_reading:
                    consumption = current_reading.reading_value - prev_reading.reading_value
                elif current_reading and not prev_reading:
                    # If no previous month reading, use the last available reading
                    if last_reading:
                        consumption = current_reading.reading_value - last_reading.reading_value
                    else:
                        # If no last reading available, use default reading
                        consumption = current_reading.reading_value - default_reading
                else:
                    consumption = 0
                    # print(f"""No consumption for apartment {meter.apartment_number.apartment_nr} {meter.type} {meter.number} meter. 
                    #       Apartment has {meter.apartment_number.cold_meters_count} cold and {meter.apartment_number.hot_meters_count} hot meters.""")

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
                    'last_reading': last_reading,
                    'vat_amount': vat_amount,
                    'total': round(float(amount) + vat_amount, 2),
                    'quantity_received': bill.quantity_received
                })
                if total_amount is None:
                    total_amount = 0.0
                total_amount += float(amount) + float(vat_amount)
                print(f"Total amount volume bill calculations.py after calculation: {total_amount}")
    return total_amount, monthly_consumption, quantity_received


def calculate_water_difference(bills, apartment, selected_year, selected_month, individual_positions, total_consumption, total_amount, Service, apartments_with_missing_readings):    
    # Used in calculate_total_bills/calculate_volume_services. 
    # Calculates the difference between the total consumption and the quantity received.
    # Splits the difference between the apartments without meters.
    for bill in bills:
        house = bill.house
        if bill.service.name == 'cold_water' or bill.service.name == 'hot_water':
            if bill.quantity_received > total_consumption:
                difference = float(bill.quantity_received) - float(total_consumption)
                if apartment in apartments_with_missing_readings:
                    difference_for_apartment = difference/len(apartments_with_missing_readings)
                else:
                    if house.water_difference_calculation == 'object_count': # MK 524.10.1
                        difference_for_apartment = difference / house.apartment_count
                    elif house.water_difference_calculation in ['last_month_consumption', 'last_3_months_consumption']: # MK 524.10.2 and 524.10.3
                        # Get last month's consumption for this apartment
                        if selected_month == 1:
                            last_month = 12
                            last_year = selected_year - 1
                        else:
                            last_month = selected_month - 1
                            last_year = selected_year
                        
                        # Get all meters for this apartment
                        apartment_meters = Meter.objects.filter(
                            apartment_number=apartment,
                            type__in=['cold', 'hot']
                        )
                        
                        # Calculate total consumption for last month
                        last_month_consumption = 0
                        if apartment_meters.count() > 0:
                            for meter in apartment_meters:
                                last_reading = MeterReading.objects.filter(
                                    meter=meter,
                                    reading_date__year=last_year,
                                    reading_date__month=last_month
                                ).first()
                            
                                if last_reading:
                                    # Get the reading before last month
                                    if last_month == 1:
                                        prev_month = 12
                                        prev_year = last_year - 1
                                    else:
                                        prev_month = last_month - 1
                                        prev_year = last_year
                                        
                                    prev_reading = MeterReading.objects.filter(
                                        meter=meter,
                                        reading_date__year=prev_year,
                                        reading_date__month=prev_month
                                    ).first()

                                    if prev_reading:
                                        last_month_consumption += last_reading.reading_value - prev_reading.reading_value
                                    else:
                                        print(f"No previous reading for {meter.apartment_number.apartment_nr} {meter.type} meter")
                                else:
                                    print(f"No last reading for {meter.apartment_number.apartment_nr} {meter.type} meter")
                        else:
                            print(f"No meters found for apartment {apartment.apartment_nr}")
                                
                        # Get the previous month's bill amount
                        previous_month_bill = IncomingBill.objects.filter(
                            house=house,
                            service=bill.service,
                            year=last_year,
                            month=last_month
                        ).first()

                        if house.water_difference_calculation == 'last_month_consumption': # MK 524.10.2
                            if previous_month_bill:
                                if last_month_consumption > 0:
                                    proportion = last_month_consumption / previous_month_bill.quantity_received
                                else:
                                    difference_for_apartment = apartment.living_person_count * house.norm_for_person
                            else:
                                proportion = 0
                        elif house.water_difference_calculation == 'last_3_months_consumption': # MK 524.10.3
                            # Calculate consumption for previous 3 months
                            three_months_consumption = last_month_consumption
                            three_months_bill_quantity = 0
                            
                            # Get the two months before last month
                            for i in range(2):
                                if last_month == 1:
                                    last_month = 12
                                    last_year -= 1
                                else:
                                    last_month -= 1
                                
                                # Get consumption for this month
                                month_consumption = 0
                                for meter in apartment_meters:
                                    current_reading = MeterReading.objects.filter(
                                        meter=meter,
                                        reading_date__year=last_year,
                                        reading_date__month=last_month
                                    ).first()
                                    
                                    if current_reading:
                                        if last_month == 1:
                                            prev_month = 12
                                            prev_year = last_year - 1
                                        else:
                                            prev_month = last_month - 1
                                            prev_year = last_year
                                            
                                        prev_reading = MeterReading.objects.filter(
                                            meter=meter,
                                            reading_date__year=prev_year,
                                            reading_date__month=prev_month
                                        ).first()
                                        
                                        if prev_reading:
                                            month_consumption += current_reading.reading_value - prev_reading.reading_value
                                
                                three_months_consumption += month_consumption
                                
                                # Get bill amount for this month
                                month_bill = IncomingBill.objects.filter(
                                    house=house,
                                    service=bill.service,
                                    year=last_year,
                                    month=last_month
                                ).first()
                                
                                if month_bill:
                                    three_months_bill_quantity += month_bill.quantity_received
                            
                            if three_months_bill_quantity > 0:
                                proportion = three_months_consumption / three_months_bill_quantity
                            else:
                                proportion = 0

                            # Calculate difference based on the proportion
                            difference_for_apartment = (bill.quantity_received - total_consumption) * proportion

                amount = difference_for_apartment * float(bill.service.price_per_unit)
                vat_amount = calculate_vat(bill, amount)
                individual_positions.append({
                    'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name) + ' (difference)',
                    'amount': round(amount, 2),
                    'vat_amount': vat_amount,
                    'total': round(float(amount) + vat_amount, 2)
                })
                print(f"T

                total_amount = total_amount + float(amount) + float(vat_amount)
    return total_amount
    
# def get_previous_months_readings(bills, house, apartment):
#     for bill in bills:
        # if bill.service.name == 'cold_water':

def check_apartment_water_meter_readings(apartment, year, month):
    """
    Checks if an apartment's water meters have readings for the specified month.
    If no readings found, checks previous 2 months.
    
    Args:
        apartment: Apartment object
        year: Year to check
        month: Month to check
        
    Returns:
        tuple: (has_readings, missing_meters, last_reading_date, missing_readings_data)
            has_readings: Boolean indicating if any meter has readings
            missing_meters: List of meter types missing readings
            last_reading_date: Date of the most recent reading found (None if no readings)
            missing_readings_data: Dictionary of missing readings data
    """
    # Get all water meters for the apartment
    water_meters = Meter.objects.filter(
        apartment_number=apartment,
        type__in=['cold', 'hot']
    )
    
    if not water_meters.exists():
        return False, ['cold', 'hot'], None, {}
    
    missing_meters = []
    missing_readings_data = {}
    last_reading_date = None
    
    for meter in water_meters:
        # Try current month
        reading = MeterReading.objects.filter(
            meter=meter,
            reading_date__year=year,
            reading_date__month=month
        ).first()
        
        if not reading:
            missing_readings_data['current_month'] = {
                'apartment_nr': apartment.apartment_nr,
                'meter_type': meter.type,
                'month': month,
                'year': year
            }
            # Try previous month
            if month == 1:
                prev_month = 12
                prev_year = year - 1
            else:
                prev_month = month - 1
                prev_year = year
                
            reading = MeterReading.objects.filter(
                meter=meter,
                reading_date__year=prev_year,
                reading_date__month=prev_month
            ).first()
            
            if not reading:
                missing_readings_data['previous_month'] = {
                    'apartment_nr': apartment.apartment_nr,
                    'meter_type': meter.type,
                    'month': prev_month,
                    'year': prev_year
                }
                # Try month before previous
                if prev_month == 1:
                    prev_prev_month = 12
                    prev_year = prev_year - 1
                else:
                    prev_prev_month = prev_month - 1
                    prev_year = prev_year
                    
                reading = MeterReading.objects.filter(
                    meter=meter,
                    reading_date__year=prev_year,
                    reading_date__month=prev_prev_month
                ).first()
                
                if not reading:
                    missing_readings_data['two_months_ago'] = {
                        'apartment_nr': apartment.apartment_nr,
                        'meter_type': meter.type,
                        'month': prev_prev_month,
                        'year': prev_year
                    }
        if not reading:
            missing_meters.append(meter.type)
        else:
            if last_reading_date is None or reading.reading_date > last_reading_date:
                last_reading_date = reading.reading_date
    
    return len(missing_meters) < len(water_meters), missing_meters, last_reading_date, missing_readings_data

def calculate_norm_consumption_for_apartments_without_meters(house, apartments_without_meters, selected_year, selected_month):
    """
    Calculates monthly consumption for apartments without meters based on person norms.
    
    Args:
        house: House object
        apartments_without_meters: List of Apartment objects that don't have meters
        selected_year: Year to calculate for
        selected_month: Month to calculate for
        
    Returns:
        float: Total consumption based on norms for apartments without meters
    """
    total_norm_consumption = 0
    
    for apartment in apartments_without_meters:
        # Calculate consumption based on living persons
        if house.water_calculation_type_2 == 'living_person_count':
            norm_consumption = house.norm_for_person * apartment.living_person_count
        # Calculate consumption based on declared persons
        elif house.water_calculation_type_2 == 'declared_person_count':
            norm_consumption = house.norm_for_person * apartment.declared_person_count
        # If no person count type specified, use living persons
        else:
            norm_consumption = house.norm_for_person * apartment.living_person_count
            
        total_norm_consumption += norm_consumption
        
    return total_norm_consumption
