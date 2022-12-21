import contextlib
import json
import psycopg2


@contextlib.contextmanager
def json_cursor(django_database_connection):
    """
    Cast json fields into their specific types to account for django bugs
    https://code.djangoproject.com/ticket/31956
    https://code.djangoproject.com/ticket/31973
    https://www.psycopg.org/docs/extras.html#psycopg2.extras.register_default_jsonb
    """
    with django_database_connection.cursor() as cursor:

        # The thing that is returned by connection.cursor() is (normally) a Django object
        # of type CursorWrapper that itself has the "real" cursor as a property called cursor.
        # However, it could be a CursorDebugWrapper instead, or it could be an outer wrapper
        # wrapping one of those. For example django-debug-toolbar wraps CursorDebugWrapper in
        # a NormalCursorWrapper. The django-db-readonly package wraps the Django CursorWrapper
        # in a ReadOnlyCursorWrapper. I'm not sure if they ever next multiple levels. I tried
        # looping in while `isinstance(inner_cursor, CursorWrapper)`, but it seems that the
        # outer wrapper is not necessarily a subclass of the Django wrapper. My next best option
        # is to make the assumption that we need to get to the last property called `cursor`,
        # basically assuming that any wrapper is going to have a property called that that is the
        # real cursor or the next-level wrapper.

        # We expect that there is ALWAYS at least ONE wrapper.
        inner_cursor = cursor.cursor

        # The other option might be to check the class of inner_cursor to see if it is the real database cursor.
        # I'm not sure if that would work across multiple version of django though.
        while hasattr(inner_cursor, 'cursor'):
            inner_cursor = inner_cursor.cursor

        # Hopefully we have the right thing now, but try/catch so we can get a little better info
        # if it is not. Another option might be an isinstance, or another function that tests the cursor?
        try:
            psycopg2.extras.register_default_jsonb(conn_or_curs=inner_cursor, loads=json.loads)
        except TypeError as e:
            print(f'json_cursor: conn_or_curs was actually a {type(inner_cursor)}')
            raise TypeError(e)

        yield cursor
