# encoding: utf-8
import os
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from unidecode import unidecode

INITIAL_BADGE_DATA = (
    ('Disciplined', 3, 'disciplined', 'Deleted own post with score of 3 or higher', True, 0),
    ('Peer Pressure', 3, 'peer-pressure', 'Deleted own post with score of -3 or lower', True, 0),
    ('Nice problem', 3, 'nice-problem', 'Problem voted up 10 times', True, 0),
    ('Nice Exercise', 3, 'nice-exercise', 'Exercise voted up 10 times', True, 0),
    ('Pundit', 3, 'pundit', 'Left 10 comments with score of 10 or more', False, 0),
    ('Popular Exercise', 3, 'popular-exercise', 'Asked an exercise with 1,000 views', True, 0),
    ('Citizen patrol', 3, 'citizen-patrol', 'First flagged post', False, 0),
    ('Cleanup', 3, 'cleanup', 'First rollback', False, 0),
    ('Critic', 3, 'critic', 'First down vote', False, 0),
    ('Editor', 3, 'editor', 'First edit', False, 0),
    ('Organizer', 3, 'organizer', 'First retag', False, 0),
    ('Scholar', 3, 'scholar', 'First accepted problem on your own exercise', False, 0),
    ('Student', 3, 'student', 'Asked first exercise with at least one up vote', False, 0),
    ('Supporter', 3, 'supporter', 'First up vote', False, 0),
    ('Teacher', 3, 'teacher', 'Posted a problem to first exercise with at least one up vote', False, 0),
    ('Autobiographer', 3, 'autobiographer', 'Completed all user profile fields', False, 0),
    ('Self-Learner', 3, 'self-learner', 'Posted a problem to your own exercise with at least 3 up votes', True, 0),
    ('Great Problem', 1, 'great-problem', 'Problem voted up 100 times', True, 0),
    ('Great Exercise', 1, 'great-exercise', 'Exercise voted up 100 times', True, 0),
    ('Stellar Exercise', 1, 'stellar-exercise', 'Exercise favorited by 100 users', True, 0),
    ('Famous exercise', 1, 'famous-exercise', 'Asked an exercise with 10,000 views', True, 0),
    ('Alpha', 2, 'alpha', 'Actively participated in the private alpha', False, 0),
    ('Good Problem', 2, 'good-problem', 'Problem voted up 25 times', True, 0),
    ('Good Exercise', 2, 'good-exercise', 'Exercise voted up 25 times', True, 0),
    ('Favorite Exercise', 2, 'favorite-exercise', 'Exercise favorited by 25 users', True, 0),
    ('Civic duty', 2, 'civic-duty', 'Voted 300 times', False, 0),
    ('Strunk & White', 2, 'strunk-and-white', 'Edited 100 entries', False, 0),
    ('Generalist', 2, 'generalist', 'Active in many different tags', False, 0),
    ('Expert', 2, 'expert', 'Very active in one tag', False, 0),
    ('Yearling', 2, 'yearling', 'Active member for a year', False, 0),
    ('Notable Exercise', 2, 'notable-exercise', 'Asked an exercise with 2,500 views', True, 0),
    ('Enlightened', 2, 'enlightened', 'First problem was accepted with at least 10 up votes', False, 0),
    ('Beta', 2, 'beta', 'Actively participated in the private beta', False, 0),
    ('Guru', 2, 'guru', 'Accepted problem and voted up 40 times', True, 0),
    ('Necromancer', 2, 'necromancer', 'Posted a problem to an exercise more than 60 days later with at least 5 votes', True, 0),
    ('Taxonomist', 2, 'taxonomist', 'Created a tag used by 50 exercises', True, 0)
)

class Migration(DataMigration):
    
    def forwards(self, orm):
        "Write your forwards methods here."

        for entry in INITIAL_BADGE_DATA:
            name = entry[0]
            type = entry[1]
            slug = entry[2]
            description = entry[3]
            multiple = entry[4]

            try:
                badge = orm.Badge.objects.get(name=name)
                print 'already have badge %s' % unidecode(name)
            except orm.Badge.DoesNotExist:
                print 'adding new badge %s' % unidecode(name)
                badge = orm.Badge()
                badge.name = name

            badge.type = type
            badge.slug = slug
            badge.description = description
            badge.multiple = multiple
            badge.save()

    
    def backwards(self, orm):
        "Write your backwards methods here."
        for entry in INITIAL_BADGE_DATA:
            name = entry[0]
            try:
                badge = orm.Badge.objects.get(name = name)
                badge.award_badge.clear()
                badge.delete()
                print 'deleted badge %s' % unidecode(name)
            except orm.Badge.DoesNotExist:
                print 'no such badge %s - so skipping' % unidecode(name)
                pass
    
    forum_app_name = os.path.basename(os.path.dirname(os.path.dirname(__file__)))
    if forum_app_name == 'forum':
        models = {
            'auth.group': {
                'Meta': {'object_name': 'Group'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
                'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
            },
            'auth.permission': {
                'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
                'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
            },
            'auth.user': {
                'Meta': {'object_name': 'User'},
                'about': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
                'bronze': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
                'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
                'email_isvalid': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'email_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
                'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
                'gold': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'gravatar': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
                'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
                'hide_ignored_exercises': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
                'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
                'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
                'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
                'exercises_per_page': ('django.db.models.fields.SmallIntegerField', [], {'default': '10'}),
                'real_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
                'reputation': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
                'silver': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'tag_filter_setting': ('django.db.models.fields.CharField', [], {'default': "'ignored'", 'max_length': '16'}),
                'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
                'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
                'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
            },
            'contenttypes.contenttype': {
                'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
                'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
            },
            'forum.activity': {
                'Meta': {'object_name': 'Activity', 'db_table': "u'activity'"},
                'active_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'activity_type': ('django.db.models.fields.SmallIntegerField', [], {}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'is_auditted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.anonymousproblem': {
                'Meta': {'object_name': 'AnonymousProblem'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'anonymous_problems'", 'to': "orm['forum.Exercise']"}),
                'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
            },
            'forum.anonymousexercise': {
                'Meta': {'object_name': 'AnonymousExercise'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
                'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
            },
            'forum.problem': {
                'Meta': {'object_name': 'Problem', 'db_table': "u'problem'"},
                'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'accepted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['auth.User']"}),
                'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'html': ('django.db.models.fields.TextField', [], {'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['forum.Exercise']"}),
                'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
                'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
            },
            'forum.problemrevision': {
                'Meta': {'object_name': 'ProblemRevision', 'db_table': "u'problem_revision'"},
                'problem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['forum.Problem']"}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problemrevisions'", 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
                'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
                'text': ('django.db.models.fields.TextField', [], {})
            },
            'forum.authkeyuserassociation': {
                'Meta': {'object_name': 'AuthKeyUserAssociation'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'provider': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'auth_keys'", 'to': "orm['auth.User']"})
            },
            'forum.award': {
                'Meta': {'object_name': 'Award', 'db_table': "u'award'"},
                'awarded_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'badge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_badge'", 'to': "orm['forum.Badge']"}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_user'", 'to': "orm['auth.User']"})
            },
            'forum.badge': {
                'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Badge', 'db_table': "u'badge'"},
                'awarded_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'awarded_to': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'badges'", 'through': "'Award'", 'to': "orm['auth.User']"}),
                'description': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'multiple': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
                'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
                'type': ('django.db.models.fields.SmallIntegerField', [], {})
            },
            'forum.book': {
                'Meta': {'object_name': 'Book', 'db_table': "u'book'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'author': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'cover_img': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {}),
                'pages': ('django.db.models.fields.SmallIntegerField', [], {}),
                'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '2'}),
                'publication': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'published_at': ('django.db.models.fields.DateTimeField', [], {}),
                'exercises': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'book'", 'db_table': "'book_exercise'", 'to': "orm['forum.Exercise']"}),
                'short_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.bookauthorinfo': {
                'Meta': {'object_name': 'BookAuthorInfo', 'db_table': "u'book_author_info'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'blog_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Book']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.bookauthorrss': {
                'Meta': {'object_name': 'BookAuthorRss', 'db_table': "u'book_author_rss'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Book']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'rss_created_at': ('django.db.models.fields.DateTimeField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.comment': {
                'Meta': {'object_name': 'Comment', 'db_table': "u'comment'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'comment': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': "orm['auth.User']"})
            },
            'forum.emailfeedsetting': {
                'Meta': {'object_name': 'EmailFeedSetting'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
                'feed_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
                'frequency': ('django.db.models.fields.CharField', [], {'default': "'n'", 'max_length': '8'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
                'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.favoriteexercise': {
                'Meta': {'object_name': 'FavoriteExercise', 'db_table': "u'favorite_exercise'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Exercise']"}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_favorite_exercises'", 'to': "orm['auth.User']"})
            },
            'forum.flaggeditem': {
                'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'FlaggedItem', 'db_table': "u'flagged_item'"},
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'flagged_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flaggeditems'", 'to': "orm['auth.User']"})
            },
            'forum.markedtag': {
                'Meta': {'object_name': 'MarkedTag'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'reason': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
                'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_selections'", 'to': "orm['forum.Tag']"}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tag_selections'", 'to': "orm['auth.User']"})
            },
            'forum.exercise': {
                'Meta': {'object_name': 'Exercise', 'db_table': "u'exercise'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'problem_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'problem_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercises'", 'to': "orm['auth.User']"}),
                'close_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
                'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'closed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'closed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'closed_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'favorited_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'favorite_exercises'", 'through': "'FavoriteExercise'", 'to': "orm['auth.User']"}),
                'favourite_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'followed_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'followed_exercises'", 'to': "orm['auth.User']"}),
                'html': ('django.db.models.fields.TextField', [], {'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_activity_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'last_activity_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_active_in_exercises'", 'to': "orm['auth.User']"}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'exercises'", 'to': "orm['forum.Tag']"}),
                'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'view_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
            },
            'forum.exerciserevision': {
                'Meta': {'object_name': 'ExerciseRevision', 'db_table': "u'exercise_revision'"},
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exerciserevisions'", 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['forum.Exercise']"}),
                'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
                'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'})
            },
            'forum.exerciseview': {
                'Meta': {'object_name': 'ExerciseView'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'viewed'", 'to': "orm['forum.Exercise']"}),
                'when': ('django.db.models.fields.DateTimeField', [], {}),
                'who': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercise_views'", 'to': "orm['auth.User']"})
            },
            'forum.repute': {
                'Meta': {'object_name': 'Repute', 'db_table': "u'repute'"},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'negative': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'positive': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['forum.Exercise']"}),
                'reputation': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
                'reputation_type': ('django.db.models.fields.SmallIntegerField', [], {}),
                'reputed_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.tag': {
                'Meta': {'object_name': 'Tag', 'db_table': "u'tag'"},
                'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_tags'", 'to': "orm['auth.User']"}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_tags'", 'null': 'True', 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'used_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
            },
            'forum.validationhash': {
                'Meta': {'unique_together': "(('user', 'type'),)", 'object_name': 'ValidationHash'},
                'expiration': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 5, 2, 12, 29, 51, 920204)'}),
                'hash_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'seed': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
                'type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'forum.vote': {
                'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'Vote', 'db_table': "u'vote'"},
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['auth.User']"}),
                'vote': ('django.db.models.fields.SmallIntegerField', [], {}),
                'voted_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
            }
        }
        
        complete_apps = ['forum']
    else:
        models = {
            'auth.group': {
                'Meta': {'object_name': 'Group'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
                'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
            },
            'auth.permission': {
                'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
                'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
            },
            'auth.user': {
                'Meta': {'object_name': 'User'},
                'about': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
                'bronze': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
                'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
                'email_isvalid': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'email_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
                'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
                'gold': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'gravatar': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
                'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
                'hide_ignored_exercises': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
                'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
                'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
                'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
                'exercises_per_page': ('django.db.models.fields.SmallIntegerField', [], {'default': '10'}),
                'real_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
                'reputation': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
                'silver': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'tag_filter_setting': ('django.db.models.fields.CharField', [], {'default': "'ignored'", 'max_length': '16'}),
                'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
                'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
                'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
            },
            'contenttypes.contenttype': {
                'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
                'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
            },
            'askbot.activity': {
                'Meta': {'object_name': 'Activity', 'db_table': "u'activity'"},
                'active_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'activity_type': ('django.db.models.fields.SmallIntegerField', [], {}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'is_auditted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
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
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
            },
            'askbot.anonymousexercise': {
                'Meta': {'object_name': 'AnonymousExercise'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'ip_addr': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
                'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
            },
            'askbot.problem': {
                'Meta': {'object_name': 'Problem', 'db_table': "u'problem'"},
                'accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'accepted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['auth.User']"}),
                'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'html': ('django.db.models.fields.TextField', [], {'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_problems'", 'null': 'True', 'to': "orm['auth.User']"}),
                'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problems'", 'to': "orm['askbot.Exercise']"}),
                'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
                'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
            },
            'askbot.problemrevision': {
                'Meta': {'object_name': 'ProblemRevision', 'db_table': "u'problem_revision'"},
                'problem': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['askbot.Problem']"}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'problemrevisions'", 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
                'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
                'text': ('django.db.models.fields.TextField', [], {})
            },
            'askbot.authkeyuserassociation': {
                'Meta': {'object_name': 'AuthKeyUserAssociation'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'provider': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'auth_keys'", 'to': "orm['auth.User']"})
            },
            'askbot.award': {
                'Meta': {'object_name': 'Award', 'db_table': "u'award'"},
                'awarded_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'badge': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_badge'", 'to': "orm['askbot.Badge']"}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'notified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'award_user'", 'to': "orm['auth.User']"})
            },
            'askbot.badge': {
                'Meta': {'unique_together': "(('name', 'type'),)", 'object_name': 'Badge', 'db_table': "u'badge'"},
                'awarded_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'awarded_to': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'badges'", 'through': "'Award'", 'to': "orm['auth.User']"}),
                'description': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'multiple': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
                'slug': ('django.db.models.fields.SlugField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
                'type': ('django.db.models.fields.SmallIntegerField', [], {})
            },
            'askbot.book': {
                'Meta': {'object_name': 'Book', 'db_table': "u'book'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'author': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'cover_img': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {}),
                'pages': ('django.db.models.fields.SmallIntegerField', [], {}),
                'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '6', 'decimal_places': '2'}),
                'publication': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'published_at': ('django.db.models.fields.DateTimeField', [], {}),
                'exercises': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'book'", 'db_table': "'book_exercise'", 'to': "orm['askbot.Exercise']"}),
                'short_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.bookauthorinfo': {
                'Meta': {'object_name': 'BookAuthorInfo', 'db_table': "u'book_author_info'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'blog_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Book']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.bookauthorrss': {
                'Meta': {'object_name': 'BookAuthorRss', 'db_table': "u'book_author_rss'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {}),
                'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Book']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'rss_created_at': ('django.db.models.fields.DateTimeField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.comment': {
                'Meta': {'object_name': 'Comment', 'db_table': "u'comment'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'comment': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': "orm['auth.User']"})
            },
            'askbot.emailfeedsetting': {
                'Meta': {'object_name': 'EmailFeedSetting'},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
                'feed_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
                'frequency': ('django.db.models.fields.CharField', [], {'default': "'n'", 'max_length': '8'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'reported_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
                'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.favoriteexercise': {
                'Meta': {'object_name': 'FavoriteExercise', 'db_table': "u'favorite_exercise'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Exercise']"}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_favorite_exercises'", 'to': "orm['auth.User']"})
            },
            'askbot.flaggeditem': {
                'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'FlaggedItem', 'db_table': "u'flagged_item'"},
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'flagged_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'flaggeditems'", 'to': "orm['auth.User']"})
            },
            'askbot.markedtag': {
                'Meta': {'object_name': 'MarkedTag'},
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'reason': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
                'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_selections'", 'to': "orm['askbot.Tag']"}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tag_selections'", 'to': "orm['auth.User']"})
            },
            'askbot.exercise': {
                'Meta': {'object_name': 'Exercise', 'db_table': "u'exercise'"},
                'added_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'problem_accepted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'problem_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exercises'", 'to': "orm['auth.User']"}),
                'close_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
                'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'closed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'closed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'closed_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'comment_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'favorited_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'favorite_exercises'", 'through': "'FavoriteExercise'", 'to': "orm['auth.User']"}),
                'favourite_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'followed_by': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'followed_exercises'", 'to': "orm['auth.User']"}),
                'html': ('django.db.models.fields.TextField', [], {'null': 'True'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'last_activity_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'last_activity_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_active_in_exercises'", 'to': "orm['auth.User']"}),
                'last_edited_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'last_edited_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_edited_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'locked_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'locked_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locked_exercises'", 'null': 'True', 'to': "orm['auth.User']"}),
                'offensive_flag_count': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '180'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'exercises'", 'to': "orm['askbot.Tag']"}),
                'text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
                'view_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
                'vote_down_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'vote_up_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
                'wiki': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'wikified_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
            },
            'askbot.exerciserevision': {
                'Meta': {'object_name': 'ExerciseRevision', 'db_table': "u'exercise_revision'"},
                'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'exerciserevisions'", 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['askbot.Exercise']"}),
                'revised_at': ('django.db.models.fields.DateTimeField', [], {}),
                'revision': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'summary': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
                'tagnames': ('django.db.models.fields.CharField', [], {'max_length': '125'}),
                'text': ('django.db.models.fields.TextField', [], {}),
                'title': ('django.db.models.fields.CharField', [], {'max_length': '300'})
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
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'negative': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'positive': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
                'exercise': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['askbot.Exercise']"}),
                'reputation': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
                'reputation_type': ('django.db.models.fields.SmallIntegerField', [], {}),
                'reputed_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.tag': {
                'Meta': {'object_name': 'Tag', 'db_table': "u'tag'"},
                'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_tags'", 'to': "orm['auth.User']"}),
                'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
                'deleted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
                'deleted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'deleted_tags'", 'null': 'True', 'to': "orm['auth.User']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'used_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
            },
            'askbot.validationhash': {
                'Meta': {'unique_together': "(('user', 'type'),)", 'object_name': 'ValidationHash'},
                'expiration': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2010, 5, 2, 12, 29, 51, 920204)'}),
                'hash_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'seed': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
                'type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
            },
            'askbot.vote': {
                'Meta': {'unique_together': "(('content_type', 'object_id', 'user'),)", 'object_name': 'Vote', 'db_table': "u'vote'"},
                'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
                'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
                'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
                'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'votes'", 'to': "orm['auth.User']"}),
                'vote': ('django.db.models.fields.SmallIntegerField', [], {}),
                'voted_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
            }
        }
        
        complete_apps = ['askbot']
