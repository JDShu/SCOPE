/* function testing for existence of a column in a table
   if table does not exists, function will return "false" */
CREATE OR REPLACE FUNCTION column_exists(colname text, tablename text)
RETURNS boolean AS 
$$
DECLARE
    q text;
    onerow record;
BEGIN

    q = 'SELECT attname FROM pg_attribute WHERE attrelid = ( SELECT oid FROM pg_class WHERE relname = '''||tablename||''') AND attname = '''||colname||''''; 

    FOR onerow IN EXECUTE q LOOP
        RETURN true;
    END LOOP;

    RETURN false;
END;
$$ LANGUAGE plpgsql;

/* function adding tsvector column to table if it does not exists */
CREATE OR REPLACE FUNCTION add_tsvector_column(colname text, tablename text)
RETURNS boolean AS
$$
DECLARE
    q text;
BEGIN
    IF NOT column_exists(colname, tablename) THEN
        q = 'ALTER TABLE ' || tablename || ' ADD COLUMN ' || colname || ' tsvector';
        EXECUTE q;
        RETURN true;
    ELSE
        q = 'UPDATE ' || tablename || ' SET ' || colname || '=NULL';
        EXECUTE q;
        RETURN false;
    END IF;
END;
$$ LANGUAGE plpgsql;

/* aggregate function that concatenates tsvectors */
CREATE OR REPLACE FUNCTION tsv_add(tsv1 tsvector, tsv2 tsvector)
RETURNS tsvector AS
$$
BEGIN
    RETURN tsv1 || tsv2;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION setup_aggregates() RETURNS boolean AS
$$
DECLARE
    onerow record;
BEGIN
    FOR onerow IN SELECT * FROM pg_proc WHERE proname = 'concat_tsvectors' AND proisagg LOOP
        DROP AGGREGATE concat_tsvectors(tsvector);
    END LOOP;
    CREATE AGGREGATE concat_tsvectors (
        BASETYPE = tsvector,
        SFUNC = tsv_add,
        STYPE = tsvector,
        INITCOND = ''
    );
    RETURN true;
END;
$$ LANGUAGE plpgsql;

SELECT setup_aggregates();

/* calculates text search vector for exercise 
DOES not include problems or comments */
CREATE OR REPLACE FUNCTION get_exercise_tsv(title text, text text, tagnames text)
RETURNS tsvector AS
$$
BEGIN
    RETURN setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(text, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(tagnames, '')), 'A');
END;
$$ LANGUAGE plpgsql;

/* calculates text search vector for problem text */
CREATE OR REPLACE FUNCTION get_problem_tsv(text text) RETURNS tsvector AS
$$
BEGIN
    RETURN setweight(to_tsvector('english', coalesce(text, '')), 'B');
END;
$$ LANGUAGE plpgsql;

/* calculate text search vector for comment text */
CREATE OR REPLACE FUNCTION get_comment_tsv(comment text) RETURNS tsvector AS
$$
BEGIN
    RETURN setweight(to_tsvector('english', coalesce(comment, '')), 'C');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_dependent_comments_tsv(object_id integer, tablename text)
RETURNS tsvector AS
$$
DECLARE
    query text;
    onerow record;
BEGIN
    query = 'SELECT concat_tsvectors(text_search_vector) FROM comment' ||
        ' WHERE object_id=' ||object_id|| ' AND content_type_id=(' ||
            ' SELECT id FROM django_content_type' ||
            ' WHERE app_label=''askbot'' AND name=''' || tablename || ''')';
    FOR onerow IN EXECUTE query LOOP
        RETURN onerow.concat_tsvectors;
    END LOOP;
    RETURN to_tsvector('');
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_dependent_problems_tsv(exercise_id integer)
RETURNS tsvector AS
$$
DECLARE
    query text;
    onerow record;
BEGIN
    query = 'SELECT concat_tsvectors(text_search_vector) ' ||
       'FROM problem WHERE exercise_id = ' || exercise_id ||
       ' AND deleted=false';
    FOR onerow IN EXECUTE query LOOP
        RETURN onerow.concat_tsvectors;
    END LOOP;
    RETURN to_tsvector('');
END;
$$ LANGUAGE plpgsql;

/* create tsvector columns in the content tables */
SELECT add_tsvector_column('text_search_vector', 'exercise');
SELECT add_tsvector_column('text_search_vector', 'problem');
SELECT add_tsvector_column('text_search_vector', 'comment');

/* populate tsvectors with data */
-- comment tsvectors
UPDATE comment SET text_search_vector = get_comment_tsv(comment);

-- problem tsvectors
UPDATE problem SET text_search_vector = get_problem_tsv(text);
UPDATE problem as a SET text_search_vector = text_search_vector ||
    get_dependent_comments_tsv(a.id, 'problem');

--exercise tsvectors
UPDATE exercise SET text_search_vector = get_exercise_tsv(title, text, tagnames);

UPDATE exercise as q SET text_search_vector = text_search_vector ||
    get_dependent_comments_tsv(q.id, 'exercise');

UPDATE exercise as q SET text_search_vector = text_search_vector ||
    get_dependent_problems_tsv(q.id);

/* set up update triggers */
CREATE OR REPLACE FUNCTION exercise_trigger() RETURNS trigger AS
$$
BEGIN
    new.text_search_vector = get_exercise_tsv(new.title, new.text, new.tagnames);
    new.text_search_vector = new.text_search_vector ||
                            get_dependent_comments_tsv(new.id, 'exercise');
    new.text_search_vector = new.text_search_vector ||
                            get_dependent_problems_tsv(new.id);
    RETURN new;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS exercise_search_vector_update_trigger on exercise;
CREATE TRIGGER exercise_search_vector_update_trigger 
BEFORE INSERT OR UPDATE ON exercise FOR EACH ROW EXECUTE PROCEDURE exercise_trigger();

/* comment trigger */
CREATE OR REPLACE FUNCTION comment_trigger() RETURNS trigger AS
$$
BEGIN
    new.text_search_vector = get_comment_tsv(new.comment);
    RETURN new;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS comment_search_vector_update_trigger on comment;
CREATE TRIGGER comment_search_vector_update_trigger 
BEFORE INSERT OR UPDATE ON comment FOR EACH ROW EXECUTE PROCEDURE comment_trigger();

/* problem trigger */
CREATE OR REPLACE FUNCTION problem_trigger() RETURNS trigger AS
$$
BEGIN
    new.text_search_vector = get_problem_tsv(new.text);
    new.text_search_vector = new.text_search_vector ||
                            get_dependent_comments_tsv(new.id, 'problem');
    RETURN new;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS problem_search_vector_update_trigger on problem;
CREATE TRIGGER problem_search_vector_update_trigger 
BEFORE INSERT OR UPDATE ON problem FOR EACH ROW EXECUTE PROCEDURE problem_trigger();

CREATE INDEX askbot_search_idx ON exercise USING gin(text_search_vector);
