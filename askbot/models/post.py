from collections import defaultdict
import datetime
import operator
import cgi
import logging

from django.utils.html import strip_tags
from django.contrib.sitemaps import ping_google
from django.utils import html
from django.conf import settings
from django.contrib.auth.models import User
from django.core import urlresolvers
from django.db import models
from django.utils import html as html_utils
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.utils.http import urlquote as django_urlquote
from django.core import exceptions as django_exceptions
from django.core import cache
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

import askbot

from askbot.utils.slug import slugify
from askbot import const
from askbot.models.user import Activity
from askbot.models.user import EmailFeedSetting
from askbot.models.user import Group
from askbot.models.user import GroupMembership
from askbot.models.tag import Tag, MarkedTag
from askbot.models.tag import get_groups, tags_match_some_wildcard
from askbot.models.tag import get_global_group
from askbot.conf import settings as askbot_settings
from askbot import exceptions
from askbot.utils import markup
from askbot.utils.html import sanitize_html
from askbot.models.base import BaseQuerySetManager, DraftContent

#todo: maybe merge askbot.utils.markup and forum.utils.html
from askbot.utils.diff import textDiff as htmldiff
from askbot.utils import mysql

class PostToGroup(models.Model):
    post = models.ForeignKey('Post')
    group = models.ForeignKey(Group)

    class Meta:
        unique_together = ('post', 'group')
        app_label = 'askbot'
        db_table = 'askbot_post_groups'


class PostQuerySet(models.query.QuerySet):
    """
        Custom query set subclass for :class:`~askbot.models.Post`
        """
    #todo: we may not need this query set class,
    #as all methods on this class seem to want to
    #belong to Thread manager or Query set.

    #MAX:
    def get_by_text_query(self, search_query):
        """returns a query set of exercises,
            matching the full text query
            """
        return self.filter(
                           models.Q(thread__title__icontains = search_query)\
                           | models.Q(text__icontains = search_query)\
                           | models.Q(thread__tagnames = search_query)\
                           | models.Q(thread__posts__text__icontains = search_query, thread__posts__post_type='problem')\
                           | models.Q(thread__posts__text__icontains = search_query, thread__posts__post_type='solution')
                           )
    #        #todo - goes to thread - we search whole threads
    #        if getattr(settings, 'USE_SPHINX_SEARCH', False):
    #            matching_exercises = Exercise.sphinx_search.query(search_query)
    #            exercise_ids = [q.id for q in matching_exercises]
    #            return Exercise.objects.filter(deleted = False, id__in = exercise_ids)
    #        if settings.DATABASE_ENGINE == 'mysql' and mysql.supports_full_text_search():
    #            return self.filter(
    #                models.Q(thread__title__search = search_query)\
    #                | models.Q(text__search = search_query)\
    #                | models.Q(thread__tagnames__search = search_query)\
    #                | models.Q(problems__text__search = search_query)
    #            )
    #        elif 'postgresql_psycopg2' in askbot.get_database_engine_name():
    #            rank_clause = "ts_rank(exercise.text_search_vector, plainto_tsquery(%s))";
    #            search_query = '&'.join(search_query.split())
    #            extra_params = (search_query,)
    #            extra_kwargs = {
    #                'select': {'relevance': rank_clause},
    #                'where': ['text_search_vector @@ plainto_tsquery(%s)'],
    #                'params': extra_params,
    #                'select_params': extra_params,
    #                }
    #            return self.extra(**extra_kwargs)
    #        else:
    #            #fallback to dumb title match search
    #            return self.filter(thread__title__icontains=search_query)

    def added_between(self, start, end):
        """exercises added between ``start`` and ``end`` timestamps"""
        #todo: goes to thread
        return self.filter(
                           added_at__gt = start
                           ).exclude(
                                     added_at__gt = end
                                     )

    def get_exercises_needing_reminder(self,
                                       user = None,
                                       activity_type = None,
                                       recurrence_delay = None):
        """returns list of exercises that need a reminder,
            corresponding the given ``activity_type``
            ``user`` - is the user receiving the reminder
            ``recurrence_delay`` - interval between sending the
            reminders about the same exercise
            """
        #todo: goes to thread
        from askbot.models import Activity#avoid circular import
        exercise_list = list()
        for exercise in self:
            try:
                activity = Activity.objects.get(
                                                user = user,
                                                exercise = exercise,
                                                activity_type = activity_type
                                                )
                now = datetime.datetime.now()
                if now < activity.active_at + recurrence_delay:
                    continue
            except Activity.DoesNotExist:
                activity = Activity(
                                    user = user,
                                    exercise = exercise,
                                    activity_type = activity_type,
                                    content_object = exercise,
                                    )
            activity.active_at = datetime.datetime.now()
            activity.save()
            exercise_list.append(exercise)
        return exercise_list

    def get_author_list(self, **kwargs):
        #todo: - this is duplication - problem manager also has this method
        #will be gone when models are consolidated
        #note that method get_exercise_and_problem_contributors is similar in function
        #todo: goes to thread
        authors = set()
        for exercise in self:
            authors.update(exercise.get_author_list(**kwargs))
        return list(authors)


class PostManager(BaseQuerySetManager):
    def get_query_set(self):
        return PostQuerySet(self.model)

    def get_exercises(self):
        return self.filter(post_type='exercise')

    def get_problems(self, user = None):
        """returns query set of problem posts,
            optionally filtered to exclude posts of groups
            to which user does not belong"""
        problems = self.filter(post_type='problem')

        if askbot_settings.GROUPS_ENABLED:
            if user is None or user.is_anonymous():
                groups = [get_global_group()]
            else:
                groups = user.get_groups()
            problems = problems.filter(groups__in = groups).distinct()

        return problems

    #MAX:
    def get_solutions(self, user = None):
        """returns query set of solution posts,
            optionally filtered to exclude posts of groups
            to which user does not belong"""
        solutions = self.filter(post_type='solution')

        if askbot_settings.GROUPS_ENABLED:
            if user is None or user.is_anonymous():
                groups = [get_global_group()]
            else:
                groups = user.get_groups()
            solutions = solutions.filter(groups__in = groups).distinct()

        return solutions


    def get_comments(self):
        return self.filter(post_type='comment')

    def create_new_tag_wiki(self, text = None, author = None):
        return self.create_new(
                               None,#this post type is threadless
                               author,
                               datetime.datetime.now(),
                               text,
                               wiki = True,
                               post_type = 'tag_wiki'
                               )

    def create_new(
                   self,
                   thread,
                   author,
                   added_at,
                   text,
                   parent = None,
                   wiki = False,
                   is_private = False,
                   email_notify = False,
                   post_type = None,
                   by_email = False
                   ):
        # TODO: Some of this code will go to Post.objects.create_new

        assert(post_type in const.POST_TYPES)

        post = Post(
                    post_type = post_type,
                    thread = thread,
                    parent = parent,
                    author = author,
                    added_at = added_at,
                    wiki = wiki,
                    text = text,
                    #.html field is denormalized by the save() call
                    )

        if post.wiki:
            post.last_edited_by = post.author
            post.last_edited_at = added_at
            post.wikified_at = added_at

        #possibly modify the is_private, if one of the groups
        #mandates explicit publishing of the posts
        is_private = is_private or \
            (thread and thread.requires_response_moderation(author))

        parse_results = post.parse_and_save(author=author, is_private=is_private)

        from askbot.models import signals
        signals.post_updated.send(
                                  post=post,
                                  updated_by=author,
                                  newly_mentioned_users=parse_results['newly_mentioned_users'],
                                  timestamp=added_at,
                                  created=True,
                                  diff=parse_results['diff'],
                                  sender=post.__class__
                                  )

        post.add_revision(
                          author = author,
                          revised_at = added_at,
                          text = text,
                          comment = const.POST_STATUS['default_version'],
                          by_email = by_email
                          )

        return post

    #todo: instead of this, have Thread.add_problem()
    def create_new_problem(
                           self,
                           thread,
                           author,
                           added_at,
                           text,
                           wiki = False,
                           is_private = False,
                           email_notify = False,
                           by_email = False
                           ):
        problem = self.create_new(
                                  thread,
                                  author,
                                  added_at,
                                  text,
                                  wiki = wiki,
                                  is_private = is_private,
                                  post_type = 'problem',
                                  by_email = by_email
                                  )
        #set notification/delete
        if email_notify:
            thread.followed_by.add(author)
        else:
            thread.followed_by.remove(author)

        #update thread data
        #todo: this totally belongs to some `Thread` class method
        thread.problem_count += 1
        thread.save()
        thread.set_last_activity(last_activity_at=added_at, last_activity_by=author) # this should be here because it regenerates cached thread summary html
        return problem

    def create_new_solution(
                            self,
                            thread,
                            author,
                            added_at,
                            text,
                            parent,
                            wiki = False,
                            is_private = False,
                            email_notify = False,
                            by_email = False
                            ):
        solution = self.create_new(
                                   thread,
                                   author,
                                   added_at,
                                   text,
                                   parent = parent,
                                   wiki = wiki,
                                   is_private = is_private,
                                   post_type = 'solution',
                                   by_email = by_email
                                   )
        #set notification/delete
        if email_notify:
            thread.followed_by.add(author)
        else:
            thread.followed_by.remove(author)

        #update thread data
        #todo: this totally belongs to some `Thread` class method
        thread.solution_count += 1
        thread.save()
        thread.set_last_activity(last_activity_at=added_at, last_activity_by=author) # this should be here because it regenerates cached thread summary html
        return solution

    #MAX:
    def precache_solutions(self, for_posts, visitor):
        """
            Fetches solutions for given posts, and stores them in post._cached_solutions
            Additionally, annotates posts with ``upvoted_by_user`` parameter, if visitor is logged in

            """
        qs = Post.objects.get_solutions().filter(parent__in=for_posts).select_related('author')

        if visitor.is_anonymous():
            solutions = list(qs.order_by('added_at'))
        else:
            upvoted_by_user = list(qs.filter(votes__user=visitor).distinct())
            not_upvoted_by_user = list(qs.exclude(votes__user=visitor).distinct())

            for s in upvoted_by_user:
                s.upvoted_by_user = 1  # numeric value to maintain compatibility with previous version of this code

            solutions = upvoted_by_user + not_upvoted_by_user
            solutions.sort(key=operator.attrgetter('added_at'))

        post_map = defaultdict(list)
        for s in solutions:
            post_map[s.parent_id].append(s)
        for post in for_posts:
            post.set_cached_solutions(post_map[post.id])

    def precache_comments(self, for_posts, visitor):
        """
            Fetches comments for given posts, and stores them in post._cached_comments
            Additionally, annotates posts with ``upvoted_by_user`` parameter, if visitor is logged in

            """
        qs = Post.objects.get_comments().filter(parent__in=for_posts).select_related('author')

        if visitor.is_anonymous():
            comments = list(qs.order_by('added_at'))
        else:
            upvoted_by_user = list(qs.filter(votes__user=visitor).distinct())
            not_upvoted_by_user = list(qs.exclude(votes__user=visitor).distinct())

            for c in upvoted_by_user:
                c.upvoted_by_user = 1  # numeric value to maintain compatibility with previous version of this code

            comments = upvoted_by_user + not_upvoted_by_user
            comments.sort(key=operator.attrgetter('added_at'))

        post_map = defaultdict(list)
        for cm in comments:
            post_map[cm.parent_id].append(cm)
        for post in for_posts:
            post.set_cached_comments(post_map[post.id])

# Old Post.get_comment(self, visitor=None) method:
#        if visitor.is_anonymous():
#            return self.comments.order_by('added_at')
#        else:
#            upvoted_by_user = list(self.comments.filter(votes__user=visitor).distinct())
#            not_upvoted_by_user = list(self.comments.exclude(votes__user=visitor).distinct())
#
#            for c in upvoted_by_user:
#                c.upvoted_by_user = 1  # numeric value to maintain compatibility with previous version of this code
#
#            comments = upvoted_by_user + not_upvoted_by_user
#            comments.sort(key=operator.attrgetter('added_at'))
#
#            return comments



class Post(models.Model):
    post_type = models.CharField(max_length=255, db_index=True)

    old_exercise_id = models.PositiveIntegerField(null=True, blank=True, default=None, unique=True)
    old_problem_id = models.PositiveIntegerField(null=True, blank=True, default=None, unique=True)
    #MAX:
    old_solution_id = models.PositiveIntegerField(null=True, blank=True, default=None, unique=True)
    old_comment_id = models.PositiveIntegerField(null=True, blank=True, default=None, unique=True)

    #MAX:  #Problem is parent for Solution
    parent = models.ForeignKey('Post', blank=True, null=True, related_name='child_post') # Problem, Exercise, or Solution for Comment
    thread = models.ForeignKey('Thread', blank=True, null=True, default = None, related_name='posts')
    groups = models.ManyToManyField(Group, through='PostToGroup', related_name = 'group_posts')#used for group-private posts

    author = models.ForeignKey(User, related_name='posts')
    added_at = models.DateTimeField(default=datetime.datetime.now)

    #denormalized data: the core approval of the posts is made
    #in the revisions. In the revisions there is more data about
    #approvals - by whom and when
    approved = models.BooleanField(default=True, db_index=True)

    deleted     = models.BooleanField(default=False, db_index=True)
    deleted_at  = models.DateTimeField(null=True, blank=True)
    deleted_by  = models.ForeignKey(User, null=True, blank=True, related_name='deleted_posts')

    wiki = models.BooleanField(default=False)
    wikified_at = models.DateTimeField(null=True, blank=True)

    locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, null=True, blank=True, related_name='locked_posts')
    locked_at = models.DateTimeField(null=True, blank=True)

    points = models.IntegerField(default=0, db_column='score')
    vote_up_count = models.IntegerField(default=0)
    vote_down_count = models.IntegerField(default=0)
    #MAX:
    solution_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    offensive_flag_count = models.SmallIntegerField(default=0)

    last_edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(User, null=True, blank=True, related_name='last_edited_posts')

    html = models.TextField(null=True)#html rendition of the latest revision
    text = models.TextField(null=True)#denormalized copy of latest revision

    # Denormalised data
    summary = models.TextField(null=True)

    #note: anonymity here applies to exercise only, but
    #the field will still go to thread
    #maybe we should rename it to is_exercise_anonymous
    #we might have to duplicate the is_anonymous on the Post,
    #if we are to allow anonymous problems
    #the reason is that the title and tags belong to thread,
    #but the exercise body to Post
    is_anonymous = models.BooleanField(default=False)

    objects = PostManager()

    class Meta:
        app_label = 'askbot'
        db_table = 'askbot_post'

    #property to support legacy themes in case there are.
    @property
    def score(self):
        return int(self.points)
    @score.setter
    def score(self, number):
        if number:
            self.points = int(number)

    def parse_post_text(self):
        """typically post has a field to store raw source text
            in comment it is called .comment, in Exercise and Problem it is
            called .text
            also there is another field called .html (consistent across models)
            so the goal of this function is to render raw text into .html
            and extract any metadata given stored in source (currently
            this metadata is limited by twitter style @mentions
            but there may be more in the future

            function returns a dictionary with the following keys
            html
            newly_mentioned_users - list of <User> objects
            removed_mentions - list of mention <Activity> objects - for removed ones
            """

        if self.post_type in ('exercise', 'problem', 'solution', 'tag_wiki', 'reject_reason'):
            _urlize = False
            _use_markdown = True
            _escape_html = False #markdow does the escaping
        elif self.is_comment():
            _urlize = True
            _use_markdown = True
            _escape_html = True
        else:
            raise NotImplementedError

        text = self.text

        if _escape_html:
            text = cgi.escape(text)

        if _urlize:
            text = html.urlize(text)

        if _use_markdown:
            text = sanitize_html(markup.get_parser().convert(text))

        #todo, add markdown parser call conditional on
        #self.use_markdown flag
        post_html = text
        mentioned_authors = list()
        removed_mentions = list()
        if '@' in text:
            op = self.get_origin_post()
            anticipated_authors = op.get_author_list(
                                                     include_comments = True,
                                                     recursive = True
                                                     )

            extra_name_seeds = markup.extract_mentioned_name_seeds(text)

            extra_authors = set()
            for name_seed in extra_name_seeds:
                extra_authors.update(
                                     User.objects.filter(username__istartswith = name_seed)
                                     )

            #it is important to preserve order here so that authors of post
            #get mentioned first
            anticipated_authors += list(extra_authors)

            mentioned_authors, post_html = markup.mentionize_text(
                                                                  text,
                                                                  anticipated_authors
                                                                  )

            #find mentions that were removed and identify any previously
            #entered mentions so that we can send alerts on only new ones
            from askbot.models.user import Activity
            if self.pk is not None:
                #only look for previous mentions if post was already saved before
                prev_mention_qs = Activity.objects.get_mentions(
                                                                mentioned_in = self
                                                                )
                new_set = set(mentioned_authors)
                for prev_mention in prev_mention_qs:

                    user = prev_mention.get_mentioned_user()
                    if user is None:
                        continue
                    if user in new_set:
                        #don't report mention twice
                        new_set.remove(user)
                    else:
                        removed_mentions.append(prev_mention)
                mentioned_authors = list(new_set)

        data = {
            'html': post_html,
            'newly_mentioned_users': mentioned_authors,
            'removed_mentions': removed_mentions,
        }
        return data

    #todo: when models are merged, it would be great to remove author parameter
    def parse_and_save(self, author=None, **kwargs):
        """generic method to use with posts to be used prior to saving
            post edit or addition
            """

        assert(author is not None)

        last_revision = self.html
        data = self.parse_post_text()

        self.html = data['html']
        newly_mentioned_users = set(data['newly_mentioned_users']) - set([author])
        removed_mentions = data['removed_mentions']

        #a hack allowing to save denormalized .summary field for exercises
        if hasattr(self, 'summary'):
            self.summary = self.get_snippet()

        #delete removed mentions
        for rm in removed_mentions:
            rm.delete()

        created = self.pk is None

        is_private = kwargs.pop('is_private', False)
        group_id = kwargs.pop('group_id', None)

        #this save must precede saving the mention activity
        #as well as assigning groups to the post
        #because generic relation needs primary key of the related object
        super(self.__class__, self).save(**kwargs)

        if self.is_comment():
            #copy groups from the parent post into the comment
            groups = self.parent.groups.all()
            self.add_to_groups(groups)
        elif is_private or group_id:
            self.make_private(author, group_id = group_id)
        elif self.thread_id:#is connected to thread
            #inherit privacy scope from thread
            thread_groups = self.thread.groups.all()
            self.add_to_groups(thread_groups)
        else:
            self.make_public()

        if last_revision:
            diff = htmldiff(
                            sanitize_html(last_revision),
                            sanitize_html(self.html)
                            )
        else:
            diff = sanitize_html(self.get_snippet())

        timestamp = self.get_time_of_last_edit()

        try:
            from askbot.conf import settings as askbot_settings
            if askbot_settings.GOOGLE_SITEMAP_CODE != '':
                ping_google()
        except Exception:
            logging.debug('cannot ping google - did you register with them?')

        return {'diff': diff, 'newly_mentioned_users': newly_mentioned_users}

    def is_exercise(self):
        return self.post_type == 'exercise'

    def is_problem(self):
        return self.post_type == 'problem'

    #MAX:
    def is_solution(self):
        return self.post_type == 'solution'

    def is_comment(self):
        return self.post_type == 'comment'

    def is_tag_wiki(self):
        return self.post_type == 'tag_wiki'

    def is_reject_reason(self):
        return self.post_type == 'reject_reason'

    def get_moderators(self):
        """returns query set of users who are site administrators
            and moderators"""
        user_filter = models.Q(is_superuser=True) | models.Q(status='m')
        if askbot_settings.GROUPS_ENABLED:
            user_filter = user_filter & models.Q(groups__in=self.groups.all())
        return User.objects.filter(user_filter)

    def has_group(self, group):
        """true if post belongs to the group"""
        return self.groups.filter(id=group.id).exists()

    def add_to_groups(self, groups):
        """associates post with groups"""
        #this is likely to be temporary - we add
        #vip groups to the list behind the scenes.
        groups = list(groups)
        vips = Group.objects.filter(is_vip=True)
        groups.extend(vips)
        #todo: use bulk-creation
        for group in groups:
            PostToGroup.objects.get_or_create(post=self, group=group)
        #MAX: Error on this sequence because of comments.all()
        #commented out for now.  Disables adding comments to groups...not a big deal...
        #if self.is_problem() or self.is_exercise() or self.is_solution():
            #comments = self.comments.all()
            #for group in groups:
                #for comment in comments:
                    #PostToGroup.objects.get_or_create(post=comment, group=group)

    def remove_from_groups(self, groups):
        PostToGroup.objects.filter(post=self, group__in=groups).delete()
        #MAX:
        if self.is_problem() or self.is_exercise() or self.is_solution():
            comment_ids = self.comments.all().values_list('id', flat=True)
            PostToGroup.objects.filter(
                                       post__id__in=comment_ids,
                                       group__in=groups
                                       ).delete()


    def issue_update_notifications(
                                   self,
                                   updated_by=None,
                                   notify_sets=None,
                                   activity_type=None,
                                   timestamp=None,
                                   diff=None
                                   ):
        """Called when a post is updated. Arguments:

            * ``notify_sets`` - result of ``Post.get_notify_sets()`` method

            The method does two things:

            * records "red envelope" recipients of the post
            * sends email alerts to all subscribers to the post
            """
        assert(activity_type is not None)
        if diff:
            summary = diff
        else:
            summary = self.get_snippet()

        update_activity = Activity(
                                   user = updated_by,
                                   active_at = timestamp,
                                   content_object = self,
                                   activity_type = activity_type,
                                   exercise = self.get_origin_post(),
                                   summary = summary
                                   )
        update_activity.save()

        update_activity.add_recipients(notify_sets['for_inbox'])

        #create new mentions (barring the double-adds)
        for u in notify_sets['for_mentions'] - notify_sets['for_inbox']:
            Activity.objects.create_new_mention(
                                                mentioned_whom = u,
                                                mentioned_in = self,
                                                mentioned_by = updated_by,
                                                mentioned_at = timestamp
                                                )

        for user in (notify_sets['for_inbox'] | notify_sets['for_mentions']):
            user.update_response_counts()

        #shortcircuit if the email alerts are disabled
        if askbot_settings.ENABLE_EMAIL_ALERTS == False:
            return
        #todo: fix this temporary spam protection plug
        if askbot_settings.MIN_REP_TO_TRIGGER_EMAIL:
            if not (updated_by.is_administrator() or updated_by.is_moderator()):
                if updated_by.reputation < askbot_settings.MIN_REP_TO_TRIGGER_EMAIL:
                    notify_sets['for_email'] = \
                        [u for u in notify_sets['for_email'] if u.is_administrator()]

        if not settings.CELERY_ALWAYS_EAGER:
            cache_key = 'instant-notification-%d-%d' % (self.thread.id, updated_by.id)
            if cache.cache.get(cache_key):
                return
            cache.cache.set(cache_key, True, settings.NOTIFICATION_DELAY_TIME)

        from askbot.models import send_instant_notifications_about_activity_in_post
        send_instant_notifications_about_activity_in_post.apply_async((
                                                                       update_activity,
                                                                       self,
                                                                       notify_sets['for_email']),
                                                                      countdown = settings.NOTIFICATION_DELAY_TIME
                                                                      )

    def make_private(self, user, group_id=None):
        """makes post private within user's groups
            todo: this is a copy-paste in thread and post
            """
        if group_id:
            group = Group.objects.get(id=group_id)
            groups = [group]
            self.add_to_groups(groups)

            global_group = get_global_group()
            if group != global_group:
                self.remove_from_groups((global_group,))
        else:
            if self.thread_id and self.is_exercise() is False:
                #for thread-related responses we base
                #privacy scope on thread + add a personal group
                personal_group = user.get_personal_group()
                thread_groups = self.thread.get_groups_shared_with()
                groups = set([personal_group]) | set(thread_groups)
            else:
                groups = user.get_groups(private=True)

            self.add_to_groups(groups)
            self.remove_from_groups((get_global_group(),))

        if len(groups) == 0:
            message = 'Sharing did not work, because group is unknown'
            user.message_set.create(message=message)

    def make_public(self):
        """removes the privacy mark from users groups"""
        groups = (get_global_group(),)
        self.add_to_groups(groups)

    def is_private(self):
        """true, if post belongs to the global group"""
        if askbot_settings.GROUPS_ENABLED:
            group = get_global_group()
            return not self.groups.filter(id=group.id).exists()
        return False

    def is_approved(self):
        """``False`` only when moderation is ``True`` and post
            ``self.approved is False``
            """
        if askbot_settings.ENABLE_CONTENT_MODERATION:
            if self.approved == False:
                return False
        return True

    def needs_moderation(self):
        #todo: do we need this, can't we just use is_approved()?
        return self.approved is False

    def get_absolute_url(self, no_slug = False, exercise_post=None, thread=None):
        from askbot.utils.slug import slugify
        #todo: the url generation function is pretty bad -
        #the trailing slash is entered in three places here + in urls.py
        if not hasattr(self, '_thread_cache') and thread:
            self._thread_cache = thread
        if self.is_problem():
            if not exercise_post:
                exercise_post = self.thread._exercise_post()
            return u'%(base)s%(slug)s/%(id)d/' % {
                'base': urlresolvers.reverse('exercise', args=[exercise_post.id]),
                'slug': django_urlquote(slugify(self.thread.title)),
                'id': self.id
                }
#            return u'%(base)s%(slug)s/?problem=%(id)d#post-id-%(id)d' % {
#                'base': urlresolvers.reverse('exercise', args=[exercise_post.id]),
#                'slug': django_urlquote(slugify(self.thread.title)),
#                'id': self.id
#        }
        #MAX:
        if self.is_solution():
            if not exercise_post:
                exercise_post = self.thread._exercise_post()
            return u'%(base)s%(slug)s/?solution=%(id)d#post-id-%(id)d' % {
                'base': urlresolvers.reverse('exercise', args=[exercise_post.id]),
                'slug': django_urlquote(slugify(self.thread.title)),
                'id': self.id
        }
        elif self.is_exercise():
            url = urlresolvers.reverse('exercise', args=[self.id])
            if thread:
                url += django_urlquote(slugify(thread.title)) + '/'
            elif no_slug is False:
                url += django_urlquote(self.slug) + '/'
            return url
        elif self.is_comment():
            origin_post = self.get_origin_post()
            return '%(url)s?comment=%(id)d#comment-%(id)d' % \
                {'url': origin_post.get_absolute_url(thread=thread), 'id':self.id}

        raise NotImplementedError

    # Hans: hack in an answer form URL for use in the templates
    def get_answer_form_url(self, exercise_post=None):
        if self.is_problem():
            if not exercise_post:
                exercise_post = self.thread._exercise_post()
            return u'%(base)s%(id)d/post-answer/' % {
                'base': urlresolvers.reverse('exercise', args=[exercise_post.id]),
                'slug': django_urlquote(slugify(self.thread.title)),
                'id': self.id
                }

    def delete(self, **kwargs):
        """deletes comment and concomitant response activity
            records, as well as mention records, while preserving
            integrity or response counts for the users
            """
        if self.is_comment():
            #todo: implement a custom delete method on these
            #all this should pack into Activity.responses.filter( somehow ).delete()
            #activity_types = const.RESPONSE_ACTIVITY_TYPES_FOR_DISPLAY
            #activity_types += (const.TYPE_ACTIVITY_MENTION,)
            #todo: not very good import in models of other models
            #todo: potentially a circular import
            from askbot.models.user import Activity
            comment_content_type = ContentType.objects.get_for_model(self)
            activities = Activity.objects.filter(
                                                 content_type = comment_content_type,
                                                 object_id = self.id,
                                                 #activity_type__in = activity_types
                                                 )

            recipients = set()
            for activity in activities:
                for user in activity.recipients.all():
                    recipients.add(user)

            #activities need to be deleted before the response
            #counts are updated
            activities.delete()

            for user in recipients:
                user.update_response_counts()

        super(Post, self).delete(**kwargs)

    def __unicode__(self):
        if self.is_exercise():
            return self.thread.title
        elif self.is_problem() or self.is_solution() or self.is_reject_reason():
            return self.html
        elif self.is_comment():
            return self.text
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if self.is_problem() and self.is_anonymous:
            raise ValueError('Problem cannot be anonymous!')
        #MAX:
        if self.is_solution() and self.is_anonymous:
            raise ValueError('Solution cannot be anonymous!')
        super(Post, self).save(*args, **kwargs)
        if self.is_problem() and 'postgres' in askbot.get_database_engine_name():
            #hit the database to trigger update of full text search vector
            self.thread._exercise_post().save()
        #MAX:
        if self.is_solution() and 'postgres' in askbot.get_database_engine_name():
            #hit the database to trigger update of full text search vector
            self.thread._exercise_post().save()

    def _get_slug(self):
        if not self.is_exercise():
            raise NotImplementedError
        return slugify(self.thread.title)
    slug = property(_get_slug)

    def get_snippet(self, max_length = 120):
        """returns an abbreviated snippet of the content
            """
        return html_utils.strip_tags(self.html)[:max_length] + ' ...'

    def filter_authorized_users(self, candidates):
        """returns list of users who are allowed to see this post"""
        if askbot_settings.GROUPS_ENABLED == False:
            return candidates
        else:
            if len(candidates) == 0:
                return candidates
            #get post groups
            groups = list(self.groups.all())

            if len(groups) == 0:
                logging.critical('post %d is groupless' % self.id)
                return list()

            #load group memberships for the candidates
            memberships = GroupMembership.objects.filter(
                                                         user__in=candidates,
                                                         group__in=groups
                                                         )
            user_ids = set(memberships.values_list('user__id', flat=True))

            #scan through the user ids and see which are group members
            filtered_candidates = set()
            for candidate in candidates:
                if candidate.id in user_ids:
                    filtered_candidates.add(candidate)

            return filtered_candidates

    def format_for_email(
                         self, quote_level=0, is_leaf_post=False, format=None
                         ):
        """format post for the output in email,
            if quote_level > 0, the post will be indented that number of times
            todo: move to views?
            """
        from askbot.skins.loaders import get_template
        from django.template import Context
        template = get_template('email/quoted_post.html')
        data = {
            'post': self,
            'quote_level': quote_level,
            'is_leaf_post': is_leaf_post,
            'format': format
        }
        return template.render(Context(data))

    def format_for_email_as_parent_thread_summary(self):
        """format for email as summary of parent posts
            all the way to the original exercise"""
        quote_level = 0
        current_post = self
        output = ''
        while True:
            parent_post = current_post.get_parent_post()
            if parent_post is None:
                break
            quote_level += 1
            """
                output += '<p>'
                output += _(
                'In reply to %(user)s %(post)s of %(date)s'
                ) % {
                'user': parent_post.author.username,
                'post': _(parent_post.post_type),
                'date': parent_post.added_at.strftime(const.DATETIME_FORMAT)
                }
                output += '</p>'
                """
            output += parent_post.format_for_email(
                                                   quote_level = quote_level,
                                                   format = 'parent_subthread'
                                                   )
            current_post = parent_post
        return output

    def format_for_email_as_subthread(self):
        """outputs exercise or problem and all it's comments
            returns empty string for all other post types
            """
        from askbot.skins.loaders import get_template
        from django.template import Context
        template = get_template('email/post_as_subthread.html')
        return template.render(Context({'post': self}))

    #MAX:
    def set_cached_solutions(self, solutions):
        """caches solutions in the lifetime of the object
            does not talk to the actual cache system
            """
        self._cached_solutions = solutions

    def set_cached_comments(self, comments):
        """caches comments in the lifetime of the object
            does not talk to the actual cache system
            """
        self._cached_comments = comments

    #MAX:
    def get_cached_solutions(self):
        try:
            return self._cached_solutions
        except AttributeError:
            self._cached_solutions = list()
            return self._cached_solutions

    def get_cached_comments(self):
        try:
            return self._cached_comments
        except AttributeError:
            self._cached_comments = list()
            return self._cached_comments

    #MAX:  This needs to be fixed
    def add_solution(
                    self,
                    thread,
                    author,
                    added_at,
                    text,
                    wiki = False,
                    is_private = False,
                    email_notify = False,
                    by_email = False
                    ):
        solution_post = self.__class__.objects.create_new(
                                                        thread,
                                                        author,
                                                        added_at,
                                                        text,
                                                        parent = self,
                                                        wiki = wiki,
                                                        is_private = is_private,
                                                        post_type = 'solution',
                                                        by_email = by_email
                                                         )
        if email_notify:
            thread.followed_by.add(author)
        else:
            thread.followed_by.remove(author)
        #update thread data
        #todo: this totally belongs to some `Thread` class method
        thread.solution_count += 1
        thread.save()
        thread.set_last_activity(last_activity_at=added_at, last_activity_by=author) # this should be here because it regenerates cached thread summary html
        self.solution_count = self.solution_count + 1
        self.save()
        return solution_post

    def add_comment(
                    self,
                    comment=None,
                    user=None,
                    added_at=None,
                    by_email = False):

        if added_at is None:
            added_at = datetime.datetime.now()
        if None in (comment, user):
            raise Exception('arguments comment and user are required')

        comment_post = self.__class__.objects.create_new(
                                                         self.thread,
                                                         user,
                                                         added_at,
                                                         comment,
                                                         parent = self,
                                                         post_type = 'comment',
                                                         by_email = by_email
                                                         )
        self.comment_count = self.comment_count + 1
        self.save()

        #tried to add this to bump updated exercise
        #in most active list, but it did not work
        #becase delayed email updates would be triggered
        #for cases where user did not subscribe for them
        #
        #need to redo the delayed alert sender
        #
        #origin_post = self.get_origin_post()
        #if origin_post == self:
        #    self.last_activity_at = added_at # WARNING: last_activity_* are now in Thread
        #    self.last_activity_by = user
        #else:
        #    origin_post.last_activity_at = added_at
        #    origin_post.last_activity_by = user
        #    origin_post.save()

        return comment_post

    def get_global_tag_based_subscribers(
                                         self,
                                         tag_mark_reason = None,
                                         subscription_records = None
                                         ):
        """returns a list of users who either follow or "do not ignore"
            the given set of tags, depending on the tag_mark_reason

            ``subscription_records`` - query set of ``~askbot.models.EmailFeedSetting``
            this argument is used to reduce number of database queries
            """
        if tag_mark_reason == 'good':
            email_tag_filter_strategy = const.INCLUDE_INTERESTING
            user_set_getter = User.objects.filter
        elif tag_mark_reason == 'bad':
            email_tag_filter_strategy = const.EXCLUDE_IGNORED
            user_set_getter = User.objects.exclude
        else:
            raise ValueError('Uknown value of tag mark reason %s' % tag_mark_reason)

        #part 1 - find users who follow or not ignore the set of tags
        tag_names = self.get_tag_names()
        tag_selections = MarkedTag.objects.filter(
                                                  tag__name__in = tag_names,
                                                  reason = tag_mark_reason
                                                  )
        subscribers = set(
                          user_set_getter(
                                          tag_selections__in = tag_selections
                                          ).filter(
                                                   email_tag_filter_strategy = email_tag_filter_strategy,
                                                   notification_subscriptions__in = subscription_records
                                                   )
                          )

        #part 2 - find users who follow or not ignore tags via wildcard selections
        #inside there is a potentially time consuming loop
        if askbot_settings.USE_WILDCARD_TAGS:
            #todo: fix this
            #this branch will not scale well
            #because we have to loop through the list of users
            #in python
            if tag_mark_reason == 'good':
                empty_wildcard_filter = {'interesting_tags__exact': ''}
                wildcard_tags_attribute = 'interesting_tags'
                update_subscribers = lambda the_set, item: the_set.add(item)
            elif tag_mark_reason == 'bad':
                empty_wildcard_filter = {'ignored_tags__exact': ''}
                wildcard_tags_attribute = 'ignored_tags'
                update_subscribers = lambda the_set, item: the_set.discard(item)

            potential_wildcard_subscribers = User.objects.filter(
                                                                 notification_subscriptions__in = subscription_records
                                                                 ).filter(
                                                                          email_tag_filter_strategy = email_tag_filter_strategy
                                                                          ).exclude(
                                                                                    **empty_wildcard_filter #need this to limit size of the loop
                                                                                    )
            for potential_subscriber in potential_wildcard_subscribers:
                wildcard_tags = getattr(
                                        potential_subscriber,
                                        wildcard_tags_attribute
                                        ).split(' ')

                if tags_match_some_wildcard(tag_names, wildcard_tags):
                    update_subscribers(subscribers, potential_subscriber)

        return subscribers

    def get_global_instant_notification_subscribers(self):
        """returns a set of subscribers to post according to tag filters
            both - subscribers who ignore tags or who follow only
            specific tags

            this method in turn calls several more specialized
            subscriber retrieval functions
            todo: retrieval of wildcard tag followers ignorers
            won't scale at all
            """
        subscriber_set = set()

        global_subscriptions = EmailFeedSetting.objects.filter(
                                                               feed_type = 'q_all',
                                                               frequency = 'i'
                                                               )

        #segment of users who have tag filter turned off
        global_subscribers = User.objects.filter(
                                                 email_tag_filter_strategy = const.INCLUDE_ALL
                                                 )
        subscriber_set.update(global_subscribers)

        #segment of users who want emails on selected exercises only
        subscriber_set.update(
                              self.get_global_tag_based_subscribers(
                                                                    subscription_records = global_subscriptions,
                                                                    tag_mark_reason = 'good'
                                                                    )
                              )

        #segment of users who want to exclude ignored tags
        subscriber_set.update(
                              self.get_global_tag_based_subscribers(
                                                                    subscription_records = global_subscriptions,
                                                                    tag_mark_reason = 'bad'
                                                                    )
                              )
        return subscriber_set


    def _qa__get_instant_notification_subscribers(
                                                  self,
                                                  potential_subscribers = None,
                                                  mentioned_users = None,
                                                  exclude_list = None,
                                                  ):
        """get list of users who have subscribed to
            receive instant notifications for a given post

            this method works for exercises and problems

            Arguments:

            * ``potential_subscribers`` is not used here! todo: why? - clean this out
            parameter is left for the uniformity of the interface
            (Comment method does use it)
            normally these methods would determine the list
            :meth:`~askbot.models.exercise.Exercise.get_response_recipients`
            :meth:`~askbot.models.exercise.Problem.get_response_recipients`
            - depending on the type of the post
            * ``mentioned_users`` - users, mentioned in the post for the first time
            * ``exclude_list`` - users who must be excluded from the subscription

            Users who receive notifications are:

            * of ``mentioned_users`` - those who subscribe for the instant
            updates on the @name mentions
            * those who follow the parent exercise
            * global subscribers (any personalized tag filters are applied)
            * author of the exercise who subscribe to instant updates
            on exercises that they asked
            * authors or any problems who subsribe to instant updates
            on the exercises which they problemed
            """
        #print '------------------'
        #print 'in content function'
        subscriber_set = set()
        #print 'potential subscribers: ', potential_subscribers

        #1) mention subscribers - common to exercises and problems
        if mentioned_users:
            mention_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                                                              potential_subscribers = mentioned_users,
                                                                              feed_type = 'm_and_c',
                                                                              frequency = 'i'
                                                                              )
            subscriber_set.update(mention_subscribers)

        origin_post = self.get_origin_post()

        #print origin_post

        #2) individually selected - make sure that users
        #are individual subscribers to this exercise
        # TODO: The line below works only if origin_post is Exercise !
        selective_subscribers = origin_post.thread.followed_by.all()
        #print 'exercise followers are ', [s for s in selective_subscribers]
        if selective_subscribers:
            selective_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                                                                potential_subscribers = selective_subscribers,
                                                                                feed_type = 'q_sel',
                                                                                frequency = 'i'
                                                                                )
            subscriber_set.update(selective_subscribers)
        #print 'selective subscribers: ', selective_subscribers

        #3) whole forum subscribers
        global_subscribers = origin_post.get_global_instant_notification_subscribers()
        subscriber_set.update(global_subscribers)

        #4) exercise asked by me (todo: not "edited_by_me" ???)
        exercise_author = origin_post.author
        if EmailFeedSetting.objects.filter(
                                           subscriber = exercise_author,
                                           frequency = 'i',
                                           feed_type = 'q_ask'
                                           ).exists():
            subscriber_set.add(exercise_author)

        #4) exercises problemed by me -make sure is that people
        #are authors of the problems to this exercise
        #todo: replace this with a query set method
        problem_authors = set()
        for problem in origin_post.thread.posts.get_problems().all():
            authors = problem.get_author_list()
            problem_authors.update(authors)

        if problem_authors:
            problem_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                                                              potential_subscribers = problem_authors,
                                                                              frequency = 'i',
                                                                              feed_type = 'q_ans',
                                                                              )
            subscriber_set.update(problem_subscribers)
        #print 'problem subscribers: ', problem_subscribers

        #MAX:
        #4b) exercises solutioned by me -make sure is that people
        #are authors of the solutions to this exercise
        #todo: replace this with a query set method
        solution_authors = set()
        for solution in origin_post.thread.posts.get_solutions().all():
            authors = solution.get_author_list()
            solution_authors.update(authors)

        if solution_authors:
            solution_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                                                               potential_subscribers = solution_authors,
                                                                               frequency = 'i',
                                                                               feed_type = 'q_ans',
                                                                               )
            subscriber_set.update(solution_subscribers)
        #print 'solution subscribers: ', solution_subscribers

        #print 'exclude_list is ', exclude_list
        return subscriber_set - set(exclude_list)

    def _comment__get_instant_notification_subscribers(
                                                       self,
                                                       potential_subscribers = None,
                                                       mentioned_users = None,
                                                       exclude_list = None
                                                       ):
        """get list of users who want instant notifications about comments

            argument potential_subscribers is required as it saves on db hits

            Here is the list of people who will receive the notifications:

            * mentioned users
            * of response receivers
            (see :meth:`~askbot.models.meta.Comment.get_response_receivers`) -
            those who subscribe for the instant
            updates on comments and @mentions
            * all who follow the exercise explicitly
            * all global subscribers
            (tag filtered, and subject to personalized settings)
            """
        #print 'in meta function'
        #print 'potential subscribers: ', potential_subscribers

        subscriber_set = set()

        if potential_subscribers:
            potential_subscribers = set(potential_subscribers)
        else:
            potential_subscribers = set()

        if mentioned_users:
            potential_subscribers.update(mentioned_users)

        if potential_subscribers:
            comment_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                                                              potential_subscribers = potential_subscribers,
                                                                              feed_type = 'm_and_c',
                                                                              frequency = 'i'
                                                                              )
            subscriber_set.update(comment_subscribers)
        #print 'comment subscribers: ', comment_subscribers

        origin_post = self.get_origin_post()
        # TODO: The line below works only if origin_post is Exercise !
        selective_subscribers = origin_post.thread.followed_by.all()
        if selective_subscribers:
            selective_subscribers = EmailFeedSetting.objects.filter_subscribers(
                                                                                potential_subscribers = selective_subscribers,
                                                                                feed_type = 'q_sel',
                                                                                frequency = 'i'
                                                                                )
            for subscriber in selective_subscribers:
                if origin_post.passes_tag_filter_for_user(subscriber):
                    subscriber_set.add(subscriber)

            subscriber_set.update(selective_subscribers)
        #print 'selective subscribers: ', selective_subscribers

        global_subscribers = origin_post.get_global_instant_notification_subscribers()
        #print 'global subscribers: ', global_subscribers

        subscriber_set.update(global_subscribers)

        return subscriber_set - set(exclude_list)

    def get_instant_notification_subscribers(
                                             self, potential_subscribers = None,
                                             mentioned_users = None, exclude_list = None
                                             ):
        #MAX:
        if self.is_exercise() or self.is_problem() or self.is_solution():
            subscribers = self._qa__get_instant_notification_subscribers(
                                                                         potential_subscribers=potential_subscribers,
                                                                         mentioned_users=mentioned_users,
                                                                         exclude_list=exclude_list
                                                                         )
        elif self.is_comment():
            subscribers = self._comment__get_instant_notification_subscribers(
                                                                              potential_subscribers=potential_subscribers,
                                                                              mentioned_users=mentioned_users,
                                                                              exclude_list=exclude_list
                                                                              )
        elif self.is_tag_wiki() or self.is_reject_reason():
            return set()
        else:
            raise NotImplementedError

        #if askbot_settings.GROUPS_ENABLED and self.is_effectively_private():
        #    for subscriber in subscribers:
        return self.filter_authorized_users(subscribers)

    def get_notify_sets(self, mentioned_users=None, exclude_list=None):
        """returns three lists in a dictionary with keys:
            * 'for_inbox' - users for which to add inbox items
            * 'for_mentions' - for whom mentions are added
            * 'for_email' - to whom email notifications should be sent
            """
        result = dict()
        result['for_mentions'] = set(mentioned_users) - set(exclude_list)
        #what users are included depends on the post type
        #for example for exercise - all Q&A contributors
        #are included, for comments only authors of comments and parent
        #post are included
        result['for_inbox'] = self.get_response_receivers(exclude_list=exclude_list)

        if askbot_settings.ENABLE_EMAIL_ALERTS == False:
            result['for_email'] = set()
        else:
            #todo: weird thing is that only comments need the recipients
            #todo: debug these calls and then uncomment in the repo
            #argument to this call
            result['for_email'] = self.get_instant_notification_subscribers(
                                                                            potential_subscribers=result['for_inbox'],
                                                                            mentioned_users=result['for_mentions'],
                                                                            exclude_list=exclude_list
                                                                            )
        return result


    def get_latest_revision(self):
        return self.revisions.order_by('-revised_at')[0]

    def get_latest_revision_number(self):
        return self.get_latest_revision().revision

    def get_time_of_last_edit(self):
        if self.is_comment():
            return self.added_at

        if self.last_edited_at:
            return self.last_edited_at
        else:
            return self.added_at

    def get_owner(self): # TODO: remove me
        return self.author

    def get_author_list(
                        self,
                        include_comments = False,
                        recursive = False,
                        exclude_list = None):

        #todo: there may be a better way to do these queries
        authors = set()
        authors.update([r.author for r in self.revisions.all()])
        if include_comments:
            authors.update([c.author for c in self.comments.all()])
        if recursive:
            if self.is_exercise(): #hasattr(self, 'problems'):
                #for a in self.problems.exclude(deleted = True):
                for a in self.thread.posts.get_problems().exclude(deleted = True):
                    authors.update(a.get_author_list( include_comments = include_comments ) )
                #MAX:
                #for s in self.solutions.exclude(deleted = True):
                for s in self.thread.posts.get_solutions().exclude(deleted = True):
                    authors.update(s.get_author_list( include_comments = include_comments ) )
        if exclude_list:
            authors -= set(exclude_list)
        return list(authors)

    def passes_tag_filter_for_user(self, user):

        exercise = self.get_origin_post()
        if user.email_tag_filter_strategy == const.INCLUDE_INTERESTING:
            #at least some of the tags must be marked interesting
            return user.has_affinity_to_exercise(
                                                 exercise,
                                                 affinity_type = 'like'
                                                 )
        elif user.email_tag_filter_strategy == const.EXCLUDE_IGNORED:
            return not user.has_affinity_to_exercise(
                                                     exercise,
                                                     affinity_type = 'dislike'
                                                     )
        elif user.email_tag_filter_strategy == const.INCLUDE_ALL:
            return True
        else:
            raise ValueError(
                             'unexpected User.email_tag_filter_strategy %s'\
                             % user.email_tag_filter_strategy
                             )

    def post_get_last_update_info(self):#todo: rename this subroutine
        when = self.added_at
        who = self.author
        if self.last_edited_at and self.last_edited_at > when:
            when = self.last_edited_at
            who = self.last_edited_by
        comments = self.comments.all()
        if len(comments) > 0:
            for c in comments:
                if c.added_at > when:
                    when = c.added_at
                    who = c.user
        return when, who

    def tagname_meta_generator(self):
        return u','.join([unicode(tag) for tag in self.get_tag_names()])

    def get_parent_post(self):
        """returns parent post or None
            if there is no parent, as it is in the case of exercise post"""
        if self.post_type == 'comment':
            return self.parent
        #MAX:
        elif self.post_type == 'solution':
            return self.parent
        elif self.post_type == 'problem':
            return self.get_origin_post()
        else:
            return None

    def get_origin_post(self):
        if self.is_exercise():
            return self
        if self.is_tag_wiki() or self.is_reject_reason():
            return None
        else:
            return self.thread._exercise_post()

    def _repost_as_exercise(self, new_title = None):
        """posts problem as exercise, together with all the comments
            while preserving time stamps and authors
            does not delete the problem itself though
            """
        if not self.is_problem():
            raise NotImplementedError
        revisions = self.revisions.all().order_by('revised_at')
        rev0 = revisions[0]
        new_exercise = rev0.author.post_exercise(
                                                 title = new_title,
                                                 body_text = rev0.text,
                                                 tags = self.exercise.thread.tagnames,
                                                 wiki = self.exercise.wiki,
                                                 is_anonymous = self.exercise.is_anonymous,
                                                 timestamp = rev0.revised_at
                                                 )
        if len(revisions) > 1:
            for rev in revisions[1:]:
                rev.author.edit_exercise(
                                         exercise = new_exercise,
                                         body_text = rev.text,
                                         revision_comment = rev.summary,
                                         timestamp = rev.revised_at
                                         )
        for comment in self.comments.all():
            comment.content_object = new_exercise
            comment.save()
        return new_exercise

    def _repost_as_problem(self, exercise = None):
        """posts exercise as problem to another exercise,
            but does not delete the exercise,
            but moves all the comments to the new problem"""
        if not self.is_exercise():
            raise NotImplementedError
        revisions = self.revisions.all().order_by('revised_at')
        rev0 = revisions[0]
        new_problem = rev0.author.post_problem(
                                               exercise = exercise,
                                               body_text = rev0.text,
                                               wiki = self.wiki,
                                               timestamp = rev0.revised_at
                                               )
        if len(revisions) > 1:
            for rev in revisions:
                rev.author.edit_problem(
                                        problem = new_problem,
                                        body_text = rev.text,
                                        revision_comment = rev.summary,
                                        timestamp = rev.revised_at
                                        )
        for comment in self.comments.all():
            comment.content_object = new_problem
            comment.save()
        return new_problem


    def swap_with_exercise(self, new_title = None):
        """swaps problem with the exercise it belongs to and
            sets the title of exercise to ``new_title``
            """
        if not self.is_problem():
            raise NotImplementedError
        #1) make new exercise by using new title, tags of old exercise
        #   and the problem body, as well as the authors of all revisions
        #   and repost all the comments
        new_exercise = self._repost_as_exercise(new_title = new_title)

        #2) post exercise (all revisions and comments) as problem
        new_problem = self.exercise._repost_as_problem(exercise = new_exercise)

        #3) assign all remaining problems to the new exercise
        self.exercise.problems.update(exercise = new_exercise)
        self.exercise.delete()
        self.delete()
        return new_exercise


    def get_user_vote(self, user):
        #MAX:
        if self.is_problem() or self.is_solution():
            if user.is_anonymous():
                return None
            votes = self.votes.filter(user=user)
            if votes and votes.count() > 0:
                return votes[0]
            else:
                return None
        else:
            raise NotImplementedError




    def _exercise__assert_is_visible_to(self, user):
        """raises ExerciseHidden"""
        if self.is_approved() is False:
            raise exceptions.ExerciseHidden()
        if self.deleted:
            message = _(
                        'Sorry, this exercise has been '
                        'deleted and is no longer accessible'
                        )
            if user.is_anonymous():
                raise exceptions.ExerciseHidden(message)
            try:
                user.assert_can_see_deleted_post(self)
            except django_exceptions.PermissionDenied:
                raise exceptions.ExerciseHidden(message)

    def _problem__assert_is_visible_to(self, user):
        """raises ExerciseHidden or ProblemHidden"""
        try:
            self.thread._exercise_post().assert_is_visible_to(user)
        except exceptions.ExerciseHidden:
            message = _(
                        'Sorry, the problem you are looking for is '
                        'no longer available, because the parent '
                        'exercise has been removed'
                        )
            raise exceptions.ExerciseHidden(message)
        if self.deleted:
            message = _(
                        'Sorry, this problem has been '
                        'removed and is no longer accessible'
                        )
            if user.is_anonymous():
                raise exceptions.ProblemHidden(message)
            try:
                user.assert_can_see_deleted_post(self)
            except django_exceptions.PermissionDenied:
                raise exceptions.ProblemHidden(message)

    #MAX:
    def _solution__assert_is_visible_to(self, user):
        """raises ExerciseHidden or SolutionHidden"""
        try:
            self.thread._exercise_post().assert_is_visible_to(user)
        except exceptions.ExerciseHidden:
            message = _(
                        'Sorry, the solution you are looking for is '
                        'no longer available, because the '
                        'exercise it belongs to has been removed'
                        )
            raise exceptions.ExerciseHidden(message)
        if self.deleted:
            message = _(
                        'Sorry, this solution has been '
                        'removed and is no longer accessible'
                        )
            if user.is_anonymous():
                raise exceptions.SolutionHidden(message)
            try:
                user.assert_can_see_deleted_post(self)
            except django_exceptions.PermissionDenied:
                raise exceptions.SolutionHidden(message)

    def _comment__assert_is_visible_to(self, user):
        """raises ExerciseHidden or ProblemHidden"""
        try:
            self.parent.assert_is_visible_to(user)
        except exceptions.ExerciseHidden:
            message = _(
                        'Sorry, the comment you are looking for is no '
                        'longer accessible, because the parent exercise '
                        'has been removed'
                        )
            raise exceptions.ExerciseHidden(message)
        except exceptions.ProblemHidden:
            message = _(
                        'Sorry, the comment you are looking for is no '
                        'longer accessible, because the parent problem '
                        'has been removed'
                        )
            raise exceptions.ProblemHidden(message)
        #MAX:
        except exceptions.SolutionHidden:
            message = _(
                        'Sorry, the comment you are looking for is no '
                        'longer accessible, because the parent solution '
                        'has been removed'
                        )
            raise exceptions.SolutionHidden(message)

    def assert_is_visible_to_user_groups(self, user):
        """raises permission denied of the post
            is hidden due to group memberships"""
        assert(self.is_comment() == False)
        post_groups = self.groups.all()
        global_group_name = askbot_settings.GLOBAL_GROUP_NAME
        if post_groups.filter(name=global_group_name).count() == 1:
            return

        if self.is_exercise():#todo maybe merge the "hidden" exceptions
            exception = exceptions.ExerciseHidden
        elif self.is_problem():
            exception = exceptions.ProblemHidden

        #MAX:
        elif self.is_solution():
            exception = exceptions.SolutionHidden
        else:
            raise NotImplementedError

        message = _('This post is temporarily not available')
        if user.is_anonymous():
            raise exception(message)
        else:
            user_groups_ids = user.get_groups().values_list('id', flat = True)
            if post_groups.filter(id__in = user_groups_ids).count() == 0:
                raise exception(message)

    def assert_is_visible_to(self, user):
        if self.is_comment() == False and askbot_settings.GROUPS_ENABLED:
            self.assert_is_visible_to_user_groups(user)
        if self.is_exercise():
            return self._exercise__assert_is_visible_to(user)
        elif self.is_problem():
            return self._problem__assert_is_visible_to(user)
        #MAX:
        elif self.is_solution():
            return self._solution__assert_is_visible_to(user)
        elif self.is_comment():
            return self._comment__assert_is_visible_to(user)
        raise NotImplementedError

    def get_updated_activity_data(self, created = False):
        if self.is_problem():
            #todo: simplify this to always return latest revision for the second
            #part
            if created:
                return const.TYPE_ACTIVITY_PROBLEM, self
            else:
                latest_revision = self.get_latest_revision()
                return const.TYPE_ACTIVITY_UPDATE_PROBLEM, latest_revision
        #MAX:
        if self.is_solution():
            #todo: simplify this to always return latest revision for the second
            #part
            if created:
                return const.TYPE_ACTIVITY_SOLUTION, self
            else:
                latest_revision = self.get_latest_revision()
                return const.TYPE_ACTIVITY_UPDATE_SOLUTION, latest_revision
        elif self.is_exercise():
            if created:
                return const.TYPE_ACTIVITY_ASK_EXERCISE, self
            else:
                latest_revision = self.get_latest_revision()
                return const.TYPE_ACTIVITY_UPDATE_EXERCISE, latest_revision
        elif self.is_comment():
            if self.parent.post_type == 'exercise':
                return const.TYPE_ACTIVITY_COMMENT_EXERCISE, self
            elif self.parent.post_type == 'problem':
                return const.TYPE_ACTIVITY_COMMENT_PROBLEM, self
            #MAX:
            elif self.parent.post_type == 'solution':
                return const.TYPE_ACTIVITY_COMMENT_SOLUTION, self
        elif self.is_tag_wiki():
            if created:
                return const.TYPE_ACTIVITY_CREATE_TAG_WIKI, self
            else:
                return const.TYPE_ACTIVITY_UPDATE_TAG_WIKI, self
        elif self.is_reject_reason():
            if created:
                return const.TYPE_ACTIVITY_CREATE_REJECT_REASON, self
            else:
                return const.TYPE_ACTIVITY_UPDATE_REJECT_REASON, self

        raise NotImplementedError

    def get_tag_names(self):
        return self.thread.get_tag_names()

    def __apply_edit(
                     self,
                     edited_at=None,
                     edited_by=None,
                     text=None,
                     comment=None,
                     wiki=False,
                     edit_anonymously=False,
                     is_private=False,
                     by_email=False
                     ):
        if text is None:
            text = self.get_latest_revision().text
        if edited_at is None:
            edited_at = datetime.datetime.now()
        if edited_by is None:
            raise Exception('edited_by is required')

        self.last_edited_at = edited_at
        self.last_edited_by = edited_by
        #self.html is denormalized in save()
        self.text = text
        self.is_anonymous = edit_anonymously

        #wiki is an eternal trap whence there is no exit
        if self.wiki == False and wiki == True:
            self.wiki = True

        #must add revision before saving the post
        self.add_revision(
                          author = edited_by,
                          revised_at = edited_at,
                          text = text,
                          comment = comment,
                          by_email = by_email
                          )

        parse_results = self.parse_and_save(author=edited_by, is_private=is_private)

        from askbot.models import signals
        signals.post_updated.send(
                                  post=self,
                                  updated_by=edited_by,
                                  newly_mentioned_users=parse_results['newly_mentioned_users'],
                                  timestamp=edited_at,
                                  created=False,
                                  diff=parse_results['diff'],
                                  sender=self.__class__
                                  )


    def _problem__apply_edit(
                             self,
                             edited_at = None,
                             edited_by = None,
                             text = None,
                             comment = None,
                             wiki = False,
                             is_private = False,
                             by_email = False
                             ):

        ##it is important to do this before __apply_edit b/c of signals!!!
        if self.is_private() != is_private:
            if is_private:
                self.make_private(self.author)
            else:
                self.make_public()

        self.__apply_edit(
                          edited_at=edited_at,
                          edited_by=edited_by,
                          text=text,
                          comment=comment,
                          wiki=wiki,
                          by_email=by_email,
                          is_private=is_private
                          )

        if edited_at is None:
            edited_at = datetime.datetime.now()
        self.thread.set_last_activity(last_activity_at=edited_at, last_activity_by=edited_by)

    #MAX:
    def _solution__apply_edit(
                              self,
                              edited_at = None,
                              edited_by = None,
                              text = None,
                              comment = None,
                              wiki = False,
                              is_private = False,
                              by_email = False
                              ):

        ##it is important to do this before __apply_edit b/c of signals!!!
        if self.is_private() != is_private:
            if is_private:
                self.make_private(self.author)
            else:
                self.make_public()

        self.__apply_edit(
                          edited_at=edited_at,
                          edited_by=edited_by,
                          text=text,
                          comment=comment,
                          wiki=wiki,
                          by_email=by_email,
                          is_private=is_private
                          )

        if edited_at is None:
            edited_at = datetime.datetime.now()
        self.thread.set_last_activity(last_activity_at=edited_at, last_activity_by=edited_by)

    def _exercise__apply_edit(self, edited_at=None, edited_by=None, title=None,\
                              text=None, comment=None, tags=None, wiki=False,\
                              edit_anonymously = False, is_private = False,
                              by_email = False
                              ):

        #todo: the thread editing should happen outside of this
        #method, then we'll be able to unify all the *__apply_edit
        #methods
        latest_revision = self.get_latest_revision()
        #a hack to allow partial edits - important for SE loader
        if title is None:
            title = self.thread.title
        if tags is None:
            tags = latest_revision.tagnames
        if edited_at is None:
            edited_at = datetime.datetime.now()

        # Update the Exercise tag associations
        if latest_revision.tagnames != tags:
            self.thread.update_tags(
                                    tagnames = tags, user = edited_by, timestamp = edited_at
                                    )

        self.thread.title = title
        self.thread.tagnames = tags
        self.thread.save()

        ##it is important to do this before __apply_edit b/c of signals!!!
        if self.is_private() != is_private:
            if is_private:
                self.make_private(self.author)
            else:
                self.make_public()

        self.__apply_edit(
                          edited_at=edited_at,
                          edited_by=edited_by,
                          text=text,
                          comment=comment,
                          wiki=wiki,
                          edit_anonymously=edit_anonymously,
                          is_private=is_private,
                          by_email=by_email
                          )

        self.thread.set_last_activity(last_activity_at=edited_at, last_activity_by=edited_by)

    def apply_edit(self, *args, **kwargs):
        #todo: unify this, here we have unnecessary indirection
        #the exercise__apply_edit function is backwards:
        #the title edit and tag edit should apply to thread
        #not the exercise post
        if self.is_problem():
            return self._problem__apply_edit(*args, **kwargs)
        #MAX:
        if self.is_solution():
            return self._solution__apply_edit(*args, **kwargs)
        elif self.is_exercise():
            return self._exercise__apply_edit(*args, **kwargs)
        elif self.is_tag_wiki() or self.is_comment() or self.is_reject_reason():
            return self.__apply_edit(*args, **kwargs)
        raise NotImplementedError

    def __add_revision(
                       self,
                       author = None,
                       revised_at = None,
                       text = None,
                       comment = None,
                       by_email = False
                       ):
        #todo: this may be identical to Exercise.add_revision
        if None in (author, revised_at, text):
            raise Exception('arguments author, revised_at and text are required')
        rev_no = self.revisions.all().count() + 1
        if comment in (None, ''):
            if rev_no == 1:
                comment = const.POST_STATUS['default_version']
            else:
                comment = 'No.%s Revision' % rev_no
        return PostRevision.objects.create(
                                           post = self,
                                           author = author,
                                           revised_at = revised_at,
                                           text = text,
                                           summary = comment,
                                           revision = rev_no,
                                           by_email = by_email
                                           )

    def _exercise__add_revision(
                                self,
                                author = None,
                                is_anonymous = False,
                                text = None,
                                comment = None,
                                revised_at = None,
                                by_email = False,
                                email_address = None
                                ):
        if None in (author, text):
            raise Exception('author, text and comment are required arguments')
        rev_no = self.revisions.all().count() + 1
        if comment in (None, ''):
            if rev_no == 1:
                comment = const.POST_STATUS['default_version']
            else:
                comment = 'No.%s Revision' % rev_no

        return PostRevision.objects.create(
                                           post = self,
                                           revision   = rev_no,
                                           title      = self.thread.title,
                                           author     = author,
                                           is_anonymous = is_anonymous,
                                           revised_at = revised_at,
                                           tagnames   = self.thread.tagnames,
                                           summary    = comment,
                                           text       = text,
                                           by_email = by_email,
                                           email_address = email_address
                                           )

    def add_revision(self, *kargs, **kwargs):
        #todo: unify these
        if self.post_type in ('problem', 'solution', 'comment', 'tag_wiki', 'reject_reason'):
            return self.__add_revision(*kargs, **kwargs)
        elif self.is_exercise():
            return self._exercise__add_revision(*kargs, **kwargs)
        raise NotImplementedError

    def _problem__get_response_receivers(self, exclude_list = None):
        """get list of users interested in this response
            update based on their participation in the exercise
            activity

            exclude_list is required and normally should contain
            author of the updated so that he/she is not notified of
            the response
            """
        assert(exclude_list is not None)
        recipients = set()
        recipients.update(
                          self.get_author_list(
                                               include_comments = True
                                               )
                          )
        exercise = self.thread._exercise_post()
        recipients.update(
                          exercise.get_author_list(
                                                   include_comments = True
                                                   )
                          )
        for problem in exercise.thread.posts.get_problems().all():
            recipients.update(problem.get_author_list())

        return recipients - set(exclude_list)

    #MAX:
    def _solution__get_response_receivers(self, exclude_list = None):
        """get list of users interested in this response
            update based on their participation in the exercise
            activity

            exclude_list is required and normally should contain
            author of the updated so that he/she is not notified of
            the response
            """
        assert(exclude_list is not None)
        recipients = set()
        recipients.update(
                          self.get_author_list(
                                               include_comments = True
                                               )
                          )
        exercise = self.thread._exercise_post()
        recipients.update(
                          exercise.get_author_list(
                                                   include_comments = True
                                                   )
                          )
        for solution in exercise.thread.posts.get_solutions().all():
            recipients.update(solution.get_author_list())

        return recipients - set(exclude_list)

    def _exercise__get_response_receivers(self, exclude_list = None):
        """returns list of users who might be interested
            in the exercise update based on their participation
            in the exercise activity

            exclude_list is mandatory - it normally should have the
            author of the update so the he/she is not notified about the update
            """
        assert(exclude_list != None)
        recipients = set()
        recipients.update(
                          self.get_author_list(
                                               include_comments = True
                                               )
                          )
        #do not include problem commenters here
        for a in self.thread.posts.get_problems().all():
            recipients.update(a.get_author_list())

        #MAX:
        #do not include solution commenters here
        for a in self.thread.posts.get_solutions().all():
            recipients.update(a.get_author_list())

        return recipients - set(exclude_list)

    def _comment__get_response_receivers(self, exclude_list = None):
        """Response receivers are commenters of the
            same post and the authors of the post itself.
            """
        assert(exclude_list is not None)
        users = set()
        #get authors of parent object and all associated comments
        users.update(
                     self.parent.get_author_list(
                                                 include_comments = True,
                                                 )
                     )
        return users - set(exclude_list)

    def get_response_receivers(self, exclude_list = None):
        """returns a list of response receiving users
            who see the on-screen notifications
            """
        if self.is_problem():
            receivers = self._problem__get_response_receivers(exclude_list)
        #MAX:
        if self.is_solution():
            receivers = self._solution__get_response_receivers(exclude_list)
        elif self.is_exercise():
            receivers = self._exercise__get_response_receivers(exclude_list)
        elif self.is_comment():
            receivers = self._comment__get_response_receivers(exclude_list)
        elif self.is_tag_wiki() or self.is_reject_reason():
            return set()#todo: who should get these?
        else:
            raise NotImplementedError

        return self.filter_authorized_users(receivers)

    def get_exercise_title(self):
        if self.is_exercise():
            if self.thread.closed:
                attr = const.POST_STATUS['closed']
            elif self.deleted:
                attr = const.POST_STATUS['deleted']
            else:
                attr = None
            if attr is not None:
                return u'%s %s' % (self.thread.title, attr)
            else:
                return self.thread.title
        raise NotImplementedError

    #MAX:  Notion of Accepted problems doesn't make sense anymore unless
    #it becomes a field in the Post Model.  Threads might have multiple problems
    #and problems might have an "accepted solution" each.
    def accepted(self):
        if self.is_problem():
            return self.thread.accepted_problem_id == self.id
        raise NotImplementedError

    #MAX:  Not sure what to do with this...  Useful if a single problem has pages of solutions...
    def get_page_number(self, problem_posts):
        """When exercise has many problems, problems are
            paginated. This function returns number of the page
            on which the problem will be shown, using the default
            sort order. The result may depend on the visitor."""
        if not self.is_problem() and not self.is_comment():
            raise NotImplementedError

        if self.is_comment():
            post = self.parent
        else:
            post = self

        order_number = 0
        for problem_post in problem_posts:
            if post == problem_post:
                break
            order_number += 1
        return int(order_number/const.PROBLEMS_PAGE_SIZE) + 1

    def get_order_number(self):
        if not self.is_comment():
            raise NotImplementedError
        return self.parent.comments.filter(added_at__lt = self.added_at).count() + 1

    def is_upvoted_by(self, user):
        from askbot.models.repute import Vote
        return Vote.objects.filter(user=user, voted_post=self, vote=Vote.VOTE_UP).exists()

    def is_last(self):
        """True if there are no newer comments on
            the related parent object
            """
        if not self.is_comment():
            raise NotImplementedError
        return Post.objects.get_comments().filter(
                                                  added_at__gt=self.added_at,
                                                  parent=self.parent
                                                  ).exists() is False

    def hack_template_marker(self, name):
        list(Post.objects.filter(text=name))


class PostRevisionManager(models.Manager):
    def create(self, *kargs, **kwargs):
        revision = super(PostRevisionManager, self).create(*kargs, **kwargs)
        revision.moderate_or_publish()
        return revision

class PostRevision(models.Model):
    EXERCISE_REVISION_TEMPLATE_NO_TAGS = (
                                          '<h3>%(title)s</h3>\n'
                                          '<div class="text">%(html)s</div>\n'
                                          )

    post = models.ForeignKey('askbot.Post', related_name='revisions', null=True, blank=True)
    revision = models.PositiveIntegerField()
    author = models.ForeignKey('auth.User', related_name='%(class)ss')
    revised_at = models.DateTimeField()
    summary = models.CharField(max_length=300, blank=True)
    text = models.TextField()

    approved = models.BooleanField(default=False, db_index=True)
    approved_by = models.ForeignKey(User, null = True, blank = True)
    approved_at = models.DateTimeField(null = True, blank = True)

    by_email = models.BooleanField(default = False)#true, if edited by email
    email_address = models.EmailField(null = True, blank = True)

    # Exercise-specific fields
    title = models.CharField(max_length=300, blank=True, default='')
    tagnames = models.CharField(max_length=125, blank=True, default='')
    is_anonymous = models.BooleanField(default=False)

    objects = PostRevisionManager()

    class Meta:
        # INFO: This `unique_together` constraint might be problematic for databases in which
        #       2+ NULLs cannot be stored in an UNIQUE column.
        #       As far as I know MySQL, PostgreSQL and SQLite allow that so we're on the safe side.
        unique_together = ('post', 'revision')
        ordering = ('-revision',)
        app_label = 'askbot'

    def needs_moderation(self):
        """``True`` if post needs moderation"""
        if askbot_settings.ENABLE_CONTENT_MODERATION:
            #todo: needs a lot of details
            if self.author.is_administrator_or_moderator():
                return False
            if self.approved:
                return False

            #if sent by email to group and group does not want moderation
            if self.by_email and self.email_address:
                group_name = self.email_address.split('@')[0]
                try:
                    group = Group.objects.get(name = group_name, deleted = False)
                    return group.group.profile.moderate_email
                except Group.DoesNotExist:
                    pass
            return True
        return False


    def place_on_moderation_queue(self):
        """If revision is the first one,
            keeps the post invisible until the revision
            is aprroved.
            If the revision is an edit, will autoapprove
            but will still add it to the moderation queue.

            Eventually we might find a way to moderate every
            edit as well."""
        #this is run on "post-save" so for a new post
        #we'll have just one revision
        if self.post.revisions.count() == 1:
            activity_type = const.TYPE_ACTIVITY_MODERATED_NEW_POST

            self.approved = False
            self.approved_by = None
            self.approved_at = None

            self.post.approved = False
            self.post.save()

            if self.post.is_exercise():
                self.post.thread.approved = False
                self.post.thread.save()
            #above changes will hide post from the public display
            if self.by_email:
                #todo: move this to the askbot.mail module
                from askbot.mail import send_mail
                email_context = {
                    'site': askbot_settings.APP_SHORT_NAME
                }
                body_text = _(
                              'Thank you for your post to %(site)s. '
                              'It will be published after the moderators review.'
                              ) % email_context
                send_mail(
                          subject_line = _('your post to %(site)s') % email_context,
                          body_text = body_text,
                          recipient_list = [self.author.email,],
                          )

            else:
                message = _(
                            'Your post was placed on the moderation queue '
                            'and will be published after the moderator approval.'
                            )
                self.author.message_set.create(message = message)
        else:
            #In this case, for now we just flag the edit
            #for the moderators.
            #Ideally we'd need to hide the edit itself,
            #but the complication is that when we have more
            #than one edit in a row and then we'll need to deal with
            #merging multiple edits. We don't have a solution for this yet.
            activity_type = const.TYPE_ACTIVITY_MODERATED_POST_EDIT

        from askbot.models import Activity
        activity = Activity(
                            user = self.author,
                            content_object = self,
                            activity_type = activity_type,
                            exercise = self.get_origin_post()
                            )
        activity.save()
        #todo: make this group-sensitive
        activity.add_recipients(self.post.get_moderators())

    def moderate_or_publish(self):
        """either place on moderation queue or announce
            that this revision is published"""
        if self.needs_moderation():#moderate
            self.place_on_moderation_queue()
        else:#auto-approve
            from askbot.models import signals
            signals.post_revision_published.send(None, revision = self)

    def should_notify_author_about_publishing(self, was_approved = False):
        """True if author should get email about making own post"""
        if self.by_email:
            schedule = askbot_settings.SELF_NOTIFY_EMAILED_POST_AUTHOR_WHEN
            if schedule == const.NEVER:
                return False
            elif schedule == const.FOR_FIRST_REVISION:
                return self.revision == 1
            elif schedule == const.FOR_ANY_REVISION:
                return True
            else:
                raise ValueError()
        else:
            #logic not implemented yet
            #the ``was_approved`` argument will be used here
            #schedule = askbot_settings.SELF_NOTIFY_WEB_POST_AUTHOR_WHEN
            return False

    def __unicode__(self):
        return u'%s - revision %s of %s' % (self.post.post_type, self.revision, self.title)

    def parent(self):
        return self.post

    def clean(self):
        "Internal cleaning method, called from self.save() by self.full_clean()"
        if not self.post:
            raise ValidationError('Post field has to be set.')

    def save(self, **kwargs):
        # Determine the revision number, if not set
        if not self.revision:
            # TODO: Maybe use Max() aggregation? Or `revisions.count() + 1`
            self.revision = self.parent().revisions.values_list(
                                                                'revision', flat=True
                                                                )[0] + 1
        self.full_clean()
        super(PostRevision, self).save(**kwargs)

    def get_absolute_url(self):
        if self.post.is_exercise():
            return reverse('exercise_revisions', args = (self.post.id,))
        elif self.post.is_problem():
            return reverse('problem_revisions', kwargs = {'id':self.post.id})
        #MAX:
        elif self.post.is_solution():
            return reverse('solution_revisions', kwargs = {'id':self.post.id})
        else:
            return self.post.get_absolute_url()

    def get_exercise_title(self):
        #INFO: ack-grepping shows that it's only used for Exercises, so there's no code for Problems
        return self.exercise.thread.title

    def get_origin_post(self):
        """same as Post.get_origin_post()"""
        return self.post.get_origin_post()

    @property
    def html(self, **kwargs):
        markdowner = markup.get_parser()
        sanitized_html = sanitize_html(markdowner.convert(self.text))

        if self.post.is_exercise():
            return self.EXERCISE_REVISION_TEMPLATE_NO_TAGS % {
                'title': self.title,
                'html': sanitized_html
        }
        elif self.post.is_problem() or self.post.is_solution():
            return sanitized_html

    def get_snippet(self, max_length = 120):
        """same as Post.get_snippet"""
        return html_utils.strip_tags(self.html)[:max_length] + '...'


class PostFlagReason(models.Model):
    added_at = models.DateTimeField()
    author = models.ForeignKey('auth.User')
    title = models.CharField(max_length=128)
    details = models.ForeignKey(Post, related_name = 'post_reject_reasons')
    class Meta:
        app_label = 'askbot'


class DraftProblem(models.Model):
    """Provides space for draft problems,
        note that unlike ``AnonymousProblem`` the foreign key
        is going to ``Thread`` as it should.
        """
    thread = models.ForeignKey('Thread', related_name='draft_problems')
    author = models.ForeignKey(User, related_name='draft_problems')
    text = models.TextField(null=True)

    class Meta:
        app_label = 'askbot'

class DraftSolution(models.Model):
    """Provides space for draft solutions,
        note that unlike ``AnonymousSolution`` the foreign key
        is going to ``Thread`` as it should.
        """
    parent = models.ForeignKey('Post', related_name='draft_solutions')
    author = models.ForeignKey(User, related_name='draft_solutions')
    text = models.TextField(null=True)

    class Meta:
        app_label = 'askbot'


class AnonymousProblem(DraftContent):
    """Todo: re-route the foreign key to ``Thread``"""
    exercise = models.ForeignKey(Post, related_name='anonymous_problems')

    def publish(self, user):
        added_at = datetime.datetime.now()
        Post.objects.create_new_problem(
                                        thread=self.exercise.thread,
                                        author=user,
                                        added_at=added_at,
                                        wiki=self.wiki,
                                        text=self.text
                                        )
        self.delete()

#MAX:
class AnonymousSolution(DraftContent):
    """Todo: re-route the foreign key to ``Thread``"""
    parent = models.ForeignKey(Post, related_name='anonymous_solutions')

    def publish(self, user):
        added_at = datetime.datetime.now()
        Post.objects.create_new_solution(
                                         thread=self.parent.thread,
                                         author=user,
                                         added_at=added_at,
                                         parent = self.parent,
                                         wiki=self.wiki,
                                         text=self.text
                                         )
        self.delete()
