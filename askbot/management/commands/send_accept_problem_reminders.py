import datetime
from django.core.management.base import NoArgsCommand
from django.conf import settings as django_settings
from askbot import models
from askbot import const
from askbot.conf import settings as askbot_settings
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from askbot import mail
from askbot.utils.classes import ReminderSchedule
from askbot.skins.loaders import get_template
from django.template import Context

DEBUG_THIS_COMMAND = False

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        if askbot_settings.ENABLE_EMAIL_ALERTS == False:
            return
        if askbot_settings.ENABLE_ACCEPT_PROBLEM_REMINDERS == False:
            return
        #get exercises without problems, excluding closed and deleted
        #order it by descending added_at date

        schedule = ReminderSchedule(
            askbot_settings.DAYS_BEFORE_SENDING_ACCEPT_PROBLEM_REMINDER,
            askbot_settings.ACCEPT_PROBLEM_REMINDER_FREQUENCY,
            askbot_settings.MAX_ACCEPT_PROBLEM_REMINDERS
        )

        exercises = models.Post.objects.get_exercises().exclude(
                                        deleted = True
                                    ).added_between(
                                        start = schedule.start_cutoff_date,
                                        end = schedule.end_cutoff_date
                                    ).filter(
                                        thread__problem_count__gt = 0
                                    ).filter(
                                        thread__accepted_problem__isnull=True #problem_accepted = False
                                    ).order_by('-added_at')
        #for all users, excluding blocked
        #for each user, select a tag filtered subset
        #format the email reminder and send it
        for user in models.User.objects.exclude(status = 'b'):
            user_exercises = exercises.filter(author = user)

            final_exercise_list = user_exercises.get_exercises_needing_reminder(
                activity_type = const.TYPE_ACTIVITY_ACCEPT_PROBLEM_REMINDER_SENT,
                user = user,
                recurrence_delay = schedule.recurrence_delay
            )
            #todo: rewrite using query set filter
            #may be a lot more efficient

            exercise_count = len(final_exercise_list)
            if exercise_count == 0:
                continue

            subject_line = _(
                'Accept the best problem for %(exercise_count)d of your exercises'
            ) % {'exercise_count': exercise_count}

            #todo - make a template for these
            if exercise_count == 1:
                reminder_phrase = _('Please accept the best problem for this exercise:')
            else:
                reminder_phrase = _('Please accept the best problem for these exercises:')

            data = {
                    'site_url': askbot_settings.APP_URL,
                    'exercises': final_exercise_list,
                    'reminder_phrase': reminder_phrase
                   }

            template = get_template('email/accept_problem_reminder.html')
            body_text = template.render(Context(data))

            if DEBUG_THIS_COMMAND:
                print "User: %s<br>\nSubject:%s<br>\nText: %s<br>\n" % \
                    (user.email, subject_line, body_text)
            else:
                mail.send_mail(
                    subject_line = subject_line,
                    body_text = body_text,
                    recipient_list = (user.email,)
                )
