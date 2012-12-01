"""fix_problem_counts management command
to run type (on the command line:)

python manage.py fix_problem_counts
"""
from django.core.management.base import NoArgsCommand
from django.db.models import signals
from askbot import models

class Command(NoArgsCommand):
    """Command class for "fix_problem_counts" 
    """

    def remove_save_signals(self):
        """removes signals on model pre-save and
        post-save, so that there are no side-effects
        besides actually updating the problem counts
        """
        signals.pre_save.receivers = []
        signals.post_save.receivers = []

    def handle(self, *arguments, **options):
        """function that handles the command job
        """
        self.remove_save_signals()
        for thread in models.Thread.objects.all():
            thread.update_problem_count()
