import datetime
from django.conf import settings as django_settings
from django.test.client import Client
from askbot.tests.utils import AskbotTestCase
from askbot.conf import settings
from askbot import models
from askbot.models.badges import award_badges_signal

class BadgeTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username = 'user1')
        self.u2 = self.create_user(username = 'user2')
        self.u3 = self.create_user(username = 'user3')
        self.client = Client()

    def assert_have_badge(self, badge_key, recipient = None, expected_count = 1):
        """note - expected_count matches total number of
        badges within test, not the one that was awarded between the calls
        to this assertion"""
        filters = {'badge__slug': badge_key, 'user': recipient}
        count = models.Award.objects.filter(**filters).count()
        self.assertEquals(count, expected_count)

    def assert_accepted_problem_badge_works(self,
                                    badge_key = None,
                                    min_points = None,
                                    expected_count = 1,
                                    previous_count = 0,
                                    trigger = None
                                ):
        assert(trigger in ('accept_best_problem', 'upvote_problem'))
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u2, exercise = exercise)
        problem.points = min_points - 1
        problem.save()

        recipient = problem.author

        if trigger == 'accept_best_problem':
            self.u1.upvote(problem)
            self.assert_have_badge(badge_key, recipient, previous_count)
            self.u1.accept_best_problem(problem)
        else:
            self.u1.accept_best_problem(problem)
            self.assert_have_badge(badge_key, recipient, previous_count)
            self.u1.upvote(problem)
        self.assert_have_badge(badge_key, recipient, expected_count)

    def assert_upvoted_problem_badge_works(self,
                                    badge_key = None,
                                    min_points = None,
                                    multiple = False
                                ):
        """test problem badge where problem author is the recipient
        where badge award is triggered by upvotes
        * min_points - minimum # of upvotes required
        * multiple - multiple award or not
        * badge_key - key on askbot.models.badges.Badge object
        """
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u2, exercise = exercise)
        problem.points = min_points - 1
        problem.save()
        self.u1.upvote(problem)
        self.assert_have_badge(badge_key, recipient = self.u2)
        self.u3.upvote(problem)
        self.assert_have_badge(badge_key, recipient = self.u2, expected_count = 1)

        #post another exercise and check that there are no new badges
        exercise2 = self.post_exercise(user = self.u1)
        problem2 = self.post_problem(user = self.u2, exercise = exercise2)
        problem2.score = min_points - 1
        problem2.save()
        self.u1.upvote(problem2)

        if multiple == True:
            expected_count = 2
        else:
            expected_count = 1

        self.assert_have_badge(
                badge_key,
                recipient = self.u2,
                expected_count = expected_count
            )

    def assert_upvoted_exercise_badge_works(self,
                                    badge_key = None,
                                    min_points = None,
                                    multiple = False
                                ):
        """test exercise badge where exercise author is the recipient
        where badge award is triggered by upvotes
        * min_points - minimum # of upvotes required
        * multiple - multiple award or not
        * badge_key - key on askbot.models.badges.Badge object
        """
        exercise = self.post_exercise(user = self.u1)
        exercise.points = min_points - 1
        exercise.save()
        self.u2.upvote(exercise)
        self.assert_have_badge(badge_key, recipient = self.u1)
        self.u3.upvote(exercise)
        self.assert_have_badge(badge_key, recipient = self.u1, expected_count = 1)

        #post another exercise and check that there are no new badges
        exercise2 = self.post_exercise(user = self.u1)
        exercise2.points = min_points - 1
        exercise2.save()
        self.u2.upvote(exercise2)

        if multiple == True:
            expected_count = 2
        else:
            expected_count = 1

        self.assert_have_badge(
                        badge_key,
                        recipient = self.u1,
                        expected_count = expected_count
                    )

    def test_disciplined_badge(self):
        exercise = self.post_exercise(user = self.u1)
        exercise.points = settings.DISCIPLINED_BADGE_MIN_UPVOTES
        exercise.save()
        self.u1.delete_exercise(exercise)
        self.assert_have_badge('disciplined', recipient = self.u1)

        exercise2 = self.post_exercise(user = self.u1)
        exercise2.points = settings.DISCIPLINED_BADGE_MIN_UPVOTES
        exercise2.save()
        self.u1.delete_exercise(exercise2)
        self.assert_have_badge('disciplined', recipient = self.u1, expected_count = 2)

    def test_peer_pressure_badge(self):
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u1, exercise = exercise)
        problem.points = -1*settings.PEER_PRESSURE_BADGE_MIN_DOWNVOTES
        problem.save()
        self.u1.delete_problem(problem)
        self.assert_have_badge('peer-pressure', recipient = self.u1)

    def test_teacher_badge(self):
        self.assert_upvoted_problem_badge_works(
            badge_key = 'teacher',
            min_points = settings.TEACHER_BADGE_MIN_UPVOTES,
            multiple = False
        )

    def test_nice_problem_badge(self):
        self.assert_upvoted_problem_badge_works(
            badge_key = 'nice-problem',
            min_points = settings.NICE_PROBLEM_BADGE_MIN_UPVOTES,
            multiple = True
        )

    def test_nice_exercise_badge(self):
        self.assert_upvoted_exercise_badge_works(
            badge_key = 'nice-exercise',
            min_points = settings.NICE_EXERCISE_BADGE_MIN_UPVOTES,
            multiple = True
        )

    def test_popular_exercise_badge(self):
        exercise = self.post_exercise(user = self.u1)
        min_views = settings.POPULAR_EXERCISE_BADGE_MIN_VIEWS
        exercise.thread.view_count = min_views - 1
        exercise.thread.save()

        #patch not_a_robot_request to return True
        from askbot.utils import functions
        functions.not_a_robot_request = lambda v: True

        url = exercise.get_absolute_url()

        self.client.login(method='force', user_id = self.u2.id)
        self.client.get(url)
        self.assert_have_badge('popular-exercise', recipient = self.u1)

        self.client.login(method='force', user_id = self.u3.id)
        self.client.get(url)
        self.assert_have_badge('popular-exercise', recipient = self.u1, expected_count = 1)

        exercise2 = self.post_exercise(user = self.u1)
        exercise2.thread.view_count = min_views - 1
        exercise2.thread.save()
        self.client.login(method='force', user_id = self.u2.id)
        self.client.get(exercise2.get_absolute_url())
        self.assert_have_badge('popular-exercise', recipient = self.u1, expected_count = 2)

    def test_student_badge(self):
        exercise = self.post_exercise(user = self.u1)
        self.u2.upvote(exercise)
        self.assert_have_badge('student', recipient = self.u1)
        self.u3.upvote(exercise)
        self.assert_have_badge('student', recipient = self.u1, expected_count = 1)

        exercise2 = self.post_exercise(user = self.u1)
        self.u2.upvote(exercise)
        self.assert_have_badge('student', recipient = self.u1, expected_count = 1)

    def test_supporter_badge(self):
        exercise = self.post_exercise(user = self.u1)
        self.u2.upvote(exercise)
        self.assert_have_badge('supporter', recipient = self.u2)

        problem = self.post_problem(user = self.u1, exercise = exercise)
        self.u3.upvote(problem)
        self.assert_have_badge('supporter', recipient = self.u3)
        self.u2.upvote(problem)
        self.assert_have_badge('supporter', recipient = self.u2, expected_count = 1)

    def test_critic_badge(self):
        exercise = self.post_exercise(user = self.u1)
        self.u2.downvote(exercise)
        self.assert_have_badge('critic', recipient = self.u2)

        problem = self.post_problem(user = self.u1, exercise = exercise)
        self.u3.downvote(problem)
        self.assert_have_badge('critic', recipient = self.u3)
        self.u2.downvote(problem)
        self.assert_have_badge('critic', recipient = self.u2, expected_count = 1)

    def test_self_learner_badge(self):
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u1, exercise = exercise)
        min_votes = settings.SELF_LEARNER_BADGE_MIN_UPVOTES
        problem.points = min_votes - 1
        problem.save()
        self.u2.upvote(problem)
        self.assert_have_badge('self-learner', recipient = self.u1)

        #copy-paste of the first exercise, except expect second badge
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u1, exercise = exercise)
        problem.points = min_votes - 1
        problem.save()
        self.u2.upvote(problem)
        self.assert_have_badge('self-learner', recipient = self.u1, expected_count = 2)

        exercise = self.post_exercise(user = self.u2)
        problem = self.post_problem(user = self.u1, exercise = exercise)
        problem.points = min_votes - 1
        problem.save()
        self.u2.upvote(problem)
        #no badge when asker != problemer
        self.assert_have_badge(
            'self-learner',
            recipient = self.u1,
            expected_count = 2
        )

    def test_civic_duty_badge(self):
        settings.update('CIVIC_DUTY_BADGE_MIN_VOTES', 2)
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u2, exercise = exercise)
        problem2 = self.post_problem(user = self.u1, exercise = exercise)
        self.u3.upvote(exercise)
        self.u3.downvote(problem)
        self.assert_have_badge('civic-duty', recipient = self.u3)
        self.u3.upvote(problem2)
        self.assert_have_badge('civic-duty', recipient = self.u3, expected_count = 1)
        self.u3.downvote(problem)
        self.assert_have_badge('civic-duty', recipient = self.u3, expected_count = 1)

    def test_scholar_badge(self):
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u2, exercise = exercise)
        self.u1.accept_best_problem(problem)
        self.assert_have_badge('scholar', recipient = self.u1)
        exercise2 = self.post_exercise(user = self.u1)
        problem2 = self.post_problem(user = self.u2, exercise = exercise2)
        self.u1.accept_best_problem(problem2)
        self.assert_have_badge(
            'scholar',
            recipient = self.u1,
            expected_count=1
        )

    def assert_enlightened_badge_works(self, trigger):
        self.assert_accepted_problem_badge_works(
            'enlightened',
            min_points = settings.ENLIGHTENED_BADGE_MIN_UPVOTES,
            expected_count = 1,
            trigger = trigger
        )
        self.assert_accepted_problem_badge_works(
            'enlightened',
            min_points = settings.ENLIGHTENED_BADGE_MIN_UPVOTES,
            expected_count = 1,
            previous_count = 1,
            trigger = trigger
        )

    def assert_guru_badge_works(self, trigger):
        self.assert_accepted_problem_badge_works(
            'guru',
            min_points = settings.GURU_BADGE_MIN_UPVOTES,
            expected_count = 1,
            trigger = trigger
        )
        self.assert_accepted_problem_badge_works(
            'guru',
            min_points = settings.GURU_BADGE_MIN_UPVOTES,
            previous_count = 1,
            expected_count = 2,
            trigger = trigger
        )

    def test_enlightened_badge1(self):
        self.assert_enlightened_badge_works('upvote_problem')

    def test_enlightened_badge2(self):
        self.assert_enlightened_badge_works('accept_best_problem')

    def test_guru_badge1(self):
        self.assert_guru_badge_works('upvote_problem')

    def test_guru_badge2(self):
        self.assert_guru_badge_works('accept_best_problem')

    def test_necromancer_badge(self):
        exercise = self.post_exercise(user = self.u1)
        now = datetime.datetime.now()
        delta = datetime.timedelta(settings.NECROMANCER_BADGE_MIN_DELAY + 1)
        future = now + delta
        problem = self.post_problem(
                        user = self.u2,
                        exercise = exercise,
                        timestamp = future
                    )
        problem.points = settings.NECROMANCER_BADGE_MIN_UPVOTES - 1
        problem.save()
        self.assert_have_badge('necromancer', self.u2, expected_count = 0)
        self.u1.upvote(problem)
        self.assert_have_badge('necromancer', self.u2, expected_count = 1)

    def test_citizen_patrol_exercise(self):
        self.u2.set_status('m')
        exercise = self.post_exercise(user = self.u1)
        self.u2.flag_post(exercise)
        self.assert_have_badge('citizen-patrol', self.u2)
        exercise = self.post_exercise(user = self.u1)
        self.u2.flag_post(exercise)
        self.assert_have_badge('citizen-patrol', self.u2, 1)

    def test_citizen_patrol_problem(self):
        self.u2.set_status('m')
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u1, exercise = exercise)
        self.u2.flag_post(problem)
        self.assert_have_badge('citizen-patrol', self.u2)
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u1, exercise = exercise)
        self.u2.flag_post(problem)
        self.assert_have_badge('citizen-patrol', self.u2, 1)

    def test_editor_badge_exercise(self):
        self.u2.set_status('m')
        exercise = self.post_exercise(user = self.u1)
        self.u2.edit_exercise(
            exercise = exercise,
            title = 'hahaha',
            body_text = 'heheeh',
            revision_comment = 'ihihih'
        )
        self.assert_have_badge('editor', self.u2, 1)
        #double check that its not multiple
        exercise = self.post_exercise(user = self.u1)
        self.u2.edit_exercise(
            exercise = exercise,
            title = 'hahaha',
            body_text = 'heheeh',
            revision_comment = 'ihihih'
        )
        self.assert_have_badge('editor', self.u2, 1)

    def test_editor_badge_problem(self):
        self.u2.set_status('m')
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u1, exercise = exercise)
        self.u2.edit_problem(problem = problem, body_text = 'hahaha')
        self.assert_have_badge('editor', self.u2, 1)
        #double check that its not multiple
        exercise = self.post_exercise(user = self.u1)
        problem = self.post_problem(user = self.u1, exercise = exercise)
        self.u2.edit_problem(problem = problem, body_text = 'hahaha')
        self.assert_have_badge('editor', self.u2, 1)

    def test_associate_editor_badge(self):
        self.u2.set_status('m')
        exercise = self.post_exercise(user = self.u1)
        settings.update('ASSOCIATE_EDITOR_BADGE_MIN_EDITS', 2)
        self.u2.edit_exercise(
            exercise = exercise,
            title = 'hahaha',
            body_text = 'sdgsdjghsldkfshd',
            revision_comment = 'sdgdfgsgfs'
        )
        self.assert_have_badge('strunk-and-white', self.u2, 0)
        self.u2.edit_exercise(
            exercise = exercise,
            title = 'hahaha',
            body_text = 'sdgsdjghsldkfshd',
            revision_comment = 'sdgdfgsgfs'
        )
        self.assert_have_badge('strunk-and-white', self.u2, 1)
        self.u2.edit_exercise(
            exercise = exercise,
            title = 'hahaha',
            body_text = 'sdgsdjghsldkfshd',
            revision_comment = 'sdgdfgsgfs'
        )
        self.assert_have_badge('strunk-and-white', self.u2, 1)

    def test_organizer_badge(self):
        exercise = self.post_exercise(user = self.u1)
        self.u1.retag_exercise(exercise = exercise, tags = 'blah boom')
        self.assert_have_badge('organizer', self.u1, 1)
        self.u1.retag_exercise(exercise = exercise, tags = 'blah pooh')
        self.assert_have_badge('organizer', self.u1, 1)

    def test_autobiographer_badge(self):
        self.u1.real_name = 'blah'
        self.u1.website = 'cnn.com'
        self.u1.location = 'irvine'
        self.u1.about = 'blah'
        self.u1.save()
        award_badges_signal.send(None,
            event = 'update_user_profile',
            actor = self.u1,
            context_object = self.u1
        )
        self.assert_have_badge('autobiographer', self.u1, 1)
        award_badges_signal.send(None,
            event = 'update_user_profile',
            actor = self.u1,
            context_object = self.u1
        )
        self.assert_have_badge('autobiographer', self.u1, 1)

    def test_stellar_badge1(self):
        exercise = self.post_exercise(user = self.u1)
        settings.update('STELLAR_EXERCISE_BADGE_MIN_STARS', 2)
        self.u2.toggle_favorite_exercise(exercise)
        self.assert_have_badge('stellar-exercise', self.u1, 0)
        self.u3.toggle_favorite_exercise(exercise)
        self.assert_have_badge('stellar-exercise', self.u1, 1)

    def test_stellar_badge2(self):
        exercise = self.post_exercise(user = self.u1)
        settings.update('STELLAR_EXERCISE_BADGE_MIN_STARS', 2)
        self.u2.toggle_favorite_exercise(exercise)
        self.assert_have_badge('stellar-exercise', self.u1, 0)
        self.u1.toggle_favorite_exercise(exercise)
        """no gaming"""
        self.assert_have_badge('stellar-exercise', self.u1, 0)

    def test_stellar_badge3(self):
        exercise = self.post_exercise(user = self.u1)
        settings.update('STELLAR_EXERCISE_BADGE_MIN_STARS', 2)
        self.u2.toggle_favorite_exercise(exercise)
        self.assert_have_badge('stellar-exercise', self.u1, 0)
        self.u3.toggle_favorite_exercise(exercise)
        #award now
        self.assert_have_badge('stellar-exercise', self.u1, 1)
        self.u3.toggle_favorite_exercise(exercise)
        #dont take back
        self.assert_have_badge('stellar-exercise', self.u1, 1)
        self.u3.toggle_favorite_exercise(exercise)
        #dont reaward
        self.assert_have_badge('stellar-exercise', self.u1, 1)

    def test_commentator_badge(self):
        exercise = self.post_exercise(user = self.u1)
        min_comments = settings.COMMENTATOR_BADGE_MIN_COMMENTS
        for i in xrange(min_comments - 1):
            self.post_comment(user = self.u1, parent_post = exercise)

        self.assert_have_badge('commentator', self.u1, 0)
        self.post_comment(user = self.u1, parent_post = exercise)
        self.assert_have_badge('commentator', self.u1, 1)
        self.post_comment(user = self.u1, parent_post = exercise)
        self.assert_have_badge('commentator', self.u1, 1)

    def test_taxonomist_badge(self):
        self.post_exercise(user = self.u1, tags = 'test')
        min_use = settings.TAXONOMIST_BADGE_MIN_USE_COUNT
        for i in xrange(min_use - 2):
            self.post_exercise(user = self.u2, tags = 'test')
        self.assert_have_badge('taxonomist', self.u1, 0)
        self.post_exercise(user = self.u2, tags = 'test')
        self.assert_have_badge('taxonomist', self.u1, 1)

    def test_enthusiast_badge(self):
        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        self.u1.last_seen = yesterday
        prev_visit_count = settings.ENTHUSIAST_BADGE_MIN_DAYS - 1
        self.u1.consecutive_days_visit_count = prev_visit_count
        self.u1.save()
        self.assert_have_badge('enthusiast', self.u1, 0)
        self.client.login(method = 'force', user_id = self.u1.id)
        self.client.get('/' + django_settings.ASKBOT_URL)
        self.assert_have_badge('enthusiast', self.u1, 1)

