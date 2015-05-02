from __future__ import absolute_import
import time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import TestCase
from django.utils.importlib import import_module
from django_webtest import WebTestMixin
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
import pyquery

from accounts.models import Identity, Account
from bibleverses.models import TextVersion
import learnscripture.session


class FuzzyInt(int):
    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)


class AccountTestMixin(object):

    fixtures = ['test_bible_versions.json']

    def create_identity(self, version_slug='KJV', account=None):
        version = TextVersion.objects.get(slug=version_slug)
        return Identity.objects.create(default_bible_version=version,
                                       enable_animations=False,
                                       enable_sounds=False,
                                       account=account,
                                       )

    def create_account(self,
                       version_slug='KJV',
                       email="test1@test.com",
                       username="test1"):
        account = Account.objects.create(email=email,
                                         username=username,
                                         )
        account.set_password('password')
        account.save()
        identity = self.create_identity(version_slug=version_slug, account=account)
        return (identity, account)

    def create_account_interactive(self,
                                   email="test2@test.com",
                                   username="test2",
                                   password="testpassword2"):
        self.click(self.driver.find_element_by_link_text('Create an account'))
        self.fill_in_account_form(email=email, username=username, password=password)

    def fill_in_account_form(self,
                             email="test2@test.com",
                             username="test2",
                             password="testpassword2"):
        self.send_keys("#id_signup-email", email)
        self.send_keys("#id_signup-username", username)
        self.send_keys("#id_signup-password", password)
        self.click('input[name=signup]')


def sqla_tear_down():
    from learnscripture.utils import sqla
    sqla.default_engine.pool.dispose()


# https://code.google.com/p/selenium/source/browse/java/client/src/org/openqa/selenium/internal/ElementScrollBehavior.java
class ElementScrollBehavior(object):
    TOP = 0
    BOTTOM = 1


class LoginMixin(object):

    def fill_in_login_form(self, account):
        self.wait_until_loaded('body')
        self.fill_input("#id_login-email", account.email)
        self.fill_input("#id_login-password", "password")
        self.submit("input[name=signin]")


class FullBrowserTest(AccountTestMixin, LoginMixin, StaticLiveServerTestCase):

    hide_browser = True

    @classmethod
    def setUpClass(cls):
        if cls.hide_browser:
            cls.display = Display(visible=0, size=(1024, 768))
            cls.display.start()
        capabilities = webdriver.DesiredCapabilities.FIREFOX.copy()
        # We have problems clicking on elements that are scrolled to the top in
        # order to click on them, but are then covered by the navbar at the
        # top. The fix is to use elementScrollBehavior
        # https://code.google.com/p/selenium/issues/detail?id=4297#c3
        capabilities['elementScrollBehavior'] = ElementScrollBehavior.BOTTOM
        cls.driver = webdriver.Firefox(capabilities=capabilities)
        cls.driver.implicitly_wait(1)
        super(FullBrowserTest, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        if cls.hide_browser:
            cls.display.stop()
        super(FullBrowserTest, cls).tearDownClass()

    def setUp(self):
        super(FullBrowserTest, self).setUp()
        self.driver.delete_all_cookies()
        self.verificationErrors = []

    def tearDown(self):
        self.assertEqual([], self.verificationErrors)
        super(FullBrowserTest, self).tearDown()
        sqla_tear_down()

    # Utilities:
    def setup_session(self):
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore()
        session.save()
        self.driver.get(self.live_server_url)
        self.wait_until_loaded('body')
        self.driver.add_cookie({'domain': 'localhost',
                                'name': settings.SESSION_COOKIE_NAME,
                                'value': session.session_key})
        return session

    def get_url(self, name, *args, **kwargs):
        self.driver.get(self.live_server_url + reverse(name, *args, **kwargs))
        self.wait_until_loaded('body')
        self.wait_for_ajax()

    def find(self, css_selector):
        return self.driver.find_element_by_css_selector(css_selector)

    def click(self, clickable, produces_alert=False, wait_for_reload=False):
        if wait_for_reload:
            self.driver.execute_script("document.pageReloadedYetFlag='notyet'")

        if hasattr(clickable, 'click'):
            retval = clickable.click()
        else:
            retval = self.find(clickable).click()

        if wait_for_reload:
            def f(driver):
                obj = driver.execute_script("return document.pageReloadedYetFlag;")
                if obj is None or obj != "notyet":
                    return True
                return False
            WebDriverWait(self.driver, 5).until(f)

        if not produces_alert:
            # This will cause a Selenium error if an alert is open, and there
            # doesn't sem to be any way of detecting this case.
            self.wait_until_finished()

        return retval

    def submit(self, css_selector, wait_for_reload=False):
        self.click(css_selector, wait_for_reload=wait_for_reload)

    def fill_input(self, elem, val):
        if isinstance(elem, basestring):
            elem = self.find(elem)
        if elem.tag_name == 'select':
            self._set_select_elem(elem, val)
        elif elem.tag_name == 'input' and elem.get_attribute('type') == 'checkbox':
            self._set_check_box(elem, val)
        else:
            elem.clear()
            elem.send_keys(val)

    def fill_by_id(self, fields):
        for k, v in fields.items():
            e = self.find('#' + k)
            self.fill_input(e, v)

    def fill_by_name(self, fields, prefix=""):
        for k, v in fields.items():
            e = self.find('[name="%s%s"]' % (prefix, k))
            self.fill_input(e, v)

    @property
    def current_url(self):
        return self.driver.current_url

    def send_keys(self, css_selector, text):
        retval = self.find(css_selector).send_keys(text)
        self.wait_for_ajax()
        return retval

    def confirm(self):
        self.driver.switch_to_alert().accept()
        self.wait_until_loaded('body')
        self.wait_for_ajax()

    def wait_until(self, callback, timeout=10):
        """
        Helper function that blocks the execution of the tests until the
        specified callback returns a value that is not falsy. This function can
        be called, for example, after clicking a link or submitting a form.
        See the other public methods that call this function for more details.
        """
        WebDriverWait(self.driver, timeout).until(callback)

    def wait_for_ajax(self):
        time.sleep(0.1)
        WebDriverWait(self.driver, 10).until(lambda driver: driver.execute_script('return (typeof(jQuery) == "undefined" || jQuery.active == 0)'))

    def wait_until_finished(self):
        time.sleep(0.1)
        self.wait_for_ajax()
        self.wait_until_loaded('body')

    def wait_until_loaded(self, selector, timeout=10):
        """
        Helper function that blocks until the element with the given tag name
        is found on the page.
        """
        self.wait_until(
            lambda driver: driver.find_element(By.CSS_SELECTOR, selector),
            timeout
        )

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def _set_select_elem(self, elem, value):
        s = Select(elem)
        s.select_by_value(value)

    def _set_check_box(self, elem, state):
        if self.is_checked(elem) != state:
            elem.click()

    # Higher level, learnscripture specific things:

    def login(self, account):
        self.setup_session()
        self.setup_identity(identity=account.identity)

    def setup_identity(self, identity=None):
        session = self.setup_session()
        if identity is None:
            Identity.objects.all().delete()
            identity = Identity.objects.create()
            identity.default_bible_version = TextVersion.objects.get(slug='NET')
            identity.save()
        learnscripture.session.set_identity(session, identity)
        session.save()
        self.identity = identity
        return identity

    def get_identity(self):
        return getattr(self, 'identity', None)

    def set_preferences(self):
        # Set preferences if visible
        driver = self.driver

        if not self.find("#id_desktop_testing_method_0").is_displayed():
            return

        Select(self.find("#id_default_bible_version")).select_by_visible_text("KJV (King James Version)")

        # Turn animations off, as they can complicate testing.
        e = self.find("#id_enable_animations")
        if e.get_attribute('checked'):
            e.click()

        if 'id-preferences-save-btn' in driver.page_source:
            # popup
            self.click("#id-preferences-save-btn")
        else:
            self.click("#id-save-btn")
        self.wait_until_loaded('body')
        self.wait_for_ajax()


class WebTestBase(WebTestMixin, AccountTestMixin, LoginMixin, TestCase):

    # API that is compatible with FullBrowserTest

    def get_url_raw(self, url, auto_follow=True, expect_errors=False):
        self.last_response = self.app.get(url, auto_follow=auto_follow, expect_errors=expect_errors)
        return self.last_response

    def get_url(self, name, *args, **kwargs):
        """
        Gets the named URL, passing *args and **kwargs to Django's URL 'reverse' function.
        """
        return self.get_url_raw(reverse(name, args=args, kwargs=kwargs))

    def fill_input(self, css_selector, value):
        form, field_name = self._find_form_and_field_by_css_selector(self.last_response, css_selector)
        form[field_name] = value

    def fill_by_id(self, data):
        for element_id, value in data.items():
            form, field_name = self._find_form_and_field_by_id(self.last_response, element_id)
            form[field_name] = value

    def submit(self, css_selector, wait_for_reload=None, auto_follow=True):
        form, field_name = self._find_form_and_field_by_css_selector(self.last_response, css_selector)
        response = form.submit(field_name)
        self.last_response = response
        if auto_follow:
            is_redirect = lambda r: r.status_int >= 300 and r.status_int < 400
            while is_redirect(response):
                response = response.follow()
        self.last_response = response

    def click(self, *args, **kwargs):
        raise NotImplementedError("Can't call 'click' on WebTestBase tests. "
                                  "Use 'submit' or 'follow' instead, or move the test into a FullBrowserTest only subclass "
                                  "if you cannot make it WebTest compatible.")

    def follow_link(self, css_selector):
        """
        Follow the link described by the given CSS selector
        """
        self.assertTrue(self.is_element_present(css_selector))
        elems = self._make_pq(self.last_response).find(css_selector)
        if len(elems) == 0:
            raise ValueError("Can't find element matching '{0}'".format(css_selector))

        hrefs = []
        for e in elems:
            if 'href' in e.attrib:
                hrefs.append(e.attrib['href'])

        if not hrefs:
            raise ValueError("No href attribute found for '{0}'".format(css_selector))

        if not all(h == hrefs[0] for h in hrefs):
            raise ValueError("Different href values for links '{0}': '{1}'".format(css_selector,
                                                                                   ' ,'.join(hrefs)))
        self.get_url_raw(hrefs[0])

    @property
    def current_url(self):
        return self.last_response.request.url

    def wait_until_loaded(self, *args, **kwargs):
        pass

    # Higher level, learnscripture specific things:

    def login(self, account):
        # We could mess with session directly, but WebTest is fast enough to do
        # it the long way::
        self.get_url('login')
        self.fill_in_login_form(account)

    # Implementation
    def _make_pq(self, response):
        # Cache to save parsing every time
        if not hasattr(self, '_pq_cache'):
            self._pq_cache = {}
        if response in self._pq_cache:
            return self._pq_cache[response]
        pq = pyquery.PyQuery(response.content)
        self._pq_cache[response] = pq
        return pq

    def _find_form_and_field_by_id(self, response, element_id):
        for form in response.forms.values():
            for field_name, widgets in form.fields.items():
                for widget in widgets:
                    if hasattr(widget, 'id') and widget.id == element_id:
                        return form, field_name
        raise ValueError("Can't find field with id {0} in response: {1}.".format(element_id, response))

    def _find_parent_form(self, elem):
        p = elem.getparent()
        if p is None:
            return None
        if p.tag == 'form':
            return p
        return self._find_parent_form(p)

    def _match_form_elem_to_webtest_form(self, form_elem, response):
        form_sig = {'action': form_elem.attrib.get('action', ''),
                    'id': form_elem.attrib.get('id', ''),
                    'method': form_elem.attrib.get('method', '').lower(),
                    }
        matched = []
        for k, form in response.forms.items():
            if isinstance(k, unicode):
                # Dupe, ignore
                continue
            # signature:
            sig = {'action': getattr(form, 'action', ''),
                   'id': getattr(form, 'id', ''),
                   'method': getattr(form, 'method', '').lower(),
                   }
            sig = {k: v if v is not None else '' for k, v in sig.items()}
            if sig == form_sig:
                matched.append(form)

        if len(matched) > 1:
            raise ValueError("Can't find correct form, multiple found.")
        if len(matched) == 1:
            return matched[0]
        raise ValueError("Can't match form {0} to response forms {1}".format(form_elem, response.forms))

    def _find_form_and_field_by_css_selector(self, response, css_selector):
        pq = self._make_pq(response)
        items = pq.find(css_selector)

        found = []
        for item in items:
            form_elem = self._find_parent_form(item)
            if form_elem is None:
                raise ValueError("Can't find form for input {0}.".format(css_selector))
            form = self._match_form_elem_to_webtest_form(form_elem, response)
            try:
                field = item.name if hasattr(item, 'name') else item.attrib['name']
            except KeyError:
                raise ValueError("Element {0} needs 'name' attribute in order to submit it".format(css_selector))
            found.append((form, field))

        if len(found) == 1:
            return found[0]

        if len(found) > 1:
            raise ValueError("Multiple submit buttons found matching '{0}'".format(css_selector))

        raise ValueError("Can't find submit input matching {0} in response {1}.".format(css_selector, response))
