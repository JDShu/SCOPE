from django.core.management.base import NoArgsCommand
from askbot import models
from askbot import const
from askbot.conf import settings as askbot_settings
from django.utils.translation import ungettext
from askbot import mail
from askbot.utils.classes import ReminderSchedule
from askbot.models.exercise import Thread
from askbot.skins.loaders import get_template
from django.template import Context

DEBUG_THIS_COMMAND = False

class Command(NoArgsCommand):
    """management command that sends reminders
    about exercises without problems to all users
    """
    def handle_noargs(self, **options):
        if askbot_settings.ENABLE_EMAIL_ALERTS == False:
            return
        if askbot_settings.ENABLE_EXERCISE_WITHOUT_PROBLEM_REMINDERS == False:
            return
        #get exercises without problems, excluding closed and deleted
        #order it by descending added_at date
        schedule = ReminderSchedule(
            askbot_settings.DAYS_BEFORE_SENDING_EXERCISE_WITHOUT_PROBLEM_REMINDER,
            askbot_settings.EXERCISE_WITHOUT_PROBLEM_REMINDER_FREQUENCY,
            max_reminders = askbot_settings.MAX_EXERCISE_WITHOUT_PROBLEM_REMINDERS
        )

        exercises = models.Post.objects.get_exercises().exclude(
                                        thread__closed = True
                                    ).exclude(
                                        deleted = True
                                    ).added_between(
                                        start = schedule.start_cutoff_date,
                                        end = schedule.end_cutoff_date
                                    ).filter(
                                        thread__problem_count = 0
                                    ).order_by('-added_at')
        #for all users, excluding blocked
        #for each user, select a tag filtered subset
        #format the email reminder and send it
        for user in models.User.objects.exclude(status = 'b'):
            user_exercises = exercises.exclude(author = user)
            user_exercises = user.get_tag_filtered_exercises(user_exercises)

            if askbot_settings.GROUPS_ENABLED:
                user_groups = user.get_groups()
                user_exercises = user_exercises.filter(groups__in = user_groups)

            final_exercise_list = user_exercises.get_exercises_needing_reminder(
                user = user,
                activity_type = const.TYPE_ACTIVITY_EXERCISE_WITHOUT_PROBLEM_REMINDER_SENT,
                recurrence_delay = schedule.recurrence_delay
            )

            exercise_count = len(final_exercise_list)
            if exercise_count == 0:
                continue

            threads = Thread.objects.filter(id__in=[qq.thread_id for qq in final_exercise_list])
            tag_summary = Thread.objects.get_tag_summary_from_threads(threads)

            subject_line = ungettext(
                '%(exercise_count)d exercise without problem about %(topics)s',
                '%(exercise_count)d exercises without problems about %(topics)s',
                exercise_count
            ) % {
                'exercise_count': exercise_count,
                'topics': tag_summary
            }

            data = {
                    'site_url': askbot_settings.APP_URL,
                    'exercises': final_exercise_list,
                    'subject_line': subject_line
                   }

            template = get_template('email/exercise_without_problem_reminder.html')
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
