from askbot.tests.utils import AskbotTestCase
from askbot.conf import settings as askbot_settings
from askbot import models
from askbot.models.tag import get_global_group
import django.core.mail
from django.core.urlresolvers import reverse

class ThreadModelTestsWithGroupsEnabled(AskbotTestCase):
    
    def setUp(self):
        self.groups_enabled_backup = askbot_settings.GROUPS_ENABLED
        askbot_settings.update('GROUPS_ENABLED', True)
        self.admin = self.create_user('admin', status = 'd')
        self.user = self.create_user(
            'user',
            notification_schedule = {
                'q_ask': 'i',
                'q_all': 'i',
                'q_ans': 'i',
                'q_sel': 'i',
                'm_and_c': 'i'
            }
        )
        self.group = models.Group.objects.get_or_create(name='jockeys')
        self.admin.edit_group_membership(
            group = self.group,
            user = self.admin,
            action = 'add'
        )

    def tearDown(self):
        askbot_settings.update('GROUPS_ENABLED', self.groups_enabled_backup)

    def test_private_problem(self):
        # post exercise, problem, add problem to the group
        self.exercise = self.post_exercise(self.user)

        self.problem = self.post_problem(
            user = self.admin,
            exercise = self.exercise,
            is_private = True
        )

        thread = self.exercise.thread

        #test problem counts
        self.assertEqual(thread.get_problem_count(self.user), 0)
        self.assertEqual(thread.get_problem_count(self.admin), 1)

        #test mail outbox
        self.assertEqual(len(django.core.mail.outbox), 0)
        user = self.reload_object(self.user)
        self.assertEqual(user.new_response_count, 0)

        self.admin.edit_problem(
            self.problem,
            is_private = False
        )
        self.assertEqual(len(django.core.mail.outbox), 1)
        user = self.reload_object(self.user)
        self.assertEqual(user.new_response_count, 1)

    def test_problem_to_private_exercise_is_not_globally_visible(self):
        exercise = self.post_exercise(user=self.admin, is_private=True)
        problem = self.post_problem(exercise=exercise, user=self.admin, is_private=False)
        global_group = get_global_group()
        self.assertEqual(
            global_group in set(problem.groups.all()),
            False
        )

    def test_problem_to_group_exercise_is_not_globally_visible(self):
        #ask into group where user is not a member
        exercise = self.post_exercise(user=self.user, group_id=self.group.id)
        #problem posted by a group member
        problem = self.post_problem(exercise=exercise, user=self.admin, is_private=False)
        global_group = get_global_group()
        self.assertEqual(
            global_group in set(problem.groups.all()),
            False
        )


    def test_restrictive_response_publishing(self):
        #restrictive model should work even with groups
        #in common between the asker and the problemer
        common_group = models.Group(
                        name='common',
                        openness=models.Group.OPEN
                    )
        common_group.save()
        self.admin.join_group(common_group)
        self.user.join_group(common_group)

        self.group.moderate_problems_to_enquirers = True
        self.group.save()
        exercise = self.post_exercise(user=self.user, group_id=self.group.id)
        problem = self.post_problem(exercise=exercise, user=self.admin)

        #problem and the user don't have groups in common
        problem_groups = set(problem.groups.all())
        user_groups = set(self.user.get_groups())
        self.assertEqual(len(problem_groups & user_groups), 0)

        #publish the problem
        self.client.login(user_id=self.admin.id, method='force')
        self.client.post(
            reverse('publish_problem'),
            data={'problem_id': problem.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest' 
        )
        #todo: test redirect

        problem = self.reload_object(problem)
        problem_groups = set(problem.groups.all())
        self.assertEqual(len(problem_groups & user_groups), 1)



    def test_permissive_response_publishing(self):
        self.group.moderate_problems_to_enquirers = False
        self.group.save()
        exercise = self.post_exercise(user=self.user, group_id=self.group.id)
        problem = self.post_problem(exercise=exercise, user=self.admin)

        #problem and user have one group in common
        problem_groups = set(problem.groups.all())
        user_groups = set(self.user.get_groups())
        self.assertEqual(len(problem_groups & user_groups), 1)
