import os

SHOW_BROWSER = False


def pytest_addoption(parser):
    parser.addoption("--show-browser", action="store_true", default=False,
                     help="Show web browser window")
    parser.addoption("--traceback-pages", action="store_true", default=False,
                     help="Display traceback pages when running tests (like when DEBUG=True)")
    parser.addoption("--screenshot-on-failure", action='store_true', default=False,
                     help="Save a screenshot when a Selenium test fails")


def pytest_configure(config):
    if config.option.show_browser:
        os.environ['TESTS_SHOW_BROWSER'] = 'TRUE'
    if config.option.traceback_pages:
        os.environ['TEST_TRACEBACK_PAGES'] = 'TRUE'
    if config.option.screenshot_on_failure:
        os.environ['SELENIUM_SCREENSHOT_ON_FAILURE'] = '1'
