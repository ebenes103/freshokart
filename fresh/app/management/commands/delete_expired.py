from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import Product

class Command(BaseCommand):
    help = 'Delete expired products'
    
    def handle(self, *args, **kwargs):
        expired_products = Product.objects.filter(expiry_date__lt=timezone.now())
        count = expired_products.count()
        expired_products.delete()
        self.stdout.write(f'Deleted {count} expired products')