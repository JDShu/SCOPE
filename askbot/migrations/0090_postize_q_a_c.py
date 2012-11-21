# encoding: utf-8
import datetime
import sys
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.conf import settings
from askbot.utils.console import ProgressBar

from askbot.migrations import TERM_RED_BOLD, TERM_GREEN, TERM_RESET

class Migration(DataMigration):

    def forwards(self, orm):
        orm.Post.objects.all().delete() # in case there are some leftovers after this migration failed before

        if 'test' not in sys.argv: # Don't confuse users
            print TERM_RED_BOLD, "!!! Remember to not remove the old content types for Exercise, Problem and Comment models until further notice from migration 0101!", TERM_RESET

        post_id = max(
            # 'or 0' protects against None
            orm.Exercise.objects.aggregate(max_id=models.Max('id'))['max_id'] or 0,
            orm.Problem.objects.aggregate(max_id=models.Max('id'))['max_id'] or 0,
            orm.Comment.objects.aggregate(max_id=models.Max('id'))['max_id'] or 0,
        )

        if 'test' not in sys.argv: # Don't confuse users
            print TERM_GREEN, '[DEBUG] Initial Post.id ==', post_id + 1, TERM_RESET

        message = "Converting Exercises -> Posts"
        num_exercises = orm.Exercise.objects.count()
        for q in ProgressBar(orm.Exercise.objects.iterator(), num_exercises, message):
            post_id += 1
            orm.Post.objects.create(
                id=post_id,

                post_type='exercise',

                old_problem_id=None,
                old_exercise_id=q.id,
                old_comment_id=None,

                self_problem=None,
                self_exercise=q,
                self_comment=None,

                thread=q.thread,
                parent=None,

                author=q.author,
                added_at=q.added_at,
                deleted=q.deleted,
                deleted_at=q.deleted_at,
                deleted_by=q.deleted_by,
                wiki=q.wiki,
                wikified_at=q.wikified_at,
                locked=q.locked,
                locked_by=q.locked_by,
                locked_at=q.locked_at,
                score=q.score,
                vote_up_count=q.vote_up_count,
                vote_down_count=q.vote_down_count,
                comment_count=q.comment_count,
                offensive_flag_count=q.offensive_flag_count,
                last_edited_at=q.last_edited_at,
                last_edited_by=q.last_edited_by,
                html=q.html,
                text=q.text,
                summary=q.summary,
                is_anonymous=q.is_anonymous,
            )

        message = "Problems -> Posts"
        num_problems = orm.Problem.objects.count()
        for ans in ProgressBar(orm.Problem.objects.iterator(), num_problems, message):
            post_id += 1
            orm.Post.objects.create(
                id=post_id,

                post_type='problem',

                old_problem_id=ans.id,
                old_exercise_id=None,
                old_comment_id=None,

                self_problem=ans,
                self_exercise=None,
                self_comment=None,

                thread=ans.exercise.thread,
                parent=None,

                author=ans.author,
                added_at=ans.added_at,
                deleted=ans.deleted,
                deleted_at=ans.deleted_at,
                deleted_by=ans.deleted_by,
                wiki=ans.wiki,
                wikified_at=ans.wikified_at,
                locked=ans.locked,
                locked_by=ans.locked_by,
                locked_at=ans.locked_at,
                score=ans.score,
                vote_up_count=ans.vote_up_count,
                vote_down_count=ans.vote_down_count,
                comment_count=ans.comment_count,
                offensive_flag_count=ans.offensive_flag_count,
                last_edited_at=ans.last_edited_at,
                last_edited_by=ans.last_edited_by,
                html=ans.html,
                text=ans.text,
                summary=ans.summary,
                is_anonymous=ans.is_anonymous,
            )

        message = "Comments -> Posts"
        num_comments = orm.Comment.objects.count()
        for cm in ProgressBar(orm.Comment.objects.iterator(), num_comments, message):
            # Workaround for a strange issue with: http://south.aeracode.org/docs/generics.html
            # No need to investigate that as this is as simple as the "proper" way
            if (cm.content_type.app_label, cm.content_type.model) == ('askbot', 'exercise'):
                content_object = orm.Exercise.objects.get(id=cm.object_id)
                thread = orm.Thread.objects.get(id=content_object.thread.id) # convert from Thread to orm.Thread - a subtle difference
                parent = orm.Post.objects.get(self_exercise=content_object)
            elif (cm.content_type.app_label, cm.content_type.model) == ('askbot', 'problem'):
                content_object = orm.Problem.objects.get(id=cm.object_id)
                thread = orm.Thread.objects.get(id=content_object.exercise.thread.id) # convert from Thread to orm.Thread - a subtle difference
                parent = orm.Post.objects.get(self_problem=content_object)
            else:
                raise ValueError('comment.content_object is neither exercise nor problem!')

            post_id += 1
            orm.Post.objects.create(
                id=post_id,

                post_type='comment',

                old_problem_id=None,
                old_exercise_id=None,
                old_comment_id=cm.id,

                self_problem=None,
                self_exercise=None,
                self_comment=cm,

                thread=thread,
                parent=parent,

                author=cm.user,
                added_at=cm.added_at,
                deleted=False,
                deleted_at=None,
                deleted_by=None,
                wiki=False,
                wikified_at=None,
                locked=False,
                locked_by=None,
                locked_at=None,
                score=cm.score,
                vote_up_count=cm.score,
                vote_down_count=0,
                comment_count=0,
                offensive_flag_count=cm.offensive_flag_count,
                last_edited_at=None,
                last_edited_by=None,
                html=cm.html,
                text=cm.comment,
                summary='',
                is_anonymous=False,
            )

        if orm.Post.objects.exists():
            # Check Post.id sequence/auto-increment to make sure new Post-s don't start from id=1
            if db.backend_name == 'mysql':
                # Docs:
                # - http://stackoverflow.com/exercises/933565/get-auto-increment-value-with-mysql-query
                # -
                autoincrement = db.execute("SELECT auto_increment FROM information_schema.tables WHERE table_name='askbot_post' AND table_schema=DATABASE()")[0][0]

            elif db.backend_name == 'sqlite3':
                # Docs:
                # - http://www.sqlite.org/autoinc.html
                # - http://www.sqlite.org/c3ref/last_insert_rowid.html
                # - http://www.sqlite.org/faq.html#q1
                # - http://stackoverflow.com/exercises/531109/how-to-return-the-value-of-auto-increment-column-in-sqlite-with-vb6
                autoincrement = db.execute("SELECT last_insert_rowid() FROM askbot_post")[0][0] + 1

            elif db.backend_name == 'postgres':
                # Docs:
                # - http://lindsaar.net/2008/11/2/how-to-reset-a-sequence-with-postgresql
                # - http://www.postgresql.org/docs/8.3/static/functions-sequence.html
                # Note that SELECT SETVAL(...) returns the value being set
                autoincrement = db.execute("SELECT SETVAL('askbot_post_id_seq', %s)", params=[post_id + 1])[0][0]

            else:
                autoincrement = -1
                print TERM_RED_BOLD, ("You are using `%s` database backend which is not officially supported. "
                            "Therefore after migrations are applied you should make sure that autoincrement/sequence value for "
                            "table `askbot_post` is set to %d") % (db.backend_name, post_id + 1), TERM_RESET

            if autoincrement != -1:
                if autoincrement != (post_id + 1):
                    raise ValueError('Auto_increment for askbot_post table should be %d but is %d!' % (post_id + 1, autoincrement))
                print TERM_GREEN, '[DEBUG] %s: auto-increment/sequence-value for askbot_post table is OK (%d)' % (
                        db.backend_name, autoincrement), TERM_RESET

        # Verify that numbers match
        sum_all = orm.Exercise.objects.count() + orm.Problem.objects.count() + orm.Comment.objects.count()
        if sum_all != orm.Post.objects.count():
            raise ValueError('sum(#Q,#C,#A) != #Post !')


    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'askbot.activity': {
            'Meta': {'object_name': 'Activity', 'db_table': "u'activity'"},
            'active_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'activity_type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_auditted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Exercise']", 'null': 'True'}),
            'receiving_users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'received_activity'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'incoming_activity'", 'symmetrical': 'False', 'through': "orm['askbot.ActivityAuditStatus']", 'to': "orm['auth.User']"}),
            'summary': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'askbot.activityauditstatus': {
            'Meta': {'unique_together': "(('user', 'activity'),)", 'object_name': 'ActivityAuditStatus'},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Activity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'askbot.anonymousproblem': {
            'Meta': {'object_name': 'AnonymousProblem'},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'anonymous_problems'", 'to': "orm['askbot.Exercise']"}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'askbot.anonymousexercise': {
            'Meta': {'object_name': 'AnonymousExercise'},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'is_anonymous': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'askbot.problem': {
            'Meta': {'object_name': 'Problem', 'db_table': "u'problem'"},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['auth.User']"}),
            'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
            'html': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_anonymous': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
            'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['askbot.Exercise']"}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'askbot.award': {
            'Meta': {'object_name': 'Award', 'db_table': "u'award'"},
            'awarded_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'badge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_badge'", 'to': "orm['askbot.BadgeData']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_user'", 'to': "orm['auth.User']"})
        },
        'askbot.badgedata': {
            'Meta': {'ordering': "('slug',)", 'object_name': 'BadgeData'},
            'awarded_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'awarded_to': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'badges'", 'symmetrical': 'False', 'through': "orm['askbot.Award']", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'askbot.comment': {
            'Meta': {'ordering': "('-added_at',)", 'object_name': 'Comment', 'db_table': "u'comment'"},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'html': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2048'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'offensive_flag_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': "orm['auth.User']"})
        },
        'askbot.emailfeedsetting': {
            'Meta': {'object_name': 'EmailFeedSetting'},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feed_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'frequency': ('django.db.models.fields.CharField', [], {'default': "'n'", 'max_length': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'notification_subscriptions'", 'to': "orm['auth.User']"})
        },
        'askbot.favoriteexercise': {
            'Meta': {'object_name': 'FavoriteExercise', 'db_table': "u'favorite_exercise'"},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Thread']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_favorite_exercises'", 'to': "orm['auth.User']"})
        },
        'askbot.markedtag': {
            'Meta': {'object_name': 'MarkedTag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_selections'", 'to': "orm['askbot.Tag']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tag_selections'", 'to': "orm['auth.User']"})
        },
        'askbot.post': {
            'Meta': {'object_name': 'Post'},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['auth.User']"}),
            'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_posts'", 'null': 'True', 'to': "orm['auth.User']"}),
            'html': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_anonymous': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_posts'", 'null': 'True', 'to': "orm['auth.User']"}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_posts'", 'null': 'True', 'to': "orm['auth.User']"}),
            'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'comment_posts'", 'null': 'True', 'to': "orm['askbot.Post']"}),
            'post_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'self_problem': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['askbot.Problem']"}),
            'self_comment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['askbot.Comment']"}),
            'self_exercise': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['askbot.Exercise']"}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['askbot.Thread']"}),
            'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),

            # "Post-processing" - added manually to add support for URL mapping
            'old_exercise_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': True, 'blank': True, 'default': None, 'unique': 'True'}),
            'old_problem_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': True, 'blank': True, 'default': None, 'unique': 'True'}),
            'old_comment_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': True, 'blank': True, 'default': None, 'unique': 'True'}),
        },
        'askbot.postrevision': {
            'Meta': {'ordering': "('-revision',)", 'unique_together': "(('problem', 'revision'), ('exercise', 'revision'))", 'object_name': 'PostRevision'},
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'revisions'", 'null': 'True', 'to': "orm['askbot.Problem']"}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'postrevisions'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_anonymous': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'exercise': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'revisions'", 'null': 'True', 'to': "orm['askbot.Exercise']"}),
            'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
            'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'revision_type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'tagnames': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '125', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '300', 'blank': 'True'})
        },
        'askbot.exercise': {
            'Meta': {'object_name': 'Exercise', 'db_table': "u'exercise'"},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercises'", 'to': "orm['auth.User']"}),
            'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
            'html': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_anonymous': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
            'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
            'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'thread': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercises'", 'unique': 'True', 'to': "orm['askbot.Thread']"}),
            'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'askbot.exerciseview': {
            'Meta': {'object_name': 'ExerciseView'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'viewed'", 'to': "orm['askbot.Exercise']"}),
            'when': ('django.db.models.fields.DateTimeField', [], {}),
            'who': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercise_views'", 'to': "orm['auth.User']"})
        },
        'askbot.repute': {
            'Meta': {'object_name': 'Repute', 'db_table': "u'repute'"},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negative': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'positive': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Exercise']", 'null': 'True', 'blank': 'True'}),
            'reputation': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'reputation_type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'reputed_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'askbot.tag': {
            'Meta': {'ordering': "('-used_count', 'name')", 'object_name': 'Tag', 'db_table': "u'tag'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_tags'", 'to': "orm['auth.User']"}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_tags'", 'null': 'True', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'used_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'askbot.thread': {
            'Meta': {'object_name': 'Thread'},
            'accepted_problem': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Problem']", 'null': 'True', 'blank': 'True'}),
            'problem_accepted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'problem_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'close_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'closed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'closed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'favorited_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'unused_favorite_threads'", 'symmetrical': 'False', 'through': "orm['askbot.FavoriteExercise']", 'to': "orm['auth.User']"}),
            'favourite_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'followed_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'followed_threads'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_activity_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_activity_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'unused_last_active_in_threads'", 'to': "orm['auth.User']"}),
            'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'threads'", 'symmetrical': 'False', 'to': "orm['askbot.Tag']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'view_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'askbot.vote': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'Vote', 'db_table': "u'vote'"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['auth.User']"}),
            'vote': ('django.db.models.fields.SmallIntegerField', [], {}),
            'voted_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'about': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'avatar_type': ('django.db.models.fields.CharField', [], {'default': "'n'", 'max_length': '1'}),
            'bronze': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'consecutive_days_visit_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'display_tag_filter_strategy': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'email_isvalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'email_tag_filter_strategy': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'gold': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'gravatar': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored_tags': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'interesting_tags': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'new_response_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'exercises_per_page': ('django.db.models.fields.SmallIntegerField', [], {'default': '10'}),
            'real_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'reputation': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'seen_response_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'show_country': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'silver': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'w'", 'max_length': '2'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['askbot']
