import datetime
import operator
import re

from django.conf import settings as django_settings
from django.db import models
from django.contrib.auth.models import User
from django.core import cache  # import cache, not from cache import cache, to be able to monkey-patch cache.cache in test cases
from django.core.urlresolvers import reverse
from django.utils.hashcompat import md5_constructor
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext

import askbot
from askbot.conf import settings as askbot_settings
from askbot import mail
from askbot.mail import messages
from askbot.models.tag import Tag
from askbot.models.tag import get_groups
from askbot.models.tag import get_global_group
from askbot.models.tag import get_tags_by_names
from askbot.models.tag import filter_accepted_tags, filter_suggested_tags
from askbot.models.tag import delete_tags, separate_unused_tags
from askbot.models.base import DraftContent, BaseQuerySetManager
from askbot.models.tag import Tag, get_groups
from askbot.models.post import Post, PostRevision
from askbot.models.post import PostToGroup
from askbot.models.user import Group, PERSONAL_GROUP_NAME_PREFIX
from askbot.models import signals
from askbot import const
from askbot.utils.lists import LazyList
from askbot.utils import mysql
from askbot.utils.slug import slugify
from askbot.skins.loaders import get_template #jinja2 template loading enviroment
from askbot.search.state_manager import DummySearchState

class ThreadQuerySet(models.query.QuerySet):
    def get_visible(self, user):
        """filters out threads not belonging to the user groups"""
        if user.is_authenticated():
            groups = user.get_groups()
        else:
            groups = [get_global_group()]
        return self.filter(groups__in=groups).distinct()

class ThreadManager(BaseQuerySetManager):

    def get_query_set(self):
        return ThreadQuerySet(self.model)

    def get_tag_summary_from_threads(self, threads):
        """returns a humanized string containing up to
        five most frequently used
        unique tags coming from the ``threads``.
        Variable ``threads`` is an iterable of
        :class:`~askbot.models.Thread` model objects.

        This is not implemented yet as a query set method,
        because it is used on a list.
        """
        # TODO: In Python 2.6 there is collections.Counter() thing which would be very useful here
        # TODO: In Python 2.5 there is `defaultdict` which already would be an improvement
        tag_counts = dict()
        for thread in threads:
            for tag_name in thread.get_tag_names():
                if tag_name in tag_counts:
                    tag_counts[tag_name] += 1
                else:
                    tag_counts[tag_name] = 1
        tag_list = tag_counts.keys()
        tag_list.sort(key=lambda t: tag_counts[t], reverse=True)

        #note that double quote placement is important here
        if len(tag_list) == 1:
            last_topic = '"'
        elif len(tag_list) <= 5:
            last_topic = _('" and "%s"') % tag_list.pop()
        else:
            tag_list = tag_list[:5]
            last_topic = _('" and more')

        return '"' + '", "'.join(tag_list) + last_topic

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def create_new(
                self,
                title,
                author,
                added_at,
                wiki,
                text,
                tagnames = None,
                is_anonymous = False,
                is_private = False,
                group_id = None,
                by_email = False,
                email_address = None
            ):
        """creates new thread"""
        # TODO: Some of this code will go to Post.objects.create_new

        thread = super(
            ThreadManager,
            self
        ).create(
            title=title,
            tagnames=tagnames,
            last_activity_at=added_at,
            last_activity_by=author
        )

        #todo: code below looks like ``Post.objects.create_new()``
        exercise = Post(
            post_type='exercise',
            thread=thread,
            author = author,
            added_at = added_at,
            wiki = wiki,
            is_anonymous = is_anonymous,
            #html field is denormalized in .save() call
            text = text,
            #summary field is denormalized in .save() call
        )
        if exercise.wiki:
            #DATED COMMENT
            #todo: this is confusing - last_edited_at field
            #is used as an indicator whether exercise has been edited
            #but in principle, post creation should count as edit as well
            exercise.last_edited_by = exercise.author
            exercise.last_edited_at = added_at
            exercise.wikified_at = added_at

        #this is kind of bad, but we save assign privacy groups to posts and thread
        #this call is rather heavy, we should split into several functions
        parse_results = exercise.parse_and_save(author=author, is_private=is_private)

        revision = exercise.add_revision(
            author=author,
            is_anonymous=is_anonymous,
            text=text,
            comment=const.POST_STATUS['default_version'],
            revised_at=added_at,
            by_email=by_email,
            email_address=email_address
        )

        author_group = author.get_personal_group()
        thread.add_to_groups([author_group], visibility=ThreadToGroup.SHOW_PUBLISHED_RESPONSES)
        exercise.add_to_groups([author_group])

        if is_private or group_id:#add groups to thread and exercise
            thread.make_private(author, group_id=group_id)
        else:
            thread.make_public()

        # INFO: Exercise has to be saved before update_tags() is called
        thread.update_tags(tagnames=tagnames, user=author, timestamp=added_at)

        #todo: this is handled in signal because models for posts
        #are too spread out
        signals.post_updated.send(
            post=exercise,
            updated_by=author,
            newly_mentioned_users=parse_results['newly_mentioned_users'],
            timestamp=added_at,
            created=True,
            diff=parse_results['diff'],
            sender=exercise.__class__
        )

        return thread

    def get_for_query(self, search_query, qs=None):
        """returns a query set of exercises,
        matching the full text query
        """
        if django_settings.ENABLE_HAYSTACK_SEARCH:
            from askbot.search.haystack import AskbotSearchQuerySet
            hs_qs = AskbotSearchQuerySet().filter(content=search_query)
            return hs_qs.get_django_queryset()
        else:
            if not qs:
                qs = self.all()
    #        if getattr(settings, 'USE_SPHINX_SEARCH', False):
    #            matching_exercises = Exercise.sphinx_search.query(search_query)
    #            exercise_ids = [q.id for q in matching_exercises]
    #            return qs.filter(posts__post_type='exercise', posts__deleted=False, posts__self_exercise_id__in=exercise_ids)
            if askbot.get_database_engine_name().endswith('mysql') \
                and mysql.supports_full_text_search():
                return qs.filter(
                    models.Q(title__search = search_query) |
                    models.Q(tagnames__search = search_query) |
                    models.Q(posts__deleted=False, posts__text__search = search_query)
                )
            elif 'postgresql_psycopg2' in askbot.get_database_engine_name():
                from askbot.search import postgresql
                return postgresql.run_full_text_search(qs, search_query)
            else:
                return qs.filter(
                    models.Q(title__icontains=search_query) |
                    models.Q(tagnames__icontains=search_query) |
                    models.Q(posts__deleted=False, posts__text__icontains = search_query)
                )

    #MAX: added support for without_solutions
    def run_advanced_search(self, request_user, search_state):  # TODO: !! review, fix, and write tests for this
        """
        all parameters are guaranteed to be clean
        however may not relate to database - in that case
        a relvant filter will be silently dropped

        """
        from askbot.conf import settings as askbot_settings # Avoid circular import

        # TODO: add a possibility to see deleted exercises
        qs = self.filter(
                posts__post_type='exercise',
                posts__deleted=False,
            ) # (***) brings `askbot_post` into the SQL query, see the ordering section below

        if askbot_settings.ENABLE_CONTENT_MODERATION:
            qs = qs.filter(approved = True)

        #if groups feature is enabled, filter out threads
        #that are private in groups to which current user does not belong
        if askbot_settings.GROUPS_ENABLED:
            #get group names
            qs = qs.get_visible(user=request_user)


        #run text search while excluding any modifier in the search string
        #like #tag [title: something] @user
        if search_state.stripped_query:
            qs = self.get_for_query(search_query=search_state.stripped_query, qs=qs)

        #we run other things after full text search, because
        #FTS may break the chain of the query set calls,
        #since it might go into an external asset, like Solr

        #search in titles, if necessary
        if search_state.query_title:
            qs = qs.filter(title__icontains = search_state.query_title)

        #search user names if @user is added to search string
        #or if user name exists in the search state
        if search_state.query_users:
            query_users = User.objects.filter(username__in=search_state.query_users)
            if query_users:
                qs = qs.filter(
                    posts__post_type='exercise',
                    posts__author__in=query_users
                ) # TODO: unify with search_state.author ?

        #unified tags - is list of tags taken from the tag selection
        #plus any tags added to the query string with #tag or [tag:something]
        #syntax.
        #run tag search in addition to these unified tags
        meta_data = {}
        tags = search_state.unified_tags()
        if len(tags) > 0:

            if askbot_settings.TAG_SEARCH_INPUT_ENABLED:
                #todo: this may be gone or disabled per option
                #"tag_search_box_enabled"
                existing_tags = set()
                non_existing_tags = set()
                #we're using a one-by-one tag retreival, b/c
                #we want to take advantage of case-insensitive search indexes
                #in postgresql, plus it is most likely that there will be
                #only one or two search tags anyway
                for tag in tags:
                    try:
                        tag_record = Tag.objects.get(name__iexact=tag)
                        existing_tags.add(tag_record.name)
                    except Tag.DoesNotExist:
                        non_existing_tags.add(tag)

                meta_data['non_existing_tags'] = list(non_existing_tags)
                tags = existing_tags
            else:
                meta_data['non_existing_tags'] = list()

            #construct filter for the tag search
            for tag in tags:
                qs = qs.filter(tags__name=tag) # Tags or AND-ed here, not OR-ed (i.e. we fetch only threads with all tags)
        else:
            meta_data['non_existing_tags'] = list()

        if search_state.scope == 'without_problem':
            qs = qs.filter(closed = False) # Do not show closed exercises in without problem section
            if askbot_settings.EXERCISE_WITHOUT_PROBLEM_MEANING == 'NO_PROBLEMS':
                # todo: this will introduce a problem if there are private problems
                # which are counted here
                qs = qs.filter(problem_count=0) # TODO: expand for different meanings of this
            elif askbot_settings.EXERCISE_WITHOUT_PROBLEM_MEANING == 'NO_ACCEPTED_PROBLEMS':
                qs = qs.filter(accepted_problem__isnull=True)
            elif askbot_settings.EXERCISE_WITHOUT_PROBLEM_MEANING == 'NO_UPVOTED_PROBLEMS':
                raise NotImplementedError()
            else:
                raise Exception('EXERCISE_WITHOUT_PROBLEM_MEANING setting is wrong')
        
        #MAX:  Right now this defines without_solution as strictly meaning an exercise has solution_count = 0
        #(zero solved problems).  Could be adjusted to allow for live settings and more flexiblity as
        #in the without_problem section above or vice versa...
        elif search_state.scope == 'without_solution':
            qs = qs.filter(closed = False) # Do not show closed exercises in without solution section
            qs = qs.filter(solution_count=0)
        
        elif search_state.scope == 'favorite':
            favorite_filter = models.Q(favorited_by=request_user)
            if 'followit' in django_settings.INSTALLED_APPS:
                followed_users = request_user.get_followed_users()
                favorite_filter |= models.Q(posts__post_type__in=('exercise', 'problem', 'solution'), posts__author__in=followed_users)
            qs = qs.filter(favorite_filter)

        #user contributed exercises & problems
        if search_state.author:
            try:
                # TODO: maybe support selection by multiple authors
                u = User.objects.get(id=int(search_state.author))
            except User.DoesNotExist:
                meta_data['author_name'] = None
            else:
                qs = qs.filter(posts__post_type__in=('exercise', 'problem', 'solution'), posts__author=u, posts__deleted=False)
                meta_data['author_name'] = u.username

        #get users tag filters
        if request_user and request_user.is_authenticated():
            #mark exercises tagged with interesting tags
            #a kind of fancy annotation, would be nice to avoid it
            interesting_tags = Tag.objects.filter(
                user_selections__user = request_user,
                user_selections__reason = 'good'
            )
            ignored_tags = Tag.objects.filter(
                user_selections__user = request_user,
                user_selections__reason = 'bad'
            )
            subscribed_tags = Tag.objects.none()
            if askbot_settings.SUBSCRIBED_TAG_SELECTOR_ENABLED:
                subscribed_tags = Tag.objects.filter(
                    user_selections__user = request_user,
                    user_selections__reason = 'subscribed'
                )
                meta_data['subscribed_tag_names'] = [tag.name for tag in subscribed_tags]

            meta_data['interesting_tag_names'] = [tag.name for tag in interesting_tags]
            meta_data['ignored_tag_names'] = [tag.name for tag in ignored_tags]

            if request_user.display_tag_filter_strategy == const.INCLUDE_INTERESTING and (interesting_tags or request_user.has_interesting_wildcard_tags()):
                #filter by interesting tags only
                interesting_tag_filter = models.Q(tags__in=interesting_tags)
                if request_user.has_interesting_wildcard_tags():
                    interesting_wildcards = request_user.interesting_tags.split()
                    extra_interesting_tags = Tag.objects.get_by_wildcards(interesting_wildcards)
                    interesting_tag_filter |= models.Q(tags__in=extra_interesting_tags)
                qs = qs.filter(interesting_tag_filter)

            # get the list of interesting and ignored tags (interesting_tag_names, ignored_tag_names) = (None, None)
            if request_user.display_tag_filter_strategy == const.EXCLUDE_IGNORED and (ignored_tags or request_user.has_ignored_wildcard_tags()):
                #exclude ignored tags if the user wants to
                qs = qs.exclude(tags__in=ignored_tags)
                if request_user.has_ignored_wildcard_tags():
                    ignored_wildcards = request_user.ignored_tags.split()
                    extra_ignored_tags = Tag.objects.get_by_wildcards(ignored_wildcards)
                    qs = qs.exclude(tags__in = extra_ignored_tags)

            if request_user.display_tag_filter_strategy == const.INCLUDE_SUBSCRIBED \
                and subscribed_tags:
                qs = qs.filter(tags__in = subscribed_tags)

            if askbot_settings.USE_WILDCARD_TAGS:
                meta_data['interesting_tag_names'].extend(request_user.interesting_tags.split())
                meta_data['ignored_tag_names'].extend(request_user.ignored_tags.split())

        EXERCISE_ORDER_BY_MAP = {
            'age-desc': '-added_at',
            'age-asc': 'added_at',
            'activity-desc': '-last_activity_at',
            'activity-asc': 'last_activity_at',
            'problems-desc': '-problem_count',
            'problems-asc': 'problem_count',
            #MAX:
            'solutions-desc': '-solution_count',
            'solutions-asc': 'solution_count',
            'votes-desc': '-points',
            'votes-asc': 'points',

            'relevance-desc': '-relevance', # special Postgresql-specific ordering, 'relevance' quaso-column is added by get_for_query()
        }

        orderby = EXERCISE_ORDER_BY_MAP[search_state.sort]

        if not (
            getattr(django_settings, 'ENABLE_HAYSTACK_SEARCH', False) \
            and orderby=='-relevance'
        ):
            #FIXME: this does not produces the very same results as postgres.
            qs = qs.extra(order_by=[orderby])


        # HACK: We add 'ordering_key' column as an alias and order by it, because when distict() is used,
        #       qs.extra(order_by=[orderby,]) is lost if only `orderby` column is from askbot_post!
        #       Removing distinct() from the queryset fixes the problem, but we have to use it here.
        # UPDATE: Apparently we don't need distinct, the query don't duplicate Thread rows!
        # qs = qs.extra(select={'ordering_key': orderby.lstrip('-')}, order_by=['-ordering_key' if orderby.startswith('-') else 'ordering_key'])
        # qs = qs.distinct()

        qs = qs.only('id', 'title', 'view_count', 'problem_count', 'solution_count', 'last_activity_at', 'last_activity_by', 'closed', 'tagnames', 'accepted_problem')

        #print qs.query

        return qs.distinct(), meta_data

    def precache_view_data_hack(self, threads):
        # TODO: Re-enable this when we have a good test cases to verify that it works properly.
        #
        #       E.g.: - make sure that not precaching give threads never increase # of db queries for the main page
        #             - make sure that it really works, i.e. stuff for non-cached threads is fetched properly
        # Precache data only for non-cached threads - only those will be rendered
        #threads = [thread for thread in threads if not thread.summary_html_cached()]

        thread_ids = [obj.id for obj in threads]
        page_exercises = Post.objects.filter(
            post_type='exercise', thread__id__in = thread_ids
        ).only(# pick only the used fields
            'id', 'thread', 'points', 'is_anonymous',
            'summary', 'post_type', 'deleted'
        )
        page_exercise_map = {}
        for pq in page_exercises:
            page_exercise_map[pq.thread_id] = pq
        for thread in threads:
            thread._exercise_cache = page_exercise_map[thread.id]

        last_activity_by_users = User.objects.filter(id__in=[obj.last_activity_by_id for obj in threads])\
                                    .only('id', 'username', 'country', 'show_country')
        user_map = {}
        for la_user in last_activity_by_users:
            user_map[la_user.id] = la_user
        for thread in threads:
            thread._last_activity_by_cache = user_map[thread.last_activity_by_id]

    
    #todo: this function is similar to get_response_receivers - profile this function against the other one
    def get_thread_contributors(self, thread_list):
        """Returns query set of Thread contributors"""
        #INFO: Evaluate this query to avoid subquery in the subsequent query below (At least MySQL can be awfully slow on subqueries)
        #MAX: Includes solution contributors
        u_id = list(Post.objects.filter(post_type__in=('exercise', 'problem', 'solution'), thread__in=thread_list).values_list('author', flat=True))

        #todo: this does not belong gere - here we select users with real faces
        #first and limit the number of users in the result for display
        #on the main page, we might also want to completely hide fake gravatars
        #and show only real images and the visitors - even if he does not have
        #a real image and try to prompt him/her to upload a picture
        from askbot.conf import settings as askbot_settings
        avatar_limit = askbot_settings.SIDEBAR_MAIN_AVATAR_LIMIT
        contributors = User.objects.filter(id__in=u_id).order_by('avatar_type', '?')[:avatar_limit]
        return contributors

    def get_for_user(self, user):
        """returns threads where a given user had participated"""
        post_ids = PostRevision.objects.filter(
                                        author = user
                                    ).values_list(
                                        'post_id', flat = True
                                    ).distinct()
        thread_ids = Post.objects.filter(
                                        id__in = post_ids
                                    ).values_list(
                                        'thread_id', flat = True
                                    ).distinct()
        return self.filter(id__in = thread_ids)


class ThreadToGroup(models.Model):
    """the "through" many-to-many relation between
    threads and groups - to distinguish full and "what's published"
    visibility of threads to various groups
    """
    SHOW_PUBLISHED_RESPONSES = 0
    SHOW_ALL_RESPONSES = 1
    VISIBILITY_CHOICES = (
        (SHOW_PUBLISHED_RESPONSES, 'show only published responses'),
        (SHOW_ALL_RESPONSES, 'show all responses')
    )
    thread = models.ForeignKey('Thread')
    group = models.ForeignKey(Group)
    visibility = models.SmallIntegerField(
                        choices=VISIBILITY_CHOICES,
                        default=SHOW_ALL_RESPONSES
                    )

    class Meta:
        unique_together = ('thread', 'group')
        db_table = 'askbot_thread_groups'
        app_label = 'askbot'


class Thread(models.Model):
    SUMMARY_CACHE_KEY_TPL = 'thread-exercise-summary-%d'
    PROBLEM_LIST_KEY_TPL = 'thread-problem-list-%d'
    SOLUTION_LIST_KEY_TPL = 'thread-solution-list-%d'
    #MAXTODO: Does a thread need a SOLUTION_LIST_KEY_TPL = 'thread-solution-list-%d'
    #Threads (exercises) are directly attached to problems but only indirectly attached to solutions
    #Through problems that are already attached.  Searches don't show any obvious use of this.

    title = models.CharField(max_length=300)

    tags = models.ManyToManyField('Tag', related_name='threads')
    groups = models.ManyToManyField(Group, through=ThreadToGroup, related_name='group_threads')

    # Denormalised data, transplanted from Exercise
    tagnames = models.CharField(max_length=125)
    view_count = models.PositiveIntegerField(default=0)
    favourite_count = models.PositiveIntegerField(default=0)
    problem_count = models.PositiveIntegerField(default=0)
    #MAX: Added solution_count
    solution_count = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(default=datetime.datetime.now)
    last_activity_by = models.ForeignKey(User, related_name='unused_last_active_in_threads')

    followed_by     = models.ManyToManyField(User, related_name='followed_threads')
    favorited_by    = models.ManyToManyField(User, through='FavoriteExercise', related_name='unused_favorite_threads')

    closed          = models.BooleanField(default=False)
    closed_by       = models.ForeignKey(User, null=True, blank=True) #, related_name='closed_exercises')
    closed_at       = models.DateTimeField(null=True, blank=True)
    close_reason    = models.SmallIntegerField(
                                            choices=const.CLOSE_REASONS,
                                            null=True,
                                            blank=True
                                        )

    #denormalized data: the core approval of the posts is made
    #in the revisions. In the revisions there is more data about
    #approvals - by whom and when
    approved = models.BooleanField(default=True, db_index=True)
    #MAXTODO: Notion of accepted has to do with Moderation which we won't support right away
    #Whole approach to moderation may need to change anyway.  This is a foreign key on one accepted
    #problem.  Our model will have multiple accepted problems per exercise.
    accepted_problem = models.ForeignKey(Post, null=True, blank=True, related_name='+')
    problem_accepted_at = models.DateTimeField(null=True, blank=True)
    added_at = models.DateTimeField(default = datetime.datetime.now)

    #db_column will be removed later
    points = models.IntegerField(default = 0, db_column='score')

    objects = ThreadManager()

    class Meta:
        app_label = 'askbot'

    #property to support legacy themes in case there are.
    @property
    def score(self):
        return int(self.points)
    @score.setter
    def score(self, number):
        if number:
            self.points = int(number)

    def _exercise_post(self, refresh=False):
        if refresh and hasattr(self, '_exercise_cache'):
            delattr(self, '_exercise_cache')
        post = getattr(self, '_exercise_cache', None)
        if post:
            return post
        self._exercise_cache = Post.objects.get(post_type='exercise', thread=self)
        return self._exercise_cache

    def get_absolute_url(self):
        return self._exercise_post().get_absolute_url(thread = self)
        #exercise_id = self._exercise_post().id
        #return reverse('exercise', args = [exercise_id]) + slugify(self.title)

    def get_problem_count(self, user = None):
        """returns problem count depending on who the user is.
        When user groups are enabled and some problems are hidden,
        the problem count to show must be reflected accordingly"""
        if askbot_settings.GROUPS_ENABLED == False:
            return self.problem_count
        else:
            return self.get_problems(user).count()
     
    #MAX: Added this accessor to solution count       
    def get_solution_count(self, user = None):
        """returns solution count depending on who the user is.
        When user groups are enabled and some solutionss are hidden,
        the solution count to show must be reflected accordingly"""
        if askbot_settings.GROUPS_ENABLED == False:
            return self.solution_count
        else:
            return self.get_solutions(user).count()

    def get_sharing_info(self, visitor=None):
        """returns a dictionary with abbreviated thread sharing info:
        * users - up to a certain number of users, excluding the visitor
        * groups - up to a certain number of groups
        * more_users_count - remaining count of shared-with users
        * more_groups_count - remaining count of shared-with groups
        """
        shared_users = self.get_users_shared_with(
                                            max_count=2,#"visitor" is implicit
                                            exclude_user=visitor
                                        )
        groups = self.groups
        ugroups = groups.get_personal()
        ggroups = groups.exclude_personal()

        sharing_info = {
            'users': shared_users,
            'groups': self.get_groups_shared_with(max_count=3),
            'more_users_count': max(0, ugroups.count() - 3),
            'more_groups_count': max(0, ggroups.count() - 3)
        }
        return sharing_info

    def get_users_shared_with(self, max_count=None, exclude_user=None):
        """returns query set of users with whom
        this thread is shared
        """
        filter = models.Q(
                        thread=self,
                        visibility=ThreadToGroup.SHOW_ALL_RESPONSES
                    ) & models.Q(
                        group__name__startswith=PERSONAL_GROUP_NAME_PREFIX
                    )

        if exclude_user:
            user_group = exclude_user.get_personal_group()
            filter = filter & ~models.Q(group_id=user_group.id)

        thread_groups = ThreadToGroup.objects.filter(filter)

        if max_count:
            thread_groups = thread_groups[:max_count]

        group_ids = thread_groups.values_list('group_id', flat=True)

        from askbot.models import GroupMembership
        user_ids = GroupMembership.objects.filter(
                                    group__id__in=group_ids
                                ).values_list(
                                    'user__id', flat=True
                                )

        return User.objects.filter(id__in=user_ids)

    def get_groups_shared_with(self, max_count=None):
        """returns query set of groups with whom thread is shared"""
        thread_groups = ThreadToGroup.objects.filter(
                            models.Q(
                                thread=self,
                                visibility=ThreadToGroup.SHOW_ALL_RESPONSES
                            ) & ~models.Q(
                                group__name__startswith=PERSONAL_GROUP_NAME_PREFIX
                            )
                        )
        if max_count:
            thread_groups = thread_groups[:max_count]

        group_ids = thread_groups.values_list('group_id', flat=True)
        return Group.objects.filter(id__in=group_ids)

    def update_favorite_count(self):
        self.favourite_count = FavoriteExercise.objects.filter(thread=self).count()
        self.save()

    def update_problem_count(self):
        self.problem_count = self.get_problems().count()
        self.save()
    
    #MAX:  Added this update to solution count    
    def update_solution_count(self):
        self.solution_count = self.get_solutions().count()
        self.save()

    def increase_view_count(self, increment=1):
        qset = Thread.objects.filter(id=self.id)
        qset.update(view_count=models.F('view_count') + increment)
        self.view_count = qset.values('view_count')[0]['view_count'] # get the new view_count back because other pieces of code relies on such behaviour
        ####################################################################
        self.update_summary_html() # regenerate exercise/thread summary html
        ####################################################################

    def set_closed_status(self, closed, closed_by, closed_at, close_reason):
        self.closed = closed
        self.closed_by = closed_by
        self.closed_at = closed_at
        self.close_reason = close_reason
        self.save()
        self.invalidate_cached_data()
    
    #MAXTODO: This is used by moderation.  We don't currently moderate on solutions.
    #Also only supports one problem being accepted which doesn't fit the model of the project
    def set_accepted_problem(self, problem, timestamp):
        if problem and problem.thread != self:
            raise ValueError("Problem doesn't belong to this thread")
        self.accepted_problem = problem
        self.problem_accepted_at = timestamp
        self.save()

    def set_last_activity(self, last_activity_at, last_activity_by):
        self.last_activity_at = last_activity_at
        self.last_activity_by = last_activity_by
        self.save()
        ####################################################################
        self.update_summary_html() # regenerate exercise/thread summary html
        ####################################################################

    def get_tag_names(self):
        "Creates a list of Tag names from the ``tagnames`` attribute."
        if self.tagnames.strip() == '':
            return list()
        else:
            return self.tagnames.split(u' ')

    def get_title(self, exercise=None):
        if not exercise:
            exercise = self._exercise_post() # allow for optimization if the caller has already fetched the exercise post for this thread
        if self.is_private():
            attr = const.POST_STATUS['private']
        elif self.closed:
            attr = const.POST_STATUS['closed']
        elif exercise.deleted:
            attr = const.POST_STATUS['deleted']

        else:
            attr = None
        if attr is not None:
            return u'%s %s' % (self.title, attr)
        else:
            return self.title

    def format_for_email(self, user=None):
        """experimental function: output entire thread for email"""
        exercise, problems, junk, published_ans_ids = self.get_cached_post_data(user=user)
        output = exercise.format_for_email_as_subthread()
        if problems:
            problem_heading = ungettext(
                                    '%(count)d problem:',
                                    '%(count)d problems:',
                                    len(problems)
                                ) % {'count': len(problems)}
            output += '<p>%s</p>' % problem_heading
            for problem in problems:
                output += problem.format_for_email_as_subthread()
        return output

    def get_problems_by_user(self, user):
        """regardless - deleted or not"""
        return self.posts.filter(post_type='problem', author=user, deleted=False)
    
    #MAX:
    def get_solutions_by_user(self, user):
        """regardless - deleted or not"""
        return self.posts.filter(post_type='solution', author=user, deleted=False)

    def has_problem_by_user(self, user):
        #use len to cache the queryset
        return len(self.get_problems_by_user(user)) > 0
        
    #MAX:
    def has_solution_by_user(self, user):
        #use len to cache the queryset
        return len(self.get_solutions_by_user(user)) > 0

    def has_moderator(self, user):
        """true if ``user`` is also a thread moderator"""
        if user.is_anonymous():
            return False
        elif askbot_settings.GROUPS_ENABLED:
            if user.is_administrator_or_moderator():
                user_groups = user.get_groups(private=True)
                thread_groups = self.get_groups_shared_with()
                return bool(set(user_groups) & set(thread_groups))
        return False

    def requires_response_moderation(self, author):
        """true, if problems by a given author must be moderated
        before publishing to the enquirers"""
        author_groups = author.get_groups()
        thread_groups = self.get_groups_shared_with()
        for group in set(author_groups) & set(thread_groups):
            if group.moderate_problems_to_enquirers:
                return True

        return False

    def tagname_meta_generator(self):
        return u','.join([unicode(tag) for tag in self.get_tag_names()])

    def all_problems(self):
        return self.posts.get_problems()
        
    #MAX:
    def all_solutions(self):
        return self.posts.get_solutions()

    def get_problems(self, user=None):
        """returns query set for problems to this exercise
        that may be shown to the given user
        """
        if user is None or user.is_anonymous():
            return self.posts.get_problems().filter(deleted=False)
        else:
            return self.posts.get_problems(
                                    user=user
                                ).filter(deleted=False)
            #    return self.posts.get_problems(user=user).filter(
            #                models.Q(deleted=False) \
            #                | models.Q(author=user) \
            #                | models.Q(deleted_by=user)
            #            )
            #we used to show deleted problems to admins,
            #users who deleted those problems and problem owners
            #but later decided to not show deleted problems at all
            #because it makes caching the post lists for thread easier
            #if user.is_administrator() or user.is_moderator():
            #    return self.posts.get_problems(user=user)
            #else:
            #    return self.posts.get_problems(user=user).filter(
            #                models.Q(deleted=False) \
            #                | models.Q(author=user) \
            #                | models.Q(deleted_by=user)
            #            )
            
    #MAX:
    def get_solutions(self, user=None):
        """returns query set for solutions to problems of this exercise
        that may be shown to the given user
        """
        if user is None or user.is_anonymous():
            return self.posts.get_solutions().filter(deleted=False)
        else:
            return self.posts.get_solutions(
                                    user=user
                                ).filter(deleted=False)

    def invalidate_cached_thread_content_fragment(self):
        cache.cache.delete(self.SUMMARY_CACHE_KEY_TPL % self.id)

    def get_post_data_cache_key(self, sort_method = None):
        return 'thread-data-%s-%s' % (self.id, sort_method)

    def invalidate_cached_post_data(self):
        """needs to be called when anything notable
        changes in the post data - on votes, adding,
        deleting, editing content"""
        #we can call delete_many() here if using Django > 1.2
        for sort_method in const.PROBLEM_SORT_METHODS:
            cache.cache.delete(self.get_post_data_cache_key(sort_method))

    def invalidate_cached_data(self):
        self.invalidate_cached_post_data()
        #self.invalidate_cached_thread_content_fragment()
        self.update_summary_html()

    def get_cached_post_data(self, user = None, sort_method = 'votes'):
        """returns cached post data, as calculated by
        the method get_post_data()"""
        if askbot_settings.GROUPS_ENABLED:
            #temporary plug: bypass cache where groups are enabled
            return self.get_post_data(sort_method=sort_method, user=user)
        key = self.get_post_data_cache_key(sort_method)
        post_data = cache.cache.get(key)
        if not post_data:
            post_data = self.get_post_data(sort_method)
            cache.cache.set(key, post_data, const.LONG_TIME)
        return post_data

    #MAX: This is changed to attach solutions to problems via the 
    #set_cached_solutions method of the post class.
    def get_post_data(self, sort_method='votes', user=None):
        """returns exercise, problems as list and a list of post ids
        for the given thread, and the list of published post ids
        (four values)
        the returned posts are pre-stuffed with the comments
        all (both posts and the comments sorted in the correct
        order)
        problems are pre-stuffed with solutions
        """
        thread_posts = self.posts.all()
        if askbot_settings.GROUPS_ENABLED:
            if user is None or user.is_anonymous():
                groups = (get_global_group(),)
            else:
                groups = user.get_groups()

            thread_posts = thread_posts.filter(groups__in=groups)
            thread_posts = thread_posts.distinct()#important for >1 group

        thread_posts = thread_posts.order_by(
                    {
                        'latest':'-added_at',
                        'oldest':'added_at',
                        'votes':'-points'
                    }[sort_method]
                )
        #1) collect exercise, problem and comment posts and list of post id's
        problems = list()
        post_map = dict()
        #MAX:
        solution_map = dict()
        comment_map = dict()
        post_to_author = dict()
        exercise_post = None
        for post in thread_posts:
            #pass through only deleted exercise posts
            if post.deleted and post.post_type != 'exercise':
                continue
            if post.is_approved() is False:#hide posts on the moderation queue
                continue

            post_to_author[post.id] = post.author_id

            if post.post_type == 'problem':
                problems.append(post)
                post_map[post.id] = post
            #MAX:
            elif post.post_type == 'solution':
                if post.parent_id not in solution_map:
                    solution_map[post.parent_id] = list()
                solution_map[post.parent_id].append(post)
            elif post.post_type == 'comment':
                if post.parent_id not in comment_map:
                    comment_map[post.parent_id] = list()
                comment_map[post.parent_id].append(post)
            elif post.post_type == 'exercise':
                assert(exercise_post == None)
                post_map[post.id] = post
                exercise_post = post

        #2) sort comments in the temporal order
        for comment_list in comment_map.values():
            comment_list.sort(key=operator.attrgetter('added_at'))
        
        #MAX:  
        #2b) sort solutions in the temporal order
        for solution_list in solution_map.values():
            solution_list.sort(key=operator.attrgetter('added_at'))

        #3) attach comments to exercise and the problems
        for post_id, comment_list in comment_map.items():
            try:
                post_map[post_id].set_cached_comments(comment_list)
            except KeyError:
                pass#comment to deleted problem - don't want it
                
        #MAX:
        #3b) attach solutions to the problems
        for post_id, solution_list in solution_map.items():
            try:
                post_map[post_id].set_cached_solutions(solution_list)
            except KeyError:
                pass#solution to deleted problem - don't want it

        if self.has_accepted_problem() and self.accepted_problem.deleted == False:
            #Put the accepted problem to front
            #the second check is for the case when accepted problem is deleted
            if self.accepted_problem_id in post_map:
                accepted_problem = post_map[self.accepted_problem_id]
                problems.remove(accepted_problem)
                problems.insert(0, accepted_problem)

        #if user is not an inquirer, and thread is moderated,
        #put published problems first
        #todo: there may be > 1 enquirers
        published_problem_ids = list()
        if self.is_moderated() and user != exercise_post.author:
            #if moderated - then author is guaranteed to be the
            #limited visibility enquirer
            published_problem_ids = self.posts.get_problems(
                                        user=exercise_post.author#todo: may be > 1
                                    ).filter(
                                        deleted=False
                                    ).order_by(
                                        {
                                            'latest':'-added_at',
                                            'oldest':'added_at',
                                            'votes':'-points'
                                        }[sort_method]
                                    ).values_list('id', flat=True)

            published_problem_ids = reversed(published_problem_ids)
            #now put those problems first
            problem_map = dict([(problem.id, problem) for problem in problems])
            for problem_id in published_problem_ids:
                problem = problem_map[problem_id]
                problems.remove(problem)
                problems.insert(0, problem)

        return (exercise_post, problems, post_to_author, published_problem_ids)

    def has_accepted_problem(self):
        return self.accepted_problem_id != None

    def get_similarity(self, other_thread = None):
        """return number of tags in the other exercise
        that overlap with the current exercise (self)
        """
        my_tags = set(self.get_tag_names())
        others_tags = set(other_thread.get_tag_names())
        return len(my_tags & others_tags)

    def get_similar_threads(self):
        """
        Get 10 similar threads for given one.
        Threads with the individual tags will be added to list if above exercises are not full.

        This function has a limitation that it will
        retrieve only 100 records then select 10 most similar
        from that list as querying entire database may
        be very expensive - this function will benefit from
        some sort of optimization
        """

        def get_data():
            # todo: code in this function would be simpler if
            # we had exercise post id denormalized on the thread
            tags_list = self.get_tag_names()
            similar_threads = Thread.objects.filter(
                                        tags__name__in=tags_list
                                    ).exclude(
                                        id = self.id
                                    ).exclude(
                                        posts__post_type='exercise',
                                        posts__deleted = True
                                    ).distinct()[:100]
            similar_threads = list(similar_threads)

            for thread in similar_threads:
                thread.similarity = self.get_similarity(other_thread=thread)

            similar_threads.sort(key=operator.attrgetter('similarity'), reverse=True)
            similar_threads = similar_threads[:10]

            # Denormalize exercises to speed up template rendering
            # todo: just denormalize exercise_post_id on the thread!
            thread_map = dict([(thread.id, thread) for thread in similar_threads])
            exercises = Post.objects.get_exercises()
            exercises = exercises.select_related('thread').filter(thread__in=similar_threads)
            for q in exercises:
                thread_map[q.thread_id].exercise_denorm = q

            # Postprocess data for the final output
            result = list()
            for thread in similar_threads:
                exercise_post = getattr(thread, 'exercise_denorm', None)
                # unfortunately the if statement below is necessary due to
                # a possible bug
                # all this proves that it's wrong to reference threads by
                # the exercise post id in the exercise page urls!!!
                # this is a "legacy" problem inherited from the old models
                if exercise_post:
                    url = exercise_post.get_absolute_url()
                    title = thread.get_title(exercise_post)
                    result.append({'url': url, 'title': title})

            return result

        def get_cached_data():
            """similar thread data will expire
            with the default expiration delay
            """
            key = 'similar-threads-%s' % self.id
            data = cache.cache.get(key)
            if data is None:
                data = get_data()
                cache.cache.set(key, data)
            return data

        return LazyList(get_cached_data)

    def remove_author_anonymity(self):
        """removes anonymous flag from the exercise
        and all its revisions
        the function calls update method to make sure that
        signals are not called
        """
        #note: see note for the is_anonymous field
        #it is important that update method is called - not save,
        #because we do not want the signals to fire here
        thread_exercise = self._exercise_post()
        Post.objects.filter(id=thread_exercise.id).update(is_anonymous=False)
        thread_exercise.revisions.all().update(is_anonymous=False)

    def is_followed_by(self, user = None):
        """True if thread is followed by user"""
        if user and user.is_authenticated():
            return self.followed_by.filter(id = user.id).count() > 0
        return False

    def is_moderated(self):
        """True, if tread has SHOW_PUBLISHED_RESPONSES
        group memberships"""
        if askbot_settings.GROUPS_ENABLED:
            return ThreadToGroup.objects.filter(
                            thread=self,
                            visibility=ThreadToGroup.SHOW_PUBLISHED_RESPONSES
                        ).count() > 0
        return False

    def add_child_posts_to_groups(self, groups):
        """adds exercises and problems of the thread to
        given groups, comments are taken care of implicitly
        by the underlying ``Post`` methods
        """
        post_types = ('exercise', 'problem', 'solution')
        posts = self.posts.filter(post_type__in=post_types)
        for post in posts:
            post.add_to_groups(groups)

    def remove_child_posts_from_groups(self, groups):
        """removes child posts from given groups"""
        post_ids = self.posts.all().values_list('id', flat=True)
        group_ids = [group.id for group in groups]
        PostToGroup.objects.filter(
                        post__id__in=post_ids,
                        tag__id__in=group_ids
                    ).delete()

    def add_to_groups(
        self, groups, visibility=ThreadToGroup.SHOW_ALL_RESPONSES, recursive=False
    ):
        """adds thread to a list of groups
        ``groups`` argument may be any iterable of groups
        """
        for group in groups:
            #todo: change to bulk create when django 1.3 goes out of use
            thread_group, created = ThreadToGroup.objects.get_or_create(
                                                    thread=self,
                                                    group=group
                                                )

            if thread_group.visibility != visibility:
                thread_group.visibility = visibility
                thread_group.save()

        if recursive == True:
            #comments are taken care of automatically
            #Not any more.  comments are not added to groups for now after solutions accommodated
            self.add_child_posts_to_groups(groups)

    def remove_from_groups(self, groups, recursive=False):
        thread_groups =  ThreadToGroup.objects.filter(
                                        thread=self, group__in=groups
                                    )
        thread_groups.delete()
        if recursive == True:
            self.remove_child_posts_from_groups(groups)

    def make_public(self, recursive=False):
        """adds the global group to the thread"""
        groups = (get_global_group(), )
        self.add_to_groups(groups, recursive=recursive)
        if recursive == False:
            self._exercise_post().make_public()

    def make_private(self, user, group_id = None):
        """adds thread to all user's groups, excluding
        the global, or to a group given by id.
        The add by ID now only works if user belongs to that group
        """
        if group_id:
            group = Group.objects.get(id=group_id)
            groups = [group]
            self.add_to_groups(groups)

            global_group = get_global_group()
            if group != global_group:
                self.remove_from_groups((global_group,))
        else:
            groups = user.get_groups(private=True)
            self.add_to_groups(groups)
            self.remove_from_groups((get_global_group(),))

        self._exercise_post().make_private(user, group_id)

        if len(groups) == 0:
            message = 'Sharing did not work, because group is unknown'
            user.message_set.create(message=message)

    def is_private(self):
        """true, if thread belongs to the global group"""
        if askbot_settings.GROUPS_ENABLED:
            group = get_global_group()
            return not self.groups.filter(id=group.id).exists()
        return False


    def remove_tags_by_names(self, tagnames):
        """removes tags from thread by names"""
        removed_tags = list()
        for tag in self.tags.all():
            if tag.name in tagnames:
                tag.used_count -= 1
                removed_tags.append(tag)
        self.tags.remove(*removed_tags)
        return removed_tags


    def update_tags(
        self, tagnames = None, user = None, timestamp = None
    ):
        """
        Updates Tag associations for a thread to match the given
        tagname string.
        When tags are removed and their use count hits 0 - the tag is
        automatically deleted.
        When an added tag does not exist - it is created
        If tag moderation is on - new tags are placed on the queue

        Tag use counts are recalculated
        A signal tags updated is sent

        *IMPORTANT*: self._exercise_post() has to
        exist when update_tags() is called!
        """
        if tagnames.strip() == '':
            return

        previous_tags = list(self.tags.filter(status = Tag.STATUS_ACCEPTED))

        ordered_updated_tagnames = [t for t in tagnames.strip().split(' ')]

        previous_tagnames = set([tag.name for tag in previous_tags])
        updated_tagnames = set(ordered_updated_tagnames)
        removed_tagnames = previous_tagnames - updated_tagnames

        #remove tags from the exercise's tags many2many relation
        #used_count values are decremented on all tags
        removed_tags = self.remove_tags_by_names(removed_tagnames)

        #modified tags go on to recounting their use
        #todo - this can actually be done asynchronously - not so important
        modified_tags, unused_tags = separate_unused_tags(removed_tags)
        delete_tags(unused_tags)#tags with used_count == 0 are deleted

        modified_tags = removed_tags

        #add new tags to the relation
        added_tagnames = updated_tagnames - previous_tagnames

        if added_tagnames:
            #find reused tags
            reused_tags, new_tagnames = get_tags_by_names(added_tagnames)
            reused_tags.mark_undeleted()

            added_tags = list(reused_tags)
            #tag moderation is in the call below
            created_tags = Tag.objects.create_in_bulk(
                                            tag_names = new_tagnames, user = user
                                        )

            added_tags.extend(created_tags)
            #todo: not nice that assignment of added_tags is way above
            self.tags.add(*added_tags)
            modified_tags.extend(added_tags)
        else:
            added_tags = Tag.objects.none()

        #Save denormalized tag names on thread. Preserve order from user input.
        accepted_added_tags = filter_accepted_tags(added_tags)
        added_tagnames = set([tag.name for tag in accepted_added_tags])
        final_tagnames = (previous_tagnames - removed_tagnames) | added_tagnames
        ordered_final_tagnames = list()
        for tagname in ordered_updated_tagnames:
            if tagname in final_tagnames:
                ordered_final_tagnames.append(tagname)

        self.tagnames = ' '.join(ordered_final_tagnames)
        self.save()#need to save here?

        #todo: factor out - tell author about suggested tags
        suggested_tags = filter_suggested_tags(added_tags)
        if len(suggested_tags) > 0:
            #1) notify author that the tag is going to be moderated
            #todo: factor this out
            if len(suggested_tags) == 1:
                msg = _(
                    'Tag %s is new and will be submitted for the '
                    'moderators approval'
                ) % suggested_tags[0].name
            else:
                msg = _(
                    'Tags %s are new and will be submitted for the '
                    'moderators approval'
                ) % ', '.join([tag.name for tag in suggested_tags])
            user.message_set.create(message = msg)
            #2) todo: notify moderators about newly suggested tags

        ####################################################################
        self.update_summary_html() # regenerate exercise/thread summary html
        ####################################################################

        #if there are any modified tags, update their use counts
        if modified_tags:
            Tag.objects.update_use_counts(modified_tags)
            signals.tags_updated.send(None,
                                thread = self,
                                tags = modified_tags,
                                user = user,
                                timestamp = timestamp
                            )
            return True

        return False

    def add_tag(
        self, user = None, timestamp = None, tag_name = None, silent = False
    ):
        """adds one tag to thread"""
        tag_names = self.get_tag_names()
        if tag_name in tag_names:
            return
        tag_names.append(tag_name)

        self.retag(
            retagged_by = user,
            retagged_at = timestamp,
            tagnames = ' '.join(tag_names),
            silent = silent
        )

    def retag(self, retagged_by=None, retagged_at=None, tagnames=None, silent=False):
        """changes thread tags"""
        if None in (retagged_by, retagged_at, tagnames):
            raise Exception('arguments retagged_at, retagged_by and tagnames are required')

        thread_exercise = self._exercise_post()

        self.tagnames = tagnames.strip()
        self.save()

        # Update the Exercise itself
        if silent == False:
            thread_exercise.last_edited_at = retagged_at
            #thread_exercise.thread.last_activity_at = retagged_at
            thread_exercise.last_edited_by = retagged_by
            #thread_exercise.thread.last_activity_by = retagged_by
            thread_exercise.save()

        # Update the Thread's tag associations
        self.update_tags(tagnames=tagnames, user=retagged_by, timestamp=retagged_at)

        # Create a new revision
        latest_revision = thread_exercise.get_latest_revision()
        PostRevision.objects.create(
            post = thread_exercise,
            title      = latest_revision.title,
            author     = retagged_by,
            revised_at = retagged_at,
            tagnames   = tagnames,
            summary    = const.POST_STATUS['retagged'],
            text       = latest_revision.text
        )

    def has_favorite_by_user(self, user):
        if not user.is_authenticated():
            return False

        return FavoriteExercise.objects.filter(thread=self, user=user).exists()

    def get_last_update_info(self):
        posts = list(self.posts.select_related('author', 'last_edited_by'))

        last_updated_at = posts[0].added_at
        last_updated_by = posts[0].author

        for post in posts:
            last_updated_at, last_updated_by = max((last_updated_at, last_updated_by), (post.added_at, post.author))
            if post.last_edited_at:
                last_updated_at, last_updated_by = max((last_updated_at, last_updated_by), (post.last_edited_at, post.last_edited_by))

        return last_updated_at, last_updated_by

    def get_summary_html(self, search_state=None, visitor = None):
        html = self.get_cached_summary_html(visitor)
        if not html:
            html = self.update_summary_html(visitor)

        # todo: this work may be pushed onto javascript we post-process tag names
        # in the snippet so that tag urls match the search state
        # use `<<<` and `>>>` because they cannot be confused with user input
        # - if user accidentialy types <<<tag-name>>> into exercise title or body,
        # then in html it'll become escaped like this: &lt;&lt;&lt;tag-name&gt;&gt;&gt;
        regex = re.compile(
            r'<<<(%s)>>>' % const.TAG_REGEX_BARE,
            re.UNICODE
        )

        if search_state is None:
            search_state = DummySearchState()

        while True:
            match = regex.search(html)
            if not match:
                break
            seq = match.group(0)  # e.g "<<<my-tag>>>"
            tag = match.group(1)  # e.g "my-tag"
            full_url = search_state.add_tag(tag).full_url()
            html = html.replace(seq, full_url)

        return html

    def get_cached_summary_html(self, visitor = None):
        #todo: remove this plug by adding cached foreign user group
        #parameter to the key. Now with groups on caching is turned off
        #parameter visitor is there to get summary out by the user groups
        if askbot_settings.GROUPS_ENABLED:
            return None
        return cache.cache.get(self.SUMMARY_CACHE_KEY_TPL % self.id)

    def update_summary_html(self, visitor = None):
        #todo: it is quite wrong that visitor is an argument here
        #because we do not include any visitor-related info in the cache key
        #ideally cache should be shareable between users, so straight up
        #using the user id for cache is wrong, we could use group
        #memberships, but in that case we'd need to be more careful with 
        #cache invalidation
        context = {
            'thread': self,
            #fetch new exercise post to make sure we're up-to-date
            'exercise': self._exercise_post(refresh=True),
            'search_state': DummySearchState(),
            'visitor': visitor
        }
        html = get_template('widgets/exercise_summary.html').render(context)
        # INFO: Timeout is set to 30 days:
        # * timeout=0/None is not a reliable cross-backend way to set infinite timeout
        # * We probably don't need to pollute the cache with threads older than 30 days
        # * Additionally, Memcached treats timeouts > 30day as dates (https://code.djangoproject.com/browser/django/tags/releases/1.3/django/core/cache/backends/memcached.py#L36),
        #   which probably doesn't break anything but if we can stick to 30 days then let's stick to it
        cache.cache.set(
            self.SUMMARY_CACHE_KEY_TPL % self.id,
            html,
            timeout=const.LONG_TIME
        )
        return html

    def summary_html_cached(self):
        return cache.cache.has_key(self.SUMMARY_CACHE_KEY_TPL % self.id)

class ExerciseView(models.Model):
    exercise = models.ForeignKey(Post, related_name='viewed')
    who = models.ForeignKey(User, related_name='exercise_views')
    when = models.DateTimeField()

    class Meta:
        app_label = 'askbot'

class FavoriteExercise(models.Model):
    """A favorite Exercise of a User."""
    thread        = models.ForeignKey(Thread)
    user          = models.ForeignKey(User, related_name='user_favorite_exercises')
    added_at      = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        app_label = 'askbot'
        db_table = u'favorite_exercise'
    def __unicode__(self):
        return '[%s] favorited at %s' %(self.user, self.added_at)


class DraftExercise(models.Model):
    """Provides space to solve unpublished draft
    exercises. Contents is used to populate the Ask form.
    """
    author = models.ForeignKey(User)
    title = models.CharField(max_length=300, null=True)
    text = models.TextField(null=True)
    tagnames = models.CharField(max_length=125, null=True)

    class Meta:
        app_label = 'askbot'


class AnonymousExercise(DraftContent):
    """exercise that was asked before logging in
    maybe the name is a little misleading, the user still
    may or may not want to stay anonymous after the exercise
    is published
    """
    title = models.CharField(max_length=300)
    tagnames = models.CharField(max_length=125)
    is_anonymous = models.BooleanField(default=False)

    def publish(self,user):
        added_at = datetime.datetime.now()
        #todo: wrong - use User.post_exercise() instead
        Thread.objects.create_new(
            title = self.title,
            added_at = added_at,
            author = user,
            wiki = self.wiki,
            is_anonymous = self.is_anonymous,
            tagnames = self.tagnames,
            text = self.text,
        )
        self.delete()
