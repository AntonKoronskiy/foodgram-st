import csv
import os
from django.core.management.base import BaseCommand

from recipe.models import Ingredients
from foodgram import settings
from typing import List


ingredients_to_create: List[Ingredients] = []
existing_names = set(Ingredients.objects.values_list('name', flat=True))


class Command(BaseCommand):
    help = "Загрузка данных об ингредиентах в базу данных"

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')

        with open(path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)

            for row in reader:
                if len(row) < 2:
                    continue

                name = row[0].strip()
                unit = row[1].strip()

                if name and unit and name not in existing_names:
                    ingredients_to_create.append(
                        Ingredients(name=name, measurement_unit=unit))
                    existing_names.add(name)

        if ingredients_to_create:
            Ingredients.objects.bulk_create(
                ingredients_to_create,
                batch_size=1000
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно загружено {len(ingredients_to_create)} ингредиентов"
            )
        )
