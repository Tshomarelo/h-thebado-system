from decimal import Decimal
from reconciliation.models import ReceivedStock



def calculate_stock_change_report(fuel_tank, dip_open, dip_close):
    if dip_open.record_datetime > dip_close.record_datetime:
        raise ValueError("Opening dip must be before closing dip.")

    # Get deliveries within window
    deliveries = ReceivedStock.objects.filter(
        fuel_tank=fuel_tank,
        delivery_date__range=(dip_open.record_datetime, dip_close.record_datetime)
    )

    total_delivered = sum(d.quantity_received_liters for d in deliveries)
    delivered_cost_total = sum((d.quantity_received_liters * d.cost_per_liter) for d in deliveries if d.cost_per_liter)

    # Usage = what we had - what remains + new stock received
    usage = dip_open.dip_reading_liters + total_delivered - dip_close.dip_reading_liters
    avg_cost_per_liter = delivered_cost_total / total_delivered if total_delivered else Decimal('0.00')
    estimated_cost = usage * avg_cost_per_liter if avg_cost_per_liter else Decimal('0.00')

    return {
        'fuel_tank': fuel_tank,
        'opening_liters': dip_open.dip_reading_liters,
        'closing_liters': dip_close.dip_reading_liters,
        'delivered_liters': total_delivered,
        'used_liters': usage,
        'average_cost_per_liter': avg_cost_per_liter,
        'estimated_total_cost': estimated_cost,
        'delivery_count': deliveries.count()
    }
