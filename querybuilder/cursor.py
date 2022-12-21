import contextlib
import json
import psycopg2

from django.db.backends.utils import CursorDebugWrapper


@contextlib.contextmanager
def json_cursor(django_database_connection):
    """
    Cast json fields into their specific types to account for django bugs
    https://code.djangoproject.com/ticket/31956
    https://code.djangoproject.com/ticket/31973
    https://www.psycopg.org/docs/extras.html#psycopg2.extras.register_default_jsonb
    """
    with django_database_connection.cursor() as cursor:
        inner_cursor = cursor.cursor
        # if hasattr(cursor, 'cursor'):
        #     inner_cursor = cursor.cursor
        # Normally cursor is a CursorWrapper with the real cursor as a property. In debug, there is
        # a second layer wrapper called CursorDebugWrapper, so the thing we want is cursor.cursor.cursor :-o

        # if isinstance(inner_cursor, CursorDebugWrapper):
        #     print('json_cursor: cursor was CursorDebugWrapper')
        #     inner_cursor = cursor.cursor

        try:
            psycopg2.extras.register_default_jsonb(conn_or_curs=inner_cursor, loads=json.loads)
        except TypeError:
            print(f'json_cursor: conn_or_curs was actually a {type(inner_cursor)}')
            if isinstance(inner_cursor, CursorDebugWrapper):
                inner_cursor = inner_cursor.cursor
            try:
                psycopg2.extras.register_default_jsonb(conn_or_curs=inner_cursor, loads=json.loads)
            except TypeError as e:
                print(f'json_cursor: conn_or_curs was actually a {type(inner_cursor)}')
                raise TypeError(e)

        yield cursor
