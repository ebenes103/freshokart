from django.core.management.base import BaseCommand
from django.db import transaction
from app.models import District, City

class Command(BaseCommand):
    help = 'Load Kerala districts and cities into database'

    # Complete Kerala Districts
    KERALA_DISTRICTS = [
        'Thiruvananthapuram', 'Kollam', 'Pathanamthitta', 'Alappuzha',
        'Kottayam', 'Idukki', 'Ernakulam', 'Thrissur', 'Palakkad',
        'Malappuram', 'Kozhikode', 'Wayanad', 'Kannur', 'Kasaragod'
    ]

    # Cities/Towns by District
    CITIES_BY_DISTRICT = {
        'Thiruvananthapuram': [
            'Thiruvananthapuram', 'Attingal', 'Neyyattinkara',
            'Nedumangad', 'Varkala', 'Karakulam', 'Pothencode',
            'Pallippuram', 'Kallambalam', 'Kilimanoor'
        ],
        'Kollam': [
            'Kollam', 'Karunagappally', 'Paravur', 'Punalur', 
            'Kottarakkara', 'Chavara', 'Kundara', 'Sasthamkotta',
            'Kottiyam', 'Ochira', 'Anchal', 'Pathanapuram'
        ],
        'Pathanamthitta': [
            'Pathanamthitta', 'Adoor', 'Pandalam', 'Thiruvalla',
            'Ranni', 'Kozhencherry', 'Mallappally', 'Konni',
            'Aranmula', 'Elanthoor', 'Omalloor', 'Vechoochira'
        ],
        'Alappuzha': [
            'Alappuzha', 'Cherthala', 'Kayamkulam', 'Chengannur',
            'Haripad', 'Mavelikkara', 'Ambalappuzha', 'Kuttanad',
            'Aroor', 'Kanjikuzhy', 'Punnapra', 'Kalavoor'
        ],
        'Kottayam': [
            'Kottayam', 'Changanassery', 'Ettumanoor', 'Pala',
            'Vaikom', 'Erattupetta', 'Kanjirappally', 'Mundakkayam',
            'Ponkunnam', 'Kumarakom', 'Athirampuzha', 'Vakathanam'
        ],
        'Idukki': [
            'Thodupuzha', 'Kattappana', 'Adimali', 'Munnar',
            'Nedumkandam', 'Devikulam', 'Vandiperiyar', 'Rajakkad',
            'Kumily', 'Peerumade', 'Chakkupallam'
        ],
        'Ernakulam': [
            'Kochi', 'Aluva', 'Angamaly', 'Perumbavoor',
            'Muvattupuzha', 'Kothamangalam', 'Thrippunithura',
            'Kalamassery', 'North Paravur', 'Mattancherry',
            'Piravom', 'Kalady', 'Nedumbassery', 'Varappuzha'
        ],
        'Thrissur': [
            'Thrissur', 'Guruvayur', 'Chalakudy', 'Kodungallur',
            'Irinjalakuda', 'Kunnamkulam', 'Wadakkanchery',
            'Chelakkara', 'Chavakkad', 'Mala', 'Pavaratty',
            'Kattoor', 'Mundathikode', 'Kodakara'
        ],
        'Palakkad': [
            'Palakkad', 'Ottappalam', 'Shoranur', 'Pattambi',
            'Mannarkkad', 'Chittur', 'Alathur', 'Kollengode',
            'Nemmara', 'Vadakkencherry', 'Parli', 'Kuzhalmannam'
        ],
        'Malappuram': [
            'Malappuram', 'Manjeri', 'Tirur', 'Ponnani',
            'Perinthalmanna', 'Nilambur', 'Kottakkal', 'Kondotty',
            'Valanchery', 'Tanur', 'Parappanangadi', 'Edappal',
            'Wandoor', 'Areacode', 'Karuvarakundu'
        ],
        'Kozhikode': [
            'Kozhikode', 'Vadakara', 'Koyilandy', 'Feroke',
            'Ramanattukara', 'Mukkam', 'Payyoli', 'Balussery',
            'Koduvally', 'Thamarassery', 'Perambra', 'Kunnamangalam'
        ],
        'Wayanad': [
            'Kalpetta', 'Mananthavady', 'Sultan Bathery',
            'Padinharethara', 'Meppadi', 'Vythiri', 'Ambalavayal'
        ],
        'Kannur': [
            'Kannur', 'Thalassery', 'Taliparamba', 'Payyanur',
            'Iritty', 'Kuthuparamba', 'Mattannur', 'Panoor',
            'Sreekandapuram', 'Anthoor', 'Peralassery', 'Muzhappilangad'
        ],
        'Kasaragod': [
            'Kasaragod', 'Kanhangad', 'Nileshwaram', 'Manjeshwaram',
            'Uppala', 'Kumbla', 'Badiyadka', 'Cheruvathur',
            'Delhi', 'Mogral Puthur'
        ]
    }

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to load Kerala districts and cities...'))
        
        # Clear existing data (optional - comment out if you want to append)
        self.stdout.write('Clearing existing location data...')
        City.objects.all().delete()
        District.objects.all().delete()
        
        # Insert Districts
        self.stdout.write('Inserting districts...')
        district_objects = []
        for district_name in self.KERALA_DISTRICTS:
            district = District(name=district_name)
            district_objects.append(district)
        
        District.objects.bulk_create(district_objects)
        self.stdout.write(f'✓ Inserted {len(district_objects)} districts')
        
        # Insert Cities
        self.stdout.write('Inserting cities...')
        city_objects = []
        city_count = 0
        
        for district_name, cities in self.CITIES_BY_DISTRICT.items():
            try:
                district = District.objects.get(name=district_name)
                for city_name in cities:
                    city = City(
                        district=district,
                        name=city_name
                    )
                    city_objects.append(city)
                    city_count += 1
                    
                    # Bulk create in batches of 100 to avoid memory issues
                    if len(city_objects) >= 100:
                        City.objects.bulk_create(city_objects)
                        city_objects = []
                        self.stdout.write(f'  Inserted {city_count} cities so far...')
                        
            except District.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  District "{district_name}" not found'))
        
        # Insert remaining cities
        if city_objects:
            City.objects.bulk_create(city_objects)
        
        self.stdout.write(f'✓ Inserted {city_count} cities')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('LOCATION DATA LOADED SUCCESSFULLY!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Districts: {District.objects.count()}')
        self.stdout.write(f'Cities: {City.objects.count()}')
        self.stdout.write('='*50)