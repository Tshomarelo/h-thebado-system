from django.core.management.base import BaseCommand
from django.utils import timezone
from reconciliation.models import FuelSale, OilSale
from datetime import timedelta

class Command(BaseCommand):
    help = 'Calculates daily totals for Diesel, ULP, and Oil sales'

    def handle(self, *args, **options):
        today = timezone.now().date()

        # Fuel sales
        fuel_sales = FuelSale.objects.filter(shift__created_at__date=today)
        diesel_sales = fuel_sales.filter(product_type='Diesel')
        ulp_sales = fuel_sales.filter(product_type='ULP')

        total_diesel_volume = sum(s.litres_sold for s in diesel_sales)
        total_diesel_amount = sum(s.amount for s in diesel_sales)

        total_ulp_volume = sum(s.litres_sold for s in ulp_sales)
        total_ulp_amount = sum(s.amount for s in ulp_sales)

        # Oil sales
        oil_sales = OilSale.objects.filter(sale_datetime__date=today)
        total_oil_units = sum(o.quantity_sold for o in oil_sales)
        total_oil_amount = sum(o.quantity_sold * o.price_per_unit_at_sale for o in oil_sales)

        # Totals
        grand_total_volume = total_diesel_volume + total_ulp_volume
        grand_total_amount = total_diesel_amount + total_ulp_amount + total_oil_amount

        self.stdout.write(self.style.SUCCESS(f"🗓 Fuel & Oil Sales Summary for {today}"))
        self.stdout.write(f"🚛 Diesel: {total_diesel_volume} L — R {total_diesel_amount:.2f}")
        self.stdout.write(f"⛽️ ULP: {total_ulp_volume} L — R {total_ulp_amount:.2f}")
        self.stdout.write(f"🛢 Oil: {total_oil_units} units — R {total_oil_amount:.2f}")
        self.stdout.write("—" * 50)
        self.stdout.write(f"📊 TOTAL VOLUME (Fuel only): {grand_total_volume} L")
        self.stdout.write(f"💰 TOTAL AMOUNT (Fuel + Oil): R {grand_total_amount:.2f}")
