import contextlib
import itertools
import os
import time
from collections.abc import Callable, Generator
from functools import wraps
from typing import Any, TypeVar
from unittest.case import _UnexpectedSuccess

import pytest
import selenium
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django_functest import FuncSeleniumMixin, FuncWebTestMixin
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

from accounts.models import Account, Identity
from bibleverses.models import TextVersion

TESTS_SHOW_BROWSER = os.environ.get("TESTS_SHOW_BROWSER", "")
SELENIUM_SCREENSHOT_ON_FAILURE = os.environ.get("SELENIUM_SCREENSHOT_ON_FAILURE", "")


class FuzzyInt(int):
    def __new__(cls, lowest, highest):
        obj = super().__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)


T = TypeVar("T")


def sequence(func: Callable[[int], T]) -> Generator[T, None, None]:
    """
    Generates a sequence of values from a sequence of integers starting at zero,
    passed through the callable, which must take an integer argument.
    """
    return (func(n) for n in itertools.count())


ACCOUNT_EMAIL_SEQUENCE = (f"test{n}@test.com" for n in itertools.count(1))
ACCOUNT_USERNAME_SEQUENCE = (f"tëst{n}" for n in itertools.count(1))


class _Auto:
    """
    Sentinel value indicating an automatic default will be used.
    """

    def __bool__(self):
        # Allow `Auto` to be used like `None` or `False` in boolean expressions
        return False


Auto: Any = _Auto()


def create_account(
    version_slug: str = "KJV",
    email: str = Auto,
    username: str = Auto,
    seen_help_tour: bool = True,
    testing_method=None,
    is_tester: bool = False,
    is_active: bool = True,
    is_moderator: bool = False,
    is_hellbanned: bool = False,
) -> tuple[Identity, Account]:
    """
    Creates an account, returning (identity, account) tuple
    """
    account = Account.objects.create(
        email=email or next(ACCOUNT_EMAIL_SEQUENCE),
        username=username or next(ACCOUNT_USERNAME_SEQUENCE),
        last_login=timezone.now(),
        is_active=is_active,
        is_tester=is_tester,
        is_moderator=is_moderator,
        is_hellbanned=is_hellbanned,
    )
    account.set_password("password")
    account.save()
    identity_kwargs = dict(version_slug=version_slug, seen_help_tour=seen_help_tour, account=account)
    if testing_method is not None:
        identity_kwargs["desktop_testing_method"] = testing_method
        identity_kwargs["touchscreen_testing_method"] = testing_method
        # Otherwise we get defaults, which is important for this method matching
        # what you get from interactive paths for creating account/identity

    identity = create_identity(**identity_kwargs)
    return (identity, account)


def create_identity(
    version_slug="KJV",
    account=None,
    seen_help_tour=True,
    desktop_testing_method=None,
    touchscreen_testing_method=None,
) -> Identity:
    version = TextVersion.objects.get(slug=version_slug)
    identity_kwargs = dict(
        default_bible_version=version,
        enable_animations=False,
        enable_sounds=False,
        account=account,
        seen_help_tour=True,
    )
    if desktop_testing_method is not None:
        identity_kwargs["desktop_testing_method"] = desktop_testing_method
    if touchscreen_testing_method is not None:
        identity_kwargs["touchscreen_testing_method"] = touchscreen_testing_method
    return Identity.objects.create(**identity_kwargs)


def get_or_create_any_account(**kwargs) -> Account:
    account = Account.objects.order_by("id").first()
    if account is None:
        identity, account = create_account(**kwargs)
    return account


# These mixins workaround the fact that `fixtures` attribute does not work for
# us, because Django tries to load fixtures into all DBs if we have `databases
# == '__all__'` set (which is needed for some tests)


class Fixtures:
    # setUpTestData only works for TestCase subclasses. So we add a setUp to
    # cover TransactionTestCase
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.setUpFixtures()

    def setUp(self):
        super().setUp()
        if not isinstance(self, TestCase):
            self.setUpFixtures()

    @classmethod
    def setUpFixtures(cls):
        pass


class TextVersionsMixin(Fixtures):
    @classmethod
    def setUpFixtures(cls):
        super().setUpFixtures()
        cls.KJV = TextVersion.objects.create(
            full_name="King James Version",
            slug="KJV",
            short_name="KJV",
            language_code="en",
        )

        cls.NET = TextVersion.objects.create(
            full_name="New English Translation",
            slug="NET",
            short_name="NET",
            language_code="en",
        )

        cls.TCL02 = TextVersion.objects.create(
            full_name="Kutsal Kitap Yeni Çeviri", slug="TCL02", short_name="TCL02", language_code="tr"
        )


class BibleVersesMixin(TextVersionsMixin):
    @classmethod
    def setUpFixtures(cls):
        super().setUpFixtures()
        call_command("loaddata", "test_bible_verses.json", verbosity=0)


class CatechismsMixin(Fixtures):
    @classmethod
    def setUpFixtures(cls):
        super().setUpFixtures()
        # This works, where `fixtures` attribute does not, because Django tries
        # to load fixtures into all DBs.
        call_command("loaddata", "test_catechisms.json", verbosity=0)


class AccountTestMixin(TextVersionsMixin):

    create_identity = staticmethod(create_identity)
    create_account = staticmethod(create_account)

    def create_account_interactive(self, email="test2@test.com", username="tëst2", password="testpassword2") -> str:
        self.get_url("signup")
        self.fill_in_account_form(email=email, username=username, password=password)
        return username

    def fill_in_account_form(self, email="test2@test.com", username="tëst2", password="testpassword2"):
        self.fill({"#id_signup-email": email, "#id_signup-username": username, "#id_signup-password": password})
        self.submit("[name=signup]")


def sqla_tear_down():
    from learnscripture.utils import sqla

    sqla.default_engine.pool.dispose()


class SqlaCleanup:
    def tearDown(self):
        sqla_tear_down()
        super().tearDown()


class LoginMixin:
    def fill_in_login_form(self, account):
        self.fill({"#id_login-email": account.email, "#id_login-password": "password"})
        self.submit("[name=signin]")

    def login(self, account, shortcut=True):
        if shortcut:
            self.setup_identity(identity=account.identity)
        else:
            self.get_url("login")
            self.fill_in_login_form(account)

    def setup_identity(self, identity=None):
        if identity is None:
            Identity.objects.all().delete()
            identity = Identity.objects.create(seen_help_tour=True)
            identity.default_bible_version = TextVersion.objects.get(slug="NET")
            identity.save()

        self.set_session_data({"identity_id": identity.id})
        return identity


@pytest.mark.selenium
class FullBrowserTest(AccountTestMixin, LoginMixin, FuncSeleniumMixin, SqlaCleanup, StaticLiveServerTestCase):

    display = TESTS_SHOW_BROWSER
    default_timeout = 20
    page_load_timeout = 40
    scroll_method = "legacyWindowScrollTo"

    @classmethod
    def get_webdriver_options(cls):
        kwargs = {}
        if cls.driver_name == "Firefox":
            firefox_binary = os.environ.get("TEST_SELENIUM_FIREFOX_BINARY", None)
            if firefox_binary is not None:
                from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

                kwargs["firefox_binary"] = FirefoxBinary(firefox_path=firefox_binary)
        return kwargs

    # Overridden:
    screenshot_on_failure = SELENIUM_SCREENSHOT_ON_FAILURE

    @classmethod
    def setUpClass(cls):
        if cls.screenshot_on_failure:
            # Wrap all test methods in a decorator. Should really do this in a
            # metaclass, but this works.
            for name in dir(cls):
                if name.startswith("test_"):
                    method = getattr(cls, name)
                    if callable(method):
                        setattr(cls, name, do_screenshot_on_failure(method))

        super().setUpClass()

    def setUp(self):
        super().setUp()
        if not self._have_visited_page():
            self.get_url("django_functest.emptypage")
        self.execute_script("return window.localStorage.clear();")

    def click(self, *args, **kwargs):
        super().click(*args, **kwargs)
        self.wait_for_ajax()

    def submit(self, *args, **kwargs):
        super().submit(*args, **kwargs)
        self.wait_for_ajax()

    def get_literal_url(self, *args, **kwargs):
        super().get_literal_url(*args, **kwargs)
        self.wait_for_ajax()

    # Utilities:

    # We use some django-functest internals here, rather than in actual test
    # classes, to minimize impact if django-functest changes

    # WebTest/Selenium utilities

    def click_and_confirm(self, selector, wait_for_reload=True):
        # 'self.click' is buggy when alerts are produced.
        # So we wrap all of this functionality in a utility
        # to avoid issues.
        if wait_for_reload:
            context = self.wait_for_reload(ignore_exceptions=(NoSuchWindowException,))
        else:
            context = null_context()

        with context:
            self._find(selector).click()
            self._driver.switch_to.alert.accept()

        self.wait_for_page_load()
        self.wait_for_ajax()

    def get_element_text(self, css_selector):
        self.wait_until_loaded(css_selector)
        return self._find(css_selector).text

    def get_element_attribute(self, css_selector, attribute_name):
        self.wait_until_loaded(css_selector)
        return self._find(css_selector).get_attribute(attribute_name)

    # Selenium specific utilities:

    def drag_and_drop(self, from_css_selector, to_css_selector):
        ActionChains(self._driver).drag_and_drop(self._find(from_css_selector), self._find(to_css_selector)).perform()

    def get_page_title(self):
        return self._driver.title

    def press_enter(self, css_selector):
        self._find(css_selector=css_selector).send_keys(selenium.webdriver.common.keys.Keys.ENTER)

    def wait_for_ajax(self):
        time.sleep(0.1)
        self.wait_until(
            lambda driver: driver.execute_script('return (typeof(jQuery) == "undefined" || jQuery.active == 0)')
        )
        self.wait_until(
            lambda _: not self.is_element_present(".htmx-request")
            and not self.is_element_present(".htmx-swapping")
            and not self.is_element_present(".htmx-settling")
        )

    @contextlib.contextmanager
    def wait_for_reload(self, ignore_exceptions=None):

        self._driver.execute_script("document.pageReloadedYetFlag='notyet';")
        yield

        def f(driver):
            obj = driver.execute_script("return document.pageReloadedYetFlag;")

            if obj is None or obj != "notyet":
                return True
            return False

        if ignore_exceptions:
            try:
                WebDriverWait(self._driver, self.get_default_timeout()).until(f)
            except ignore_exceptions:
                pass
        else:
            WebDriverWait(self._driver, self.get_default_timeout()).until(f)
        self.wait_for_ajax()

    # Higher level, learnscripture specific things:

    def set_preferences(self, wait_for_reload=False, bible_version="KJV (King James Version)"):
        """
        Fill in preferences if preferences form is visible.
        """
        if not self.is_element_displayed("#id-preferences-form") and not self.is_element_displayed(
            "#id_default_bible_version"
        ):
            return

        if wait_for_reload:
            context = self.wait_for_reload()
        else:
            context = null_context()

        with context:
            self.fill_by_text({"#id_default_bible_version": bible_version})

            if self.is_element_present("#id-preferences-save-btn"):
                # side panel
                self.click("#id-preferences-save-btn")
            else:
                # preferences page
                self.submit("#id-save-btn")


def do_screenshot_on_failure(method):
    """
    Wraps a method in one that calls `save_screenshot` if any exception occurs.
    """
    if getattr(method, "_screenshot_wrapping_done", False):
        return method

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except _UnexpectedSuccess:
            # not a failure
            raise
        except Exception:
            self.save_screenshot()
            raise

    wrapper._screenshot_wrapping_done = True
    return wrapper


@contextlib.contextmanager
def null_context():
    yield


class WebTestBase(AccountTestMixin, LoginMixin, FuncWebTestMixin, TestCase):
    def get_url(self, *args, **kwargs):
        response = super().get_url(*args, **kwargs)
        if b"???" in response.content:
            raise AssertionError(f"Some kind of FTL error in response:\n {response.content.decode('utf-8')}")

    # Utilities:

    # WebTest/Selenium utilities

    # Use some django-functest internals here

    def click_and_confirm(self, css_selector):
        # No javascript, just submit the button
        self.submit(css_selector)

    def get_element_text(self, css_selector):
        return self._make_pq(self.last_response).find(css_selector).text()

    def get_element_attribute(self, css_selector, attribute_name):
        return self._make_pq(self.last_response).find_(css_selector).attr(attribute_name)


class TestBase(TestCase):
    pass


def show_server_error(request):
    """
    500 error handler to show Django default 500 template
    with nice error information and traceback.
    Useful in testing, if you can't set DEBUG=True.
    """
    import sys

    from django import http
    from django.views.debug import ExceptionReporter

    exc_type, exc_value, exc_traceback = sys.exc_info()
    error = ExceptionReporter(request, exc_type, exc_value, exc_traceback)
    return http.HttpResponseServerError(error.get_traceback_html())
