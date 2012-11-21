"""management command that transfer tag usage data from
one tag to another and deletes the "from" tag

both "from" and "to" tags are identified by id

also, corresponding exercises are retagged
"""
import re
import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from askbot import const, models
from askbot.utils import console
from askbot.management.commands.rename_tags import get_admin

def get_tags_by_ids(tag_ids):
    tags = list()
    for tag_id in tag_ids:
        try:
            tags.append(models.Tag.objects.get(id = tag_id))
        except models.Tag.DoesNotExist:
            raise CommandError('tag with id=%s not found' % tag_id)
    return tags

def get_similar_tags_from_strings(tag_strings, tag_name):
    """returns a list of tags, similar to tag_name from a set of exercises"""

    grab_pattern = r'\b([%(ch)s]*%(nm)s[%(ch)s]*)\b' % \
                {'ch': const.TAG_CHARS, 'nm': tag_name}
    grab_re = re.compile(grab_pattern, re.IGNORECASE)

    similar_tags = set()
    for tag_string in tag_strings:
        similar_tags.update(
            grab_re.findall(tag_string)
        )
    return similar_tags

def parse_tag_ids(input):
    input = input.strip().split(' ')
    return set([int(i) for i in input])

def get_tag_names(tag_list):
    return set([tag.name for tag in tag_list])

def format_tag_name_list(tag_list):
    name_list = get_tag_names(tag_list)
    return u', '.join(name_list)

class Command(BaseCommand):
    "The command object itself"

    help = """Retags exercises from one set of tags to another, like 
rename_tags, but using tag id's


"""
    option_list = BaseCommand.option_list + (
        make_option('--from',
            action = 'store',
            type = 'str',
            dest = 'from',
            default = None,
            help = 'list of tag IDs which needs to be replaced'
        ),
        make_option('--to',
            action = 'store',
            type = 'str',
            dest = 'to',
            default = None,
            help = 'list of tag IDs that are to be used instead'
        ),
        make_option('--user-id',
            action = 'store',
            type = 'int',
            dest = 'user_id',
            default = None,
            help = 'id of the user who will be marked as a performer of this operation'
        ),
    )

    #@transaction.commit_manually
    def handle(self, *args, **options):
        """command handle function. retrieves tags by id
        """
        try:
            from_tag_ids = parse_tag_ids(options['from'])
            to_tag_ids = parse_tag_ids(options['to'])
        except:
            raise CommandError('Tag IDs must be integer')

        in_both = from_tag_ids & to_tag_ids
        if in_both:
            tag_str = ', '.join([str(i) for i in in_both])
            if len(in_both) > 1:
                error_message = 'Tags with IDs %s appear ' % tag_str
            else:
                error_message = 'Tag with ID %s appears ' % tag_str
            raise CommandError(error_message + 'in both --from and --to sets')

        from_tags = get_tags_by_ids(from_tag_ids)
        to_tags = get_tags_by_ids(to_tag_ids)
        admin = get_admin(options['user_id'])

        exercises = models.Thread.objects.all()
        for from_tag in from_tags:
            exercises = exercises.filter(tags=from_tag)

        #print some feedback here and give a chance to bail out
        exercise_count = exercises.count()
        if exercise_count == 0:
            print """Did not find any matching exercises,
you might want to run prune_unused_tags
or repost a bug, if that does not help"""
        elif exercise_count == 1:
            print "One exercise matches:"
        elif exercise_count <= 10:
            print "%d exercises match:" % exercise_count
        if exercise_count > 10:
            print "%d exercises match." % exercise_count
            print "First 10 are:"
        for exercise in exercises[:10]:
            print '* %s' % exercise.title.strip()

        from_tag_names = format_tag_name_list(from_tags)
        to_tag_names = format_tag_name_list(to_tags)

        prompt = 'Rename tags %s --> %s?' % (from_tag_names, to_tag_names)
        choice = console.choice_dialog(prompt, choices=('yes', 'no'))
        if choice == 'no':
            print 'Canceled'
            sys.exit()
        else:
            sys.stdout.write('Processing:')

        #actual processing stage, only after this point we start to
        #modify stuff in the database, one exercise per transaction
        from_tag_names = get_tag_names(from_tags)
        to_tag_names = get_tag_names(to_tags)
        i = 0
        for exercise in exercises:
            tag_names = set(exercise.get_tag_names())
            tag_names.update(to_tag_names)
            tag_names.difference_update(from_tag_names)

            admin.retag_exercise(
                exercise = exercise._exercise_post(),
                tags = u' '.join(tag_names),
                #silent = True #do we want to timestamp activity on exercise
            )
            i += 1
            sys.stdout.write('%6.2f%%' % (100*float(i)/float(exercise_count)))
            sys.stdout.write('\b'*7)
            sys.stdout.flush()

        sys.stdout.write('\n')
        #transaction.commit()

        #may need to run assertions on that there are
        #print 'Searching for similar tags...',
        #leftover_exercises = models.Thread.objects.filter(
        #                        icontains=from_tag.name
        #                    )
        #if leftover_exercises.count() > 0:
        #    tag_strings = leftover_exercises.values_list('tagnames', flat=True)
        #    similar_tags = get_similar_tags_from_strings(
        #                                        tag_strings,
        #                                        from_tag.name
        #                                    )
        #    print '%d found:' % len(similar_tags),
        #    print '\n*'.join(sorted(list(similar_tags)))
        #else:
        #    print "None found."
        #print "Done."
        #transaction.commit()
