import os
import sys
import django
import json

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'home.settings')
django.setup()

from bills.models import OutgoingBill, HouseManagement, Consumer, Apartment, Service

try:
    # Create a new dictionary with all fields
    fields_dict = {
        "test2": "manually added",
        "service_name": "test service"
    }

    print("Fields dictionary before creating bill:", fields_dict)
    print("Fields dictionary type:", type(fields_dict))
    print("Fields dictionary JSON:", json.dumps(fields_dict))

    # First, create the bill without extra_fields
    outgoing_bill = OutgoingBill.objects.create(
        house_management=HouseManagement.objects.get(id=1),
        consumer=Consumer.objects.get(id=8),
        apartment=Apartment.objects.get(id=23),
        contract_nr="1234567890",
        year=2021,
        month=1,
        service=Service.objects.get(id=6),
        amount=100
    )

    # Then update the extra_fields separately
    outgoing_bill.extra_fields = fields_dict
    outgoing_bill.save()

    # Refresh the object from database to ensure we see the saved state
    outgoing_bill.refresh_from_db()

    print("\nOutgoing bill created with fields:", outgoing_bill.extra_fields)
    print("Outgoing bill fields type:", type(outgoing_bill.extra_fields))
    print("Outgoing bill fields JSON:", json.dumps(outgoing_bill.extra_fields))

    # Let's also check all outgoing bills to see what's in the database
    print("\nAll outgoing bills in database:")
    for bill in OutgoingBill.objects.all():
        print(f"Bill {bill.id}: {bill.extra_fields}")
        print(f"Bill {bill.id} fields type: {type(bill.extra_fields)}")
        print(f"Bill {bill.id} fields JSON: {json.dumps(bill.extra_fields)}")

except Exception as e:
    print(f"Error occurred: {str(e)}")
    import traceback
    traceback.print_exc()

