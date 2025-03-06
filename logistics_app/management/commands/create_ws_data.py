from django.core.management.base import BaseCommand 
from logistics_app.models import Inventory, Product
from random import choice, randint
# Faker will help us generate testing data 
from faker import Faker
# Color text pip install colorama:
from colorama import Fore, Style
from faker.providers.company.en_PH import Provider as cp

# https://simpleisbetterthancomplex.com/tutorial/2018/08/27/how-to-create-custom-django-management-commands.html

class Command(BaseCommand):
    help = 'Creating random Inventory based on Products'

    def add_arguments(self, parser):
        parser.add_argument('-m', '--model', type=str, help='Model to Add (Inventory | Product)')
        parser.add_argument('-n', '--number', type=int, help='Number of Inventories')

    def handle(self, *args, **options):
        model = options['model']
        num = options['number'] if options['number'] > 0 else 1 
        fake = Faker()

        created_msg = ''

        if model[0].lower() == 'i': 
            if Product.objects.count() >= 1:
                av_prods = [prod for prod in Product.objects.all()]
                for _ in range(num):
                    chosen_prod = choice(av_prods)
                    # https://faker.readthedocs.io/en/master/
                    street_loc = f'{fake.street_name()}, {fake.country_code()}'
                    amount = randint(1, 200)
                    testing_inv = Inventory.objects.create(
                        product=chosen_prod,
                        stock = amount,
                        location=street_loc
                    )
                    # Actually saving our created inventory 
                    testing_inv.save() 
                created_msg = f'Successfully created: {num} Inventory Data'
            else: 
                print(Fore.RED + 'No Products Found. ' + Fore.YELLOW + 'Please use "create_ws_data -m Product" to create Testing Products' + Style.RESET_ALL)
        elif model[0].lower() == 'p':
            # Creating products 
            categories = [
                "Electronics",
                "Clothing & Apparel",
                "Home & Kitchen",
                "Beauty & Personal Care",
                "Health & Wellness",
                "Sports & Outdoors",
                "Automotive",
                "Toys & Games",
                "Books & Stationery",
                "Pet Supplies",
                "SaaS & Software",
                "Financial Services",
                "Consulting & Freelancing",
                "Marketing & Advertising",
                "Education & E-learning",
                "Legal & Compliance",
                "Real Estate & Property Management",
                "Logistics & Shipping",
                "Healthcare & Medical Services",
                "Event Planning & Catering",
                "Movies & TV Shows",
                "Music & Audio Streaming",
                "Gaming & Esports",
                "Podcasts & Radio",
                "News & Journalism",
                "Social Media Platforms",
                "Online Courses & Learning",
                "Travel & Tourism",
                "Food & Restaurants",
                "Fitness & Wellness",
                "Mobile Apps",
                "Web Development Services",
                "Cloud Computing",
                "AI & Machine Learning",
                "Cybersecurity",
                "Blockchain & Cryptocurrency",
                "Data Science & Analytics",
                "IT Support & Helpdesk",
                "Augmented Reality (AR) & Virtual Reality (VR)",
                "Art & Photography"
            ]

            # Adding the provider to use random_company_product
            fake.add_provider(cp)
            for _ in range(num):
                test_prod_info = {
                    'product_name': fake.random_company_product(),
                    'price': float(randint(1,200)),
                    'category': choice(categories)
                }

                my_prod = Product.objects.create(
                    product_name=test_prod_info['product_name'],
                    price=test_prod_info['price'],
                    category=test_prod_info['category']
                )

                my_prod.save()

            created_msg = f'Successfully created: {num} Product Data'
        
        print(Fore.GREEN + created_msg + Style.RESET_ALL)