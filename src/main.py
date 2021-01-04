import datetime
import os
import time
import traceback

import mechanicalsoup
import requests
from mechanicalsoup import LinkNotFoundError
from message_service import Messenger


class EventLoop:
    def __init__(self, global_exception_handler=None):
        self.delta_time = 20
        self.__scheduled_functions = []
        self.__exception_handler = global_exception_handler
        self.__set_up_functions = []
        self._should_break = False

    def schedule_set_up(self, func):
        self.__set_up_functions.append(func)

    def schedule_repeating(self, function):
        self.__scheduled_functions.append(function)

    def unschedule(self, function):
        if function in self.__scheduled_functions:
            self.__scheduled_functions.remove(function)
            return True
        return False

    def run_set_up_functions(self):
        """
        Runs all the functions defined as set_up functions

        It is called before all scheduled functions
        """
        while len(self.__set_up_functions):
            self.__set_up_functions.pop()()

    def should_break(self):
        """ Determines whether the main loop should continue executing"""
        return self._should_break

    def schedule_bread(self):
        self._should_break = True

    def run(self):
        """
        The main loop

        Calls all functions scheduled and sleeps for the amount of time in
        seconds specified in delta_time attribute

        If an exception occurs during the execution of the loop the exception handler
        function is called to handle it if defined. Otherwise No action is taken

        Polls the should break function to determine whether the loop should close and execution stop

        :return:
        """
        self.run_set_up_functions()
        while True:
            try:
                for func in self.__scheduled_functions:
                    func()
                time.sleep(self.delta_time)
                if self.should_break():
                    break
            except Exception as e:
                if self.__exception_handler:
                    self.__exception_handler(e)
                elif not os.environ.get('DEBUG'):
                    raise


def set_up():
    # Resolve dh key too small exception as mechanicalsoup uses requests
    # https://stackoverflow.com/questions/38015537/python-requests-exceptions-sslerror-dh-key-too-small
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH!aNULL'
    try:
        requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH!aNULL'
    except:
        # no pyopenssl support used/ needed /available
        pass


def check_room_booking_open():
    """Main function that is run to check whether the room booking application link has been opened"""
    browser = mechanicalsoup.StatefulBrowser()

    # log in to student portal
    browser.open('https://smis.uonbi.ac.ke')

    browser.select_form()  # There is only one form on the page, the login form
    browser['regNo'] = os.environ['REG_NO']
    browser['smisPass'] = os.environ['SMIS_PASS']
    response = browser.submit_selected()
    if not response:
        raise Exception('Login Failed')

    # go the room booking page and check for a form on that page
    browser.follow_link('http://smis.uonbi.ac.ke/hamis/bookroom.php')
    browser.open_relative('?session=in&amp;AcademicYear=2020/2021')
    try:
        browser.select_form()
    except LinkNotFoundError:
        pass
    else:
        sms_sender = Messenger()
        sms_sender.send_message('+254705493474', 'Hello World')


def exception_handler(e):
    """Logs all exceptions to an error log"""
    with open('accommodation_checker.error.log', 'a') as f:
        f.write('[{}] [ main ] ERROR: \n'.format(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
        traceback.print_exc(file=f)
        f.write('\n\n')


if __name__ == '__main__':
    loop = EventLoop(exception_handler)
    loop.schedule_set_up(set_up)
    loop.schedule_repeating(check_room_booking_open)
    loop.run()
