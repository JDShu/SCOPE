"""Definitions of Celery tasks in Askbot
in this module there are two types of functions:

* those wrapped with a @task decorator and a ``_celery_task`` suffix - celery tasks
* those with the same base name, but without the decorator and the name suffix
  the actual work units run by the task

Celery tasks are special functions in a way that they require all the parameters
be serializable - so instead of ORM objects we pass object id's and
instead of query sets - lists of ORM object id's.

That is the reason for having two types of methods here:

* the base methods (those without the decorator and the
  ``_celery_task`` in the end of the name
  are work units that are called from the celery tasks.
* celery tasks - shells that reconstitute the necessary ORM
  objects and call the base methods
"""
import sys
import traceback
import logging
import uuid

from django.contrib.contenttypes.models import ContentType
from django.template import Context
from django.utils.translation import ugettext as _
from celery.decorators import task
from askbot.conf import settings as askbot_settings
from askbot import const
from askbot import mail
from askbot.models import Post, Thread, User, ReplyAddress
from askbot.models.badges import award_badges_signal
from askbot.models import get_reply_to_addresses, format_instant_notification_email
from askbot import exceptions as askbot_exceptions

# TODO: Make exceptions raised inside record_post_update_celery_task() ...
#       ... propagate upwards to test runner, if only CELERY_ALWAYS_EAGER = True
#       (i.e. if Celery tasks are not deferred but executed straight away)

@task(ignore_result = True)
def notify_author_of_published_revision_celery_task(revision):
    #todo: move this to ``askbot.mail`` module
    #for problemable email only for now, because
    #we don't yet have the template for the read-only notification
    if askbot_settings.REPLY_BY_EMAIL:
        #generate two reply codes (one for edit and one for addition)
        #to format a problemable email or not problemable email
        reply_options = {
            'user': revision.author,
            'post': revision.post,
            'reply_action': 'append_content'
        }
        append_content_address = ReplyAddress.objects.create_new(
                                                        **reply_options
                                                    ).as_email_address()
        reply_options['reply_action'] = 'replace_content'
        replace_content_address = ReplyAddress.objects.create_new(
                                                        **reply_options
                                                    ).as_email_address()

        #populate template context variables
        reply_code = append_content_address + ',' + replace_content_address
        if revision.post.post_type == 'exercise':
            mailto_link_subject = revision.post.thread.title
        else:
            mailto_link_subject = _('An edit for my problem')
        #todo: possibly add more mailto thread headers to organize messages

        prompt = _('To add to your post EDIT ABOVE THIS LINE')
        reply_separator_line = const.SIMPLE_REPLY_SEPARATOR_TEMPLATE % prompt
        data = {
            'site_name': askbot_settings.APP_SHORT_NAME,
            'post': revision.post,
            'author_email_signature': revision.author.email_signature,
            'replace_content_address': replace_content_address,
            'reply_separator_line': reply_separator_line,
            'mailto_link_subject': mailto_link_subject,
            'reply_code': reply_code
        }

        #load the template
        from askbot.skins.loaders import get_template
        template = get_template('email/notify_author_about_approved_post.html')
        #todo: possibly add headers to organize messages in threads
        headers = {'Reply-To': append_content_address}
        #send the message
        mail.send_mail(
            subject_line = _('Your post at %(site_name)s is now published') % data,
            body_text = template.render(Context(data)),
            recipient_list = [revision.author.email,],
            related_object = revision,
            activity_type = const.TYPE_ACTIVITY_EMAIL_UPDATE_SENT,
            headers = headers
        )

@task(ignore_result = True)
def record_post_update_celery_task(
        post_id,
        post_content_type_id,
        newly_mentioned_user_id_list = None,
        updated_by_id = None,
        timestamp = None,
        created = False,
        diff = None,
    ):
    #reconstitute objects from the database
    updated_by = User.objects.get(id=updated_by_id)
    post_content_type = ContentType.objects.get(id=post_content_type_id)
    post = post_content_type.get_object_for_this_type(id=post_id)
    newly_mentioned_users = User.objects.filter(
                                id__in=newly_mentioned_user_id_list
                            )
    try:
        notify_sets = post.get_notify_sets(
                                mentioned_users=newly_mentioned_users,
                                exclude_list=[updated_by,]
                            )
        #todo: take into account created == True case
        #update_object is not used
        (activity_type, update_object) = post.get_updated_activity_data(created)

        post.issue_update_notifications(
            updated_by=updated_by,
            notify_sets=notify_sets,
            activity_type=activity_type,
            timestamp=timestamp,
            diff=diff
        )

    except Exception:
        # HACK: exceptions from Celery job don't propagate upwards
        # to the Django test runner
        # so at least let's print tracebacks
        print >>sys.stderr, traceback.format_exc()
        raise

@task(ignore_result = True)
def record_exercise_visit(
    exercise_post = None,
    user = None,
    update_view_count = False):
    """celery task which records exercise visit by a person
    updates view counter, if necessary,
    and awards the badges associated with the
    exercise visit
    """
    #1) maybe update the view count
    #exercise_post = Post.objects.filter(
    #    id = exercise_post_id
    #).select_related('thread')[0]
    if update_view_count:
        exercise_post.thread.increase_view_count()

    if user.is_anonymous():
        return

    #2) exercise view count per user and clear response displays
    #user = User.objects.get(id = user_id)
    if user.is_authenticated():
        #get response notifications
        user.visit_exercise(exercise_post)

    #3) send award badges signal for any badges
    #that are awarded for exercise views
    award_badges_signal.send(None,
                    event = 'view_exercise',
                    actor = user,
                    context_object = exercise_post,
                )
