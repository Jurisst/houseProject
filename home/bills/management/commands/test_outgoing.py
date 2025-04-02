from django.core.management.base import BaseCommand
from bills.models import OutgoingBill, HouseManagement, Consumer, Apartment, Service

class Command(BaseCommand):
    help = 'Creates a test outgoing bill'

    def handle(self, *args, **options):
        try:
            outgoing_bill = OutgoingBill.objects.create(
                house_management=HouseManagement.objects.get(id=1),
                consumer=Consumer.objects.get(id=8),
                apartment=Apartment.objects.get(id=23),
                contract_nr="1234567890",
                year=2021,
                month=1,
                service=Service.objects.get(id=6),
                amount=100,
                extra_fields={"test": "test"}
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created outgoing bill: {outgoing_bill}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating outgoing bill: {str(e)}')) 