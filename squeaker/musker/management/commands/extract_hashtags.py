from django.core.management.base import BaseCommand


from ...models import Meep, MeepHashtag
class Command(BaseCommand):
    help = 'Extract hashtags from existing meeps'

    def add_arguments(self, parser):
        # Optional: Add command line arguments
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Delete existing hashtag associations before extracting',
        )

    def handle(self, *args, **options):
        # Optional: Delete existing hashtag associations
        if options['delete_existing']:
            deleted_count = MeepHashtag.objects.all().count()
            MeepHashtag.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted_count} existing hashtag associations')
            )

        # Get all meeps
        meeps = Meep.objects.all()
        total_meeps = meeps.count()
        processed = 0
        hashtags_found = 0

        self.stdout.write(f'Processing {total_meeps} meeps...')
        
        for meep in meeps:
            # Extract hashtags for this meep
            before_count = MeepHashtag.objects.filter(meep=meep).count()
            meep.extract_hashtags()
            after_count = MeepHashtag.objects.filter(meep=meep).count()
            
            hashtags_found += (after_count - before_count)
            processed += 1
            
            # Show progress every 100 meeps
            if processed % 100 == 0:
                self.stdout.write(f'Processed {processed}/{total_meeps} meeps...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Successfully processed {processed} meeps and found {hashtags_found} hashtag associations'
            )
        )