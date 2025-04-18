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
    for bill in bills:
        bill_type = bill.service.service_type
        
        # pay for person count
        if bill_type == 'volume' and house.water_calculation_type_2 == 'living_person_count':
            bill_type = 'living_person_count'
            # print(f"VOLUME TO LIVING PERSON COUNT")
        if bill_type == 'volume' and house.water_calculation_type_2 == 'declared_person_count':
            bill_type = 'declared_person_count'
            # print(f"VOLUME TO DECLARED PERSON COUNT")
        if bill_type == 'living_person_count':
            amount = house.pay_for_person * apartment.living_person_count
            vat_amount = calculate_vat(bill, amount)
            public_positions.append({
                'area': apartment.area, 
                'living_person_count': apartment.living_person_count,
                'declared_person_count': apartment.declared_person_count,
                'quantity': round(bill.quantity_received / house.living_person_count * apartment.living_person_count, 2),                
                'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                'service_type': bill.service.service_type,
                'amount': round(amount, 2),
                'pay_for_person': round(house.pay_for_person, 2),
                'price_per_unit': bill.service.price_per_unit,
                'measuring_units': bill.service.measuring_units,
                'vat_amount': vat_amount,
                'total': round(float(amount) + vat_amount, 2)
            })
        if bill_type == 'declared_person_count':
            amount = house.pay_for_person * apartment.declared_person_count
            vat_amount = calculate_vat(bill, amount)
            public_positions.append({
                'area': apartment.area, 
                'living_person_count': apartment.living_person_count,
                'declared_person_count': apartment.declared_person_count,
                'quantity': round(bill.quantity_received / house.declared_person_count * apartment.declared_person_count, 2),
                'service': dict(Service.NAME_CHOICES).get(bill.service.name, bill.service.name),
                'service_type': bill.service.service_type,
                'amount': round(amount, 2),
                'pay_for_person': round(house.pay_for_person, 2),
                'price_per_unit': bill.service.price_per_unit,
                'measuring_units': bill.service.measuring_units,
                'vat_amount': vat_amount,
                'total': round(float(amount) + vat_amount, 2)
            })
        # print(f"Amount: {amount}")
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


def calculate_water_difference(bills, apartment, selected_year, selected_month, individual_positions, total_consumption, total_amount, Service):    
    # Used in calculate_total_bills/calculate_volume_services. 
    # Calculates the difference between the total consumption and the quantity received.
    # Splits the difference between the apartments without meters.

    for bill in bills:
        house = bill.house
        if bill.service.name == 'cold_water':
            if bill.quantity_received > total_consumption:
                if house.water_difference_calculation == 'object_count': # MK 524.10.1
                    difference = (bill.quantity_received - total_consumption) / house.apartment_count
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
                        print(f"No meters for {apartment.apartment_nr}")
                            
                            
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
                                print(f"Proportion: {proportion} l254")
                            else:
                                print(f"No last month consumption for {house.address} {bill.service.name}")
                                difference = apartment.living_person_count * house.pay_for_person
                                print(f"Difference: {difference} l258")
                        else:
                            print(f"No previous month bill for {house.address} {bill.service.name}")
                            proportion = 0
                            print(f"Proportion: {proportion} l262")
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
                            print(f"No previous 3 months bills for {house.address} {bill.service.name}")
                            proportion = 0

                    
                        # Calculate difference based on the proportion
                        difference = (bill.quantity_received - total_consumption) * proportion
                        
                    else:
                        print(f"Difference: {difference} l321")
                print(str(house.water_difference_calculation))
                print(f"Service: {bill.service.name} Price per unit: {bill.service.price_per_unit} l328")
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
    