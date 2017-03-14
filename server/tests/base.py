from __future__ import unicode_literals, print_function, division

import datetime
import logging
import os
import threading
import time
import unittest
import requests
from flask.testing import FlaskClient

from mockredis import mock_strict_redis_client
from selenium import webdriver

from app import create_app


current_port = 5001


class BaseTestCase(unittest.TestCase):
    app = None

    def __init__(self, *args, **kwargs):
        """
        Just for the IDE FlaskClient tip.
        """
        super().__init__(*args, **kwargs)
        self.client = None  # type: FlaskClient

    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        logger = logging.getLogger('werkzeug')
        logger.setLevel("ERROR")

        if not getattr(cls, 'CLIENT_PER_TEST', None):
            cls.client = cls.app.test_client(use_cookies=True)  # type: FlaskClient

            if getattr(cls, 'USE_SESSIONS', None):
                cls.client.__enter__()

    def interactive_shell(self, globals=None, locals=None):
        """
        Opens an interactive shell through which the user running the tests can interact.
        This is only meant to be used for test development purposes. There should be no committed code
        with such a call, because it would block the test.

        Particularly, can be useful for the development of Selenium tests, so that the code can be tested
        before being written into the test, and so that the browser can be inspected exactly when it is
        in the state we expect.
        :return:
        """
        import readline  # optional, will allow Up/Down/History in the console
        import code

        if globals is None:
            vars = globals().copy()
        else:
            vars = globals.copy()

        if locals is None:
            vars.update(locals())
        else:
            vars.update(locals)

        shell = code.InteractiveConsole(vars)
        shell.interact()

    def setUp(self):
        self.rdb = mock_strict_redis_client()

        if getattr(self, 'CLIENT_PER_TEST', None):
            self.client = self.app.test_client(use_cookies=True)

            if getattr(self, 'USE_SESSIONS', None):
                self.client.__enter__()

    def tearDown(self):
        if getattr(self, 'CLIENT_PER_TEST', None):
            if getattr(self, 'USE_SESSIONS', None):
                self.client.__exit__(None, None, None)

    @classmethod
    def tearDownClass(cls):
        if not getattr(cls, 'CLIENT_PER_TEST', None):
            if getattr(cls, 'USE_SESSIONS', None):
                cls.client.__exit__(None, None, None)

        cls.app_context.pop()


class SeleniumTestCase(BaseTestCase):
    webclient = None
    current_port = -1

    @classmethod
    def url(cls, url):
        return 'http://localhost:{0}{1}'.format(cls.current_port, url)

    @classmethod
    def setUpClass(cls, force_driver=None):
        """

        :param force_driver: If set, the environment variable will be ignored and the specific driver will be used.
        :return:
        """

        cls.webclient = None

        # Choose the webdriver to use:
        # We try to use the specified one through the selenium_webdriver variable.
        # If none is specified, we try to find an available one.
        # Supported ones are: 'firefox', 'chrome', 'phantomjs', 'disabled'

        if force_driver is not None:
            driver_name = force_driver
        else:
            driver_name = os.environ.get('SELENIUM_WEBDRIVER', None)

        if driver_name is not None:

            if driver_name == 'firefox':
                try:
                    cls.webclient = webdriver.Firefox()
                except:
                    pass
            elif driver_name == 'chrome':
                try:
                    cls.webclient = webdriver.Chrome()
                except:
                    pass
            elif driver_name == 'phantomjs':
                try:
                    cls.webclient = webdriver.PhantomJS()
                    cls.webclient.set_window_size(1400, 1000)
                except:
                    pass
            elif driver_name == 'disabled':
                pass
            else:
                raise Exception("WebDriver name was not recognized")

        else:
            try:
                cls.webclient = webdriver.Chrome()
            except:
                pass

            if cls.webclient is None:
                try:
                    cls.webclient = webdriver.Firefox()
                except:
                    pass

            if cls.webclient is None:
                try:
                    cls.webclient = webdriver.PhantomJS()
                    cls.webclient.set_window_size(1400, 1000)
                except:
                    pass


        BaseTestCase.setUpClass()

        cls._run_local_server()

    @classmethod
    def _run_local_server(cls):
        """
        Starts the local server on an increasing port, to run the tests against.
        :return:
        """

        global current_port
        cls.current_port = current_port
        current_port = current_port + 1

        threading.Thread(target=cls.app.run, kwargs={'port': cls.current_port}).start()
        MAX_SECONDS = 5
        STEP = 0.1

        found = False
        for x in range(int(MAX_SECONDS / STEP)):
            try:
                if cls.webclient is not None:
                    cls.webclient.get(cls.url('/testing/started'))
                    if 'started' in (cls.webclient.page_source or ''):
                        found = True
                        break
                else:
                    r = requests.get(cls.url('/testing/started'))
                    if 'started' in (r.text or ''):
                        found = True
                        break
            except:
                import traceback
                traceback.print_exc()
                pass
            time.sleep(STEP)

        if not found:
            raise Exception("Could not start server")

    @classmethod
    def tearDownClass(cls):
        if cls.webclient:

            # Save a screenshot
            cls.webclient.save_screenshot('out.png')

            response = cls.webclient.get(cls.url('/testing/shutdown'))
            try:
                cls.webclient.close()
            except:
                print("Warning - Exception closing webdriver")

        else:
            r = requests.get(cls.url('/testing/shutdown'))

        BaseTestCase.tearDownClass()

    def page_get(self, url):
        """
        Opens the specified page to bypass an apparent PhantomJS bug.
        It first opens the specified page through Selenium's get() and then
        redirects through JavaScript (which works in PhamtomJS).
        Once PhantomJS is fixed it should hopefully no longer be necessary to use this.
        :return:
        """
        self.webclient.get(url)

        if '#' in url:
            url_start, hash_url = url.split('#', 1)

            splits = url_start.split('?', 1)
            if len(splits) > 1:
                url_params = "?" + splits[1]
            else:
                url_params = ""

            self.webclient.execute_script("window.location.replace('{}#{}')".format(url_params, hash_url))

            # self.interactive_shell(globals(), locals())

    def setUp(self):
        if not self.webclient:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass
