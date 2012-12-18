# encoding:utf-8
"""
:synopsis: views "read-only" for main textual content

By main textual content is meant - text of Exercises, Problems and Comments.
The "read-only" requirement here is not 100% strict, as for example "exercise" view does
allow adding new comments via Ajax form post.
"""
import datetime
import logging
import urllib
import operator
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseNotAllowed
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template import Context
from django.utils import simplejson
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.utils import translation
from django.views.decorators import csrf
from django.core.urlresolvers import reverse
from django.core import exceptions as django_exceptions
from django.contrib.humanize.templatetags import humanize
from django.http import QueryDict
from django.conf import settings

import askbot
from askbot import exceptions
from askbot.utils.diff import textDiff as htmldiff
from askbot.forms import ProblemForm, ShowExerciseForm, AnswerForm
from askbot import conf
from askbot import models
from askbot import schedules
from askbot.models.tag import Tag
from askbot import const
from askbot.utils import functions
from askbot.utils.html import sanitize_html
from askbot.utils.decorators import anonymous_forbidden, ajax_only, get_only
from askbot.search.state_manager import SearchState, DummySearchState
from askbot.templatetags import extra_tags
from askbot.conf import settings as askbot_settings
from askbot.skins.loaders import render_into_skin, get_template #jinja2 template loading enviroment
from askbot.views import context

# used in index page
#todo: - take these out of const or settings
from askbot.models import Post, Vote

INDEX_PAGE_SIZE = 30
INDEX_AWARD_SIZE = 15
INDEX_TAGS_SIZE = 25
# used in tags list
DEFAULT_PAGE_SIZE = 60
# used in exercises
# used in problems

#refactor? - we have these
#views that generate a listing of exercises in one way or another:
#index, without_problem, exercises, search, tag
#should we dry them up?
#related topics - information drill-down, search refinement

def index(request):#generates front page - shows listing of exercises sorted in various ways
    """index view mapped to the root url of the Q&A site
    """
    return HttpResponseRedirect(reverse('exercises'))

def exercises(request, **kwargs):
    """
    List of Exercises, Tagged exercises, and Exercises without problems.
    matching search query or user selection
    """
    #before = datetime.datetime.now()
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    search_state = SearchState(
                    user_logged_in=request.user.is_authenticated(),
                    **kwargs
                )
    page_size = int(askbot_settings.DEFAULT_EXERCISES_PAGE_SIZE)

    qs, meta_data = models.Thread.objects.run_advanced_search(
                        request_user=request.user, search_state=search_state
                    )
    if meta_data['non_existing_tags']:
        search_state = search_state.remove_tags(meta_data['non_existing_tags'])

    paginator = Paginator(qs, page_size)
    if paginator.num_pages < search_state.page:
        search_state.page = 1
    page = paginator.page(search_state.page)
    page.object_list = list(page.object_list) # evaluate the queryset

    # INFO: Because for the time being we need exercise posts and thread authors
    #       down the pipeline, we have to precache them in thread objects
    models.Thread.objects.precache_view_data_hack(threads=page.object_list)

    related_tags = Tag.objects.get_related_to_search(
                        threads=page.object_list,
                        ignored_tag_names=meta_data.get('ignored_tag_names',[])
                    )
    tag_list_type = askbot_settings.TAG_LIST_FORMAT
    if tag_list_type == 'cloud': #force cloud to sort by name
        related_tags = sorted(related_tags, key = operator.attrgetter('name'))

    contributors = list(
        models.Thread.objects.get_thread_contributors(
                                        thread_list=page.object_list
                                    ).only('id', 'username', 'gravatar')
                        )

    paginator_context = {
        'is_paginated' : (paginator.count > page_size),

        'pages': paginator.num_pages,
        'page': search_state.page,
        'has_previous': page.has_previous(),
        'has_next': page.has_next(),
        'previous': page.previous_page_number(),
        'next': page.next_page_number(),

        'base_url' : search_state.query_string(),
        'page_size' : page_size,
    }

    # We need to pass the rss feed url based
    # on the search state to the template.
    # We use QueryDict to get a querystring
    # from dicts and arrays. Much cleaner
    # than parsing and string formating.
    rss_query_dict = QueryDict("").copy()
    if search_state.query:
        # We have search string in session - pass it to
        # the QueryDict
        rss_query_dict.update({"q": search_state.query})
    if search_state.tags:
        # We have tags in session - pass it to the
        # QueryDict but as a list - we want tags+
        rss_query_dict.setlist("tags", search_state.tags)
    context_feed_url = '/%sfeeds/rss/?%s' % (settings.ASKBOT_URL, rss_query_dict.urlencode()) # Format the url with the QueryDict

    reset_method_count = len(filter(None, [search_state.query, search_state.tags, meta_data.get('author_name', None)]))

    if request.is_ajax():
        q_count = paginator.count

        exercise_counter = ungettext('%(q_num)s exercise', '%(q_num)s exercises', q_count)
        exercise_counter = exercise_counter % {'q_num': humanize.intcomma(q_count),}

        if q_count > page_size:
            paginator_tpl = get_template('main_page/paginator.html', request)
            paginator_html = paginator_tpl.render(Context({
                'context': functions.setup_paginator(paginator_context),
                'exercises_count': q_count,
                'page_size' : page_size,
                'search_state': search_state,
            }))
        else:
            paginator_html = ''

        exercises_tpl = get_template('main_page/exercises_loop.html', request)
        exercises_html = exercises_tpl.render(Context({
            'threads': page,
            'search_state': search_state,
            'reset_method_count': reset_method_count,
            'request': request
        }))

        ajax_data = {
            'query_data': {
                'tags': search_state.tags,
                'sort_order': search_state.sort,
                'ask_query_string': search_state.ask_query_string(),
            },
            'paginator': paginator_html,
            'exercise_counter': exercise_counter,
            'faces': [],#[extra_tags.gravatar(contributor, 48) for contributor in contributors],
            'feed_url': context_feed_url,
            'query_string': search_state.query_string(),
            'page_size' : page_size,
            'exercises': exercises_html.replace('\n',''),
            'non_existing_tags': meta_data['non_existing_tags']
        }
        ajax_data['related_tags'] = [{
            'name': escape(tag.name),
            'used_count': humanize.intcomma(tag.local_used_count)
        } for tag in related_tags]

        return HttpResponse(simplejson.dumps(ajax_data), mimetype = 'application/json')

    else: # non-AJAX branch

        template_data = {
            'active_tab': 'exercises',
            'author_name' : meta_data.get('author_name',None),
            'contributors' : contributors,
            'context' : paginator_context,
            'is_without_problem' : False,#remove this from template
            'interesting_tag_names': meta_data.get('interesting_tag_names', None),
            'ignored_tag_names': meta_data.get('ignored_tag_names', None),
            'subscribed_tag_names': meta_data.get('subscribed_tag_names', None),
            'language_code': translation.get_language(),
            'name_of_anonymous_user' : models.get_name_of_anonymous_user(),
            'page_class': 'main-page',
            'page_size': page_size,
            'query': search_state.query,
            'threads' : page,
            'exercises_count' : paginator.count,
            'reset_method_count': reset_method_count,
            'scope': search_state.scope,
            'show_sort_by_relevance': conf.should_show_sort_by_relevance(),
            'search_tags' : search_state.tags,
            'sort': search_state.sort,
            'tab_id' : search_state.sort,
            'tags' : related_tags,
            'tag_list_type' : tag_list_type,
            'font_size' : extra_tags.get_tag_font_size(related_tags),
            'display_tag_filter_strategy_choices': conf.get_tag_display_filter_strategy_choices(),
            'email_tag_filter_strategy_choices': const.TAG_EMAIL_FILTER_STRATEGY_CHOICES,
            'update_avatar_data': schedules.should_update_avatar_data(request),
            'query_string': search_state.query_string(),
            'search_state': search_state,
            'feed_url': context_feed_url,
        }

        return render_into_skin('main_page.html', template_data, request)


def tags(request):#view showing a listing of available tags - plain list

    tag_list_type = askbot_settings.TAG_LIST_FORMAT

    if tag_list_type == 'list':

        stag = ""
        is_paginated = True
        sortby = request.GET.get('sort', 'used')
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        stag = request.GET.get("query", "").strip()
        if stag != '':
            objects_list = Paginator(
                            models.Tag.objects.filter(
                                                deleted=False,
                                                name__icontains=stag
                                            ).exclude(
                                                used_count=0
                                            ),
                            DEFAULT_PAGE_SIZE
                        )
        else:
            if sortby == "name":
                objects_list = Paginator(models.Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("name"), DEFAULT_PAGE_SIZE)
            else:
                objects_list = Paginator(models.Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("-used_count"), DEFAULT_PAGE_SIZE)

        try:
            tags = objects_list.page(page)
        except (EmptyPage, InvalidPage):
            tags = objects_list.page(objects_list.num_pages)

        paginator_data = {
            'is_paginated' : is_paginated,
            'pages': objects_list.num_pages,
            'page': page,
            'has_previous': tags.has_previous(),
            'has_next': tags.has_next(),
            'previous': tags.previous_page_number(),
            'next': tags.next_page_number(),
            'base_url' : reverse('tags') + '?sort=%s&amp;' % sortby
        }
        paginator_context = functions.setup_paginator(paginator_data)
        data = {
            'active_tab': 'tags',
            'page_class': 'tags-page',
            'tags' : tags,
            'tag_list_type' : tag_list_type,
            'stag' : stag,
            'tab_id' : sortby,
            'keywords' : stag,
            'paginator_context' : paginator_context,
        }

    else:

        stag = ""
        sortby = request.GET.get('sort', 'name')

        if request.method == "GET":
            stag = request.GET.get("query", "").strip()
            if stag != '':
                tags = models.Tag.objects.filter(deleted=False, name__icontains=stag).exclude(used_count=0)
            else:
                if sortby == "name":
                    tags = models.Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("name")
                else:
                    tags = models.Tag.objects.all().filter(deleted=False).exclude(used_count=0).order_by("-used_count")

        font_size = extra_tags.get_tag_font_size(tags)

        data = {
            'active_tab': 'tags',
            'page_class': 'tags-page',
            'tags' : tags,
            'tag_list_type' : tag_list_type,
            'font_size' : font_size,
            'stag' : stag,
            'tab_id' : sortby,
            'keywords' : stag,
            'search_state': SearchState(*[None for x in range(7)])
        }

    return render_into_skin('tags.html', data, request)

@csrf.csrf_protect
#@cache_page(60 * 5)
def exercise(request, id):#refactor - long subroutine. display exercise body, problems and comments
    """view that displays body of the exercise and
    all problems to it
    """
    #process url parameters
    #todo: fix inheritance of sort method from exercises
    #before = datetime.datetime.now()
    default_sort_method = request.session.get('exercises_sort_method', 'votes')
    form = ShowExerciseForm(request.GET, default_sort_method)
    form.full_clean()#always valid
    show_problem = form.cleaned_data['show_problem']
    show_comment = form.cleaned_data['show_comment']
    show_page = form.cleaned_data['show_page']
    problem_sort_method = form.cleaned_data['problem_sort_method']

    #load exercise and maybe refuse showing deleted exercise
    #if the exercise does not exist - try mapping to old exercises
    #and and if it is not found again - then give up
    try:
        exercise_post = models.Post.objects.filter(
                                post_type = 'exercise',
                                id = id
                            ).select_related('thread')[0]
    except IndexError:
    # Handle URL mapping - from old Q/A/C/ URLs to the new one
        try:
            exercise_post = models.Post.objects.filter(
                                    post_type='exercise',
                                    old_exercise_id = id
                                ).select_related('thread')[0]
        except IndexError:
            raise Http404

        if show_problem:
            try:
                old_problem = models.Post.objects.get_problems().get(old_problem_id=show_problem)
                return HttpResponseRedirect(old_problem.get_absolute_url())
            except models.Post.DoesNotExist:
                pass

        elif show_comment:
            try:
                old_comment = models.Post.objects.get_comments().get(old_comment_id=show_comment)
                return HttpResponseRedirect(old_comment.get_absolute_url())
            except models.Post.DoesNotExist:
                pass

    try:
        exercise_post.assert_is_visible_to(request.user)
    except exceptions.ExerciseHidden, error:
        request.user.message_set.create(message = unicode(error))
        return HttpResponseRedirect(reverse('index'))

    #redirect if slug in the url is wrong
    if request.path.split('/')[-2] != exercise_post.slug:
        logging.debug('no slug match!')
        exercise_url = '?'.join((
                            exercise_post.get_absolute_url(),
                            urllib.urlencode(request.GET)
                        ))
        return HttpResponseRedirect(exercise_url)


    #resolve comment and problem permalinks
    #they go first because in theory both can be moved to another exercise
    #this block "returns" show_post and assigns actual comment and problem
    #to show_comment and show_problem variables
    #in the case if the permalinked items or their parents are gone - redirect
    #redirect also happens if id of the object's origin post != requested id
    show_post = None #used for permalinks
    if show_comment:
        #if url calls for display of a specific comment,
        #check that comment exists, that it belongs to
        #the current exercise
        #if it is an problem comment and the problem is hidden -
        #redirect to the default view of the exercise
        #if the exercise is hidden - redirect to the main page
        #in addition - if url points to a comment and the comment
        #is for the problem - we need the problem object
        try:
            show_comment = models.Post.objects.get_comments().get(id=show_comment)
        except models.Post.DoesNotExist:
            error_message = _(
                'Sorry, the comment you are looking for has been '
                'deleted and is no longer accessible'
            )
            request.user.message_set.create(message = error_message)
            return HttpResponseRedirect(exercise_post.thread.get_absolute_url())

        if str(show_comment.thread._exercise_post().id) != str(id):
            return HttpResponseRedirect(show_comment.get_absolute_url())
        show_post = show_comment.parent

        try:
            show_comment.assert_is_visible_to(request.user)
        except exceptions.ProblemHidden, error:
            request.user.message_set.create(message = unicode(error))
            #use reverse function here because exercise is not yet loaded
            return HttpResponseRedirect(reverse('exercise', kwargs = {'id': id}))
        except exceptions.ExerciseHidden, error:
            request.user.message_set.create(message = unicode(error))
            return HttpResponseRedirect(reverse('index'))

    elif show_problem:
        #if the url calls to view a particular problem to
        #exercise - we must check whether the exercise exists
        #whether problem is actually corresponding to the current exercise
        #and that the visitor is allowed to see it
        show_post = get_object_or_404(models.Post, post_type='problem', id=show_problem)
        if str(show_post.thread._exercise_post().id) != str(id):
            return HttpResponseRedirect(show_post.get_absolute_url())

        try:
            show_post.assert_is_visible_to(request.user)
        except django_exceptions.PermissionDenied, error:
            request.user.message_set.create(message = unicode(error))
            return HttpResponseRedirect(reverse('exercise', kwargs = {'id': id}))

    thread = exercise_post.thread

    logging.debug('problem_sort_method=' + unicode(problem_sort_method))

    #load problems and post id's->athor_id mapping
    #posts are pre-stuffed with the correctly ordered comments
    updated_exercise_post, problems, post_to_author, published_problem_ids = thread.get_cached_post_data(
                                sort_method = problem_sort_method,
                                user = request.user
                            )
    exercise_post.set_cached_comments(
        updated_exercise_post.get_cached_comments()
    )


    #Post.objects.precache_comments(for_posts=[exercise_post] + problems, visitor=request.user)

    user_votes = {}
    user_post_id_list = list()
    #todo: cache this query set, but again takes only 3ms!
    if request.user.is_authenticated():
        user_votes = Vote.objects.filter(
                            user=request.user,
                            voted_post__id__in = post_to_author.keys()
                        ).values_list('voted_post_id', 'vote')
        user_votes = dict(user_votes)
        #we can avoid making this query by iterating through
        #already loaded posts
        user_post_id_list = [
            id for id in post_to_author if post_to_author[id] == request.user.id
        ]

    #resolve page number and comment number for permalinks
    show_comment_position = None
    if show_comment:
        show_page = show_comment.get_page_number(problem_posts=problems)
        show_comment_position = show_comment.get_order_number()
    elif show_problem:
        show_page = show_post.get_page_number(problem_posts=problems)

    objects_list = Paginator(problems, const.PROBLEMS_PAGE_SIZE)
    if show_page > objects_list.num_pages:
        return HttpResponseRedirect(exercise_post.get_absolute_url())
    page_objects = objects_list.page(show_page)

    #count visits
    #import ipdb; ipdb.set_trace()
    if functions.not_a_robot_request(request):
        #todo: split this out into a subroutine
        #todo: merge view counts per user and per session
        #1) view count per session
        update_view_count = False
        if 'exercise_view_times' not in request.session:
            request.session['exercise_view_times'] = {}

        last_seen = request.session['exercise_view_times'].get(exercise_post.id, None)

        if thread.last_activity_by_id != request.user.id:
            if last_seen:
                if last_seen < thread.last_activity_at:
                    update_view_count = True
            else:
                update_view_count = True

        request.session['exercise_view_times'][exercise_post.id] = \
                                                    datetime.datetime.now()

        #2) run the slower jobs in a celery task
        from askbot import tasks
        tasks.record_exercise_visit.delay(
            exercise_post = exercise_post,
            user = request.user,
            update_view_count = update_view_count
        )

    paginator_data = {
        'is_paginated' : (objects_list.count > const.PROBLEMS_PAGE_SIZE),
        'pages': objects_list.num_pages,
        'page': show_page,
        'has_previous': page_objects.has_previous(),
        'has_next': page_objects.has_next(),
        'previous': page_objects.previous_page_number(),
        'next': page_objects.next_page_number(),
        'base_url' : request.path + '?sort=%s&amp;' % problem_sort_method,
    }
    paginator_context = functions.setup_paginator(paginator_data)

    #todo: maybe consolidate all activity in the thread
    #for the user into just one query?
    favorited = thread.has_favorite_by_user(request.user)

    is_cacheable = True
    if show_page != 1:
        is_cacheable = False
    elif show_comment_position > askbot_settings.MAX_COMMENTS_TO_SHOW:
        is_cacheable = False

    initial = {
        'wiki': exercise_post.wiki and askbot_settings.WIKI_ON,
        'email_notify': thread.is_followed_by(request.user)
    }
    #maybe load draft
    if request.user.is_authenticated():
        #todo: refactor into methor on thread
        drafts = models.DraftProblem.objects.filter(
                                        author=request.user,
                                        thread=thread
                                    )
        if drafts.count() > 0:
            initial['text'] = drafts[0].text

    problem_form = ProblemForm(initial)
    answer_form = AnswerForm(initial)

    user_can_post_comment = (
        request.user.is_authenticated() and request.user.can_post_comment()
    )

    user_already_gave_problem = False
    previous_problem = None
    if request.user.is_authenticated():
        if askbot_settings.LIMIT_ONE_PROBLEM_PER_USER:
            for problem in problems:
                if problem.author == request.user:
                    user_already_gave_problem = True
                    previous_problem = problem
                    break

    data = {
        'is_cacheable': False,#is_cacheable, #temporary, until invalidation fix
        'long_time': const.LONG_TIME,#"forever" caching
        'page_class': 'exercise-page',
        'active_tab': 'exercises',
        'exercise' : exercise_post,
        'thread': thread,
        'thread_is_moderated': thread.is_moderated(),
        'user_is_thread_moderator': thread.has_moderator(request.user),
        'published_problem_ids': published_problem_ids,
        'problem' : problem_form,
        'problems' : page_objects.object_list,
        'problem_count': thread.get_problem_count(request.user),
        'category_tree_data': askbot_settings.CATEGORY_TREE,
        'user_votes': user_votes,
        'user_post_id_list': user_post_id_list,
        'user_can_post_comment': user_can_post_comment,#in general
        'user_already_gave_problem': user_already_gave_problem,
        'previous_problem': previous_problem,
        'tab_id' : problem_sort_method,
        'favorited' : favorited,
        'similar_threads' : thread.get_similar_threads(),
        'language_code': translation.get_language(),
        'paginator_context' : paginator_context,
        'show_post': show_post,
        'show_comment': show_comment,
        'show_comment_position': show_comment_position,
        'answer': answer_form,
        #'answers': answer_form,
    }
    #shared with ...
    if askbot_settings.GROUPS_ENABLED:
        data['sharing_info'] = thread.get_sharing_info()

    data.update(context.get_for_tag_editor())

    return render_into_skin('exercise.html', data, request)

def revisions(request, id, post_type = None):
    assert post_type in ('exercise', 'problem')
    post = get_object_or_404(models.Post, post_type=post_type, id=id)
    revisions = list(models.PostRevision.objects.filter(post=post))
    revisions.reverse()
    for i, revision in enumerate(revisions):
        if i == 0:
            revision.diff = sanitize_html(revisions[i].html)
            revision.summary = _('initial version')
        else:
            revision.diff = htmldiff(
                sanitize_html(revisions[i-1].html),
                sanitize_html(revision.html)
            )

    data = {
        'page_class':'revisions-page',
        'active_tab':'exercises',
        'post': post,
        'revisions': revisions,
    }
    return render_into_skin('revisions.html', data, request)

@csrf.csrf_exempt
@ajax_only
@anonymous_forbidden
@get_only
def get_comment(request):
    """returns text of a comment by id
    via ajax response requires request method get
    and request must be ajax
    """
    id = int(request.GET['id'])
    comment = models.Post.objects.get(post_type='comment', id=id)
    request.user.assert_can_edit_comment(comment)
    return {'text': comment.text}

#@decorators.check_authorization_to_post(_('Please log in to post answers'))
#@decorators.check_spam('text')
@csrf.csrf_protect
def new_answer_form(request, mid, pid):
    exercise_post = models.Post.objects.filter(
                                post_type = 'exercise',
                                id = mid
                            ).select_related('thread')[0]

    problem_post = models.Post.objects.filter(
                                post_type = 'problem',
                                id = pid
                            ).select_related('thread')[0]
    thread = exercise_post.thread
    initial = {
        'wiki': exercise_post.wiki and askbot_settings.WIKI_ON,
        'email_notify': thread.is_followed_by(request.user)
    }
    answer_form = AnswerForm(initial)
    # if exercise doesn't exist, redirect to main page
    data = {
        'pid': pid,
        'mid': mid,
        'exercise': exercise_post,
        'problem': problem_post,
        'thread': thread,
        'answer_form': answer_form
        }
    return render_into_skin('exercise/answer_form.html', data, request)
