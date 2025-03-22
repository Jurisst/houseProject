from home.bills.models import IncomingBill, Apartment

def calculate_living_person_bills(house, incoming_bills):
    apartments = Apartment.objects.filter(address=house)
    living_person_count = house.living_person_count
    living_person_bills = incoming_bills.filter(service__service_type='living_person_count')
    
    for bill in living_person_bills:
        pay_for_living_person = bill.amount / living_person_count
        for apartment in apartments:
            amount = pay_for_living_person * apartment.living_person_count
    return living_person_bills

def calculate_declared_person_bills(incoming_bills):
    declared_person_bills = incoming_bills.filter(service__service_type='declared_person_count')
    return declared_person_bills
