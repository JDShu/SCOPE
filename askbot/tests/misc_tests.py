from askbot.tests.utils import AskbotTestCase
from askbot.models.post import PostRevision

from django.test.client import Client
from django.core.urlresolvers import reverse

class MiscTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u2 = self.create_user(username='user2')
        self.u3 = self.create_user(username='user3')

    def test_proper_PostRevision_manager_is_used(self):
        "Makes sure that both normal and related managers for PostRevision don't implement .create() method"
        exercise = self.post_exercise(user=self.u1)
        self.assertRaises(NotImplementedError, exercise.revisions.create)
        self.assertRaises(NotImplementedError, PostRevision.objects.create)

class ContentConvertionTests(AskbotTestCase):

    def setUp(self):
        self.u1 = self.create_user(username='user1')
        self.u1.set_password('password')
        self.u1.set_admin_status()
        self.u1.save()
        self.u2 = self.create_user(username='notadmin')
        self.client = Client()

        #content
        self.exercise = self.post_exercise(user=self.u1)
        self.problem_to_convert = self.post_problem(user=self.u2,
                                                  exercise=self.exercise)
        self.comment_on_problem = self.post_comment(user=self.u1,
                                                   parent_post=self.problem_to_convert)
        self.another_problem = self.post_problem(user=self.u1,
                                               exercise=self.exercise)
        self.comment_to_convert = self.post_comment(user=self.u1,
                                                    parent_post=self.another_problem)

    def test_convert_comment_to_problem(self):
        self.client.login(username='user1', password='password')
        old_parent_comment_count = self.another_problem.comment_count
        problem_count = self.exercise.thread.problem_count
        self.client.post(reverse('comment_to_problem'),
                         {'comment_id': self.comment_to_convert.id})
        converted_problem = self.reload_object(self.comment_to_convert)
        #old_parent = self.another_problem
        old_parent = self.reload_object(self.another_problem)

        #test for convertion
        self.assertEquals(converted_problem.post_type, 'problem')
        #test for parent change
        self.assertNotEquals(old_parent.id, converted_problem.parent.id)
        #test for problem count update
        self.assertEquals(converted_problem.thread.problem_count, problem_count + 1)
        #test for comment count update
        self.assertEquals(old_parent.comment_count, old_parent_comment_count - 1)

        #test the delete post view for errors
        response = self.client.post(reverse('delete_post'),
                                    {'post_id': converted_problem.id,
                                     'cancel_vote': 'false'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        self.assertTrue('is_deleted' in response.content)

    def test_convert_problem_to_comment(self):
        comment_count = self.exercise.comment_count
        #because the problem itself has a comment too!
        comment_count += self.problem_to_convert.comment_count

        problem_count = self.exercise.thread.problem_count
        self.client.login(username='user1', password='password')
        self.client.post(reverse('problem_to_comment'),
                         {'problem_id': self.problem_to_convert.id})
        converted_comment = self.reload_object(self.problem_to_convert)
        old_parent = self.reload_object(self.exercise)

        #test for convertion
        self.assertEquals(converted_comment.post_type, 'comment')
        #test for problem count update
        self.assertEquals(converted_comment.thread.problem_count, problem_count - 1)
        #test for comment count update
        self.assertEquals(old_parent.comment_count, comment_count + 1)

        #test the delete comment view for errors
        response = self.client.post(reverse('delete_comment'),
                                    {'comment_id': converted_comment.id},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
