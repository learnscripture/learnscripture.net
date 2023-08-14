import contextlib
import io
import itertools
import logging
import os
import re
import shutil
import sys
import time
import traceback
import types
from dataclasses import dataclass

import texttable
from django.core.signals import request_finished
from django.db import connection

logger = logging.getLogger(__name__)

LIMIT = 10  # Increase if not enough

SKIP_MODULES = [
    "logging",
    "__name__",
    "__main__",
    "django.db",
    "django.db.models",
    "django.db.models.query",
    "django.db.models.base",
    "django.contrib",
    "django.dispatch",
    "django.utils.functional",
]

IGNORE_URLS = {
    # Project specific stuff...
}

EXTRA_INFO = [
    # Module, function/method name, local
    # These are specific to current versions, and may need to change if
    # we upgrade.
    ("rest_framework.fields", "get_attribute", "attr"),
    ("rest_framework.fields", "get_attribute", "instance"),
    ("rest_framework.serializers", "to_representation", "field"),
    ("rest_framework.serializers", "to_representation", "item"),
    # Other project specific stuff...
]


# This can be overridden using COLUMNS environment variable
SCREEN_WIDTH = shutil.get_terminal_size(fallback=(200, 50)).columns


def db_debug_middleware(get_reponse):
    def middleware(request):
        db_logging = os.environ.get("DB_LOGGING", "")
        is_detailed = db_logging.lower() == "detailed"
        if db_logging and request.path not in IGNORE_URLS:
            recorder = QueryRecorder()
            db_ctx = connection.execute_wrapper(recorder)
        else:
            recorder = None
            db_ctx = contextlib.nullcontext()

        with db_ctx:
            response = get_reponse(request)
            if recorder:
                # We want to log, but immediately after the end of the request, so that
                # it prints after the request info line in the development server.
                # So use a one-shot request_finished callback
                def callback(**kwargs):
                    display_query_info(recorder, request, response, detailed=is_detailed)
                    request_finished.disconnect(callback)

                request_finished.connect(callback)

            return response

    return middleware


# Query collection


class QueryRecorder:
    def __init__(self):
        self.queries: list[QueryInfo] = []

    def __call__(self, execute, sql, params, many, context):
        current_query = QueryInfo(
            sql=sql,
            params=params,
            many=many,
            stacktrace=fancy_format_stack(sys._getframe(1)),
            original_order=len(self.queries),
        )
        start = time.time()
        try:
            result = execute(sql, params, many, context)
        except Exception as e:
            current_query.status = "error"
            current_query.exception = e
            raise
        else:
            return result
        finally:
            duration = time.time() - start
            current_query.duration = duration
            self.queries.append(current_query)


@dataclass
class QueryInfo:
    sql: str
    params: list
    many: bool
    stacktrace: str
    status: str = "ok"
    exception: object | None = None
    duration: float | None = None
    original_order: int = 0


# Query analysis


@dataclass
class OutputInfo:
    count: int
    sql: str
    stacktrace: str
    total_db_time: float
    original_order: int


def analyse_query_info(query_info: list[QueryInfo]) -> list[OutputInfo]:
    grouped_queries = group_query_info(query_info)

    def format_sql_with_params(sql, params):
        try:
            return sql % params
        except TypeError:
            return f"{sql}; params={params}"

    return [
        OutputInfo(
            count=len(queries),
            sql=format_sql_with_params(queries[0].sql, queries[0].params),
            stacktrace=queries[0].stacktrace,
            total_db_time=sum(q.duration for q in queries if q.duration),
            original_order=queries[0].original_order,
        )
        for queries in grouped_queries
    ]


def group_query_info(query_info: list[QueryInfo]) -> list[list[QueryInfo]]:
    def key(query):
        return (query.sql, query.stacktrace)

    return [list(items) for _, items in itertools.groupby(sorted(query_info, key=key), key=key)]


# Display functions


def analyse_and_format_query_info(recorder, styler=None, screen_width=SCREEN_WIDTH):
    queries = recorder.queries
    output = io.StringIO()
    if styler is None:
        styler = get_styler()

    def write(*args, **kwargs):
        return print(*args, **kwargs, file=output)

    output_info = analyse_query_info(queries)
    output_info.sort(key=lambda item: (item.count, item.original_order))

    for i, info in enumerate(output_info):
        write(styler.YELLOW(f"=== Query {i + 1}: {info.count} repetitions ===="))
        write(f"Total DB time: {info.total_db_time:.5f}ms")
        write("SQL (example):\n")
        write(f"  {info.sql}")
        write(styler.GREEN(info.stacktrace))

    # Summary table
    write()
    write(styler.YELLOW("Summary:"))
    table = texttable.Texttable(max_width=screen_width)
    headers = ["Number", "Count", "Total time", "Query"]

    # Header widths are enough for most columns:
    col_widths = list(map(len, headers))
    # Give remaining space to query. We also need to truncate query
    # to that number of chars so that it doesn't wrap.
    query_width = screen_width - sum(col_widths[:-1]) - (len(headers) * 3 + 2)  # borders
    col_widths[-1] = query_width
    table.set_cols_width(col_widths)
    table.add_row(headers)
    for i, info in enumerate(output_info):
        query_trimmed = re.sub(r"\s+", " ", info.sql)[0:query_width]
        table.add_row([i + 1, info.count, info.total_db_time, query_trimmed])
    total_count = sum(info.count for info in output_info)
    total_time = sum(info.total_db_time for info in output_info)
    table.add_row(["ALL", total_count, total_time, ""])
    write(table.draw())
    return output.getvalue()


def display_query_info(recorder, request=None, response=None, detailed=False, screen_width=SCREEN_WIDTH):
    styler = get_styler()
    queries = recorder.queries
    # -- Print simple --
    if not detailed:
        count = len(recorder.queries)
        grouped_count = len(group_query_info(queries))
        dupes = count - grouped_count
        total_time = sum(q.duration for q in recorder.queries if q.duration)
        count_formatted = (styler.RED if count > 50 else styler.YELLOW)(f"Count: {count}  ")
        dupes_formatted = (styler.RED if dupes > 10 else styler.YELLOW)(f"Dupes: {dupes}  ")
        print(
            styler.YELLOW("[DB] ") + count_formatted + dupes_formatted + styler.YELLOW(f"Total time: {total_time:.4f}")
        )
        return

    # -- Print detailed --

    # Request line:
    url = request.build_absolute_uri() if request else ""
    verb = request.method if request else ""
    if response:
        code = str(response.status_code)
    else:
        code = ""
    print(
        styler.BLACK(styler.BG_GREEN("=== "))
        + f" {verb} "
        + styler.BLACK(styler.BG_WHITE(url))
        + " "
        + (
            (
                code
                if code[0]
                in (
                    "2",  # 2XX success
                    "3",  # 3XX redirection
                )
                else
                # 4XX, 5XX - errors
                styler.BG_RED(styler.BLACK(code))
            )
            if code
            else "" + " "
        )
        + styler.BLACK(styler.BG_GREEN("==="))
    )

    # Queries + stacktrace
    print(analyse_and_format_query_info(recorder, screen_width=SCREEN_WIDTH, styler=styler))

    print(f"=== END {url} ===")
    print()


class Style:
    BLACK = lambda x: "\033[30m" + str(x) + "\033[0m"  # noqa: E731
    RED = lambda x: "\033[31m" + str(x) + "\033[0m"  # noqa: E731
    GREEN = lambda x: "\033[32m" + str(x) + "\033[0m"  # noqa: E731
    YELLOW = lambda x: "\033[33m" + str(x) + "\033[0m"  # noqa: E731
    BG_GREEN = lambda x: "\033[42m" + str(x) + "\033[0m"  # noqa: E731
    BG_WHITE = lambda x: "\033[47m" + str(x) + "\033[0m"  # noqa: E731
    BG_RED = lambda x: "\033[41m" + str(x) + "\033[0m"  # noqa: E731


class NoStyle:
    def __getattr__(self, name):
        # Return no-op for all styles.
        return lambda x: str(x)


def get_styler(stdout=None):
    if stdout is None:
        stdout = sys.stdout
    if stdout.isatty():
        # Real terminal:
        return Style
    else:
        return NoStyle()


# Stack formatting


def safe_repr(obj):
    # A repr that tries to ensure we don't do anything that might
    # trigger extra work or DB queries, otherwise we'll be in trouble.
    # For certain objects we try to include additional info we need.
    if isinstance(obj, str | int | float):
        return repr(obj)
    if isinstance(obj, types.MethodType):
        return repr(obj.__func__)
    if isinstance(obj, types.FunctionType):
        return repr(obj)
    return None


def fancy_format_stack(start_frame, limit=LIMIT, skip_modules=SKIP_MODULES, extra_info=EXTRA_INFO):
    frame = start_frame
    output = []
    while any(True for skip in skip_modules if frame.f_globals.get("__name__", "").startswith(skip)):
        if hasattr(frame, "f_back"):
            frame = frame.f_back

    # We want a normal stack trace, but with extra info in certain frames to
    # show local variables and identify root causes. This is also helpful in
    # deduplicating queries
    count = 0
    while count < limit:
        if not frame:
            break
        line = traceback.format_stack(f=frame, limit=1)[0]
        for module_name, function_name, local_name in extra_info:
            if frame.f_globals.get("__name__", "") == module_name:
                fs = traceback.extract_stack(frame, limit=1)[0]
                if fs.name == function_name and local_name in frame.f_locals:
                    val = frame.f_locals[local_name]
                    r = safe_repr(val)
                    if r is None:
                        line += f"      Locals: {local_name} :: {type(val)}\n"
                    else:
                        line += f"      Locals: {local_name} == {r}\n"

        output.append(line)
        count += 1
        if not hasattr(frame, "f_back"):
            break
        frame = frame.f_back

    output.reverse()
    return "".join(output).rstrip()


@contextlib.contextmanager
def db_recorder_context():
    """
    Returns context that records queries.
    For interactive use.

    >>> with db_recorder_context() as recorder:
    >>>     do_stuff()
    >>> recorder.queries
    """
    recorder = QueryRecorder()
    db_ctx = connection.execute_wrapper(recorder)
    with db_ctx:
        yield recorder
