from django.core.management.base import BaseCommand
from donations.models import Restaurant, Badge


def award_badges_for_restaurant(restaurant):
    
   # Checks a single restaurant's total_donated_kg against all threshold-based
 #badges and awards any newly-qualified ones. Returns a list of newly awarded Badge objects.

    newly_awarded = []

    eligible_badges = Badge.objects.filter(
        threshold_kg__isnull=False,
        threshold_kg__lte=restaurant.total_donated_kg,
    )

    for badge in eligible_badges:
        if not restaurant.badges.filter(pk=badge.pk).exists():
            restaurant.badges.add(badge)
            newly_awarded.append(badge)

    return newly_awarded


class Command(BaseCommand):
    help = "Auto-award donor badges to all restaurants based on total_donated_kg"

    def handle(self, *args, **options):
        restaurants = Restaurant.objects.all()
        total_awarded = 0

        for restaurant in restaurants:
            newly_awarded = award_badges_for_restaurant(restaurant)
            if newly_awarded:
                names = ", ".join(b.name for b in newly_awarded)
                self.stdout.write(self.style.SUCCESS(
                    f"{restaurant.name}: awarded [{names}] (total_donated_kg={restaurant.total_donated_kg})"
                ))
                total_awarded += len(newly_awarded)

        if total_awarded == 0:
            self.stdout.write("No new badges to award — everyone's up to date.")
        else:
            self.stdout.write(self.style.SUCCESS(f"\nDone. Awarded {total_awarded} new badge(s) total."))