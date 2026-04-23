import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fresh.settings')
django.setup()

from app.models import Category

categories = ['Vegetables', 'Fruits', 'Eggs', 'Fish', 'Meat']

for cat in categories:
    Category.objects.get_or_create(name=cat)
    print(f'Created category: {cat}')