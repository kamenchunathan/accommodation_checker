import datetime
import os
import time
import traceback

import mechanicalsoup
import requests
from logger import log_updated_message
from mechanicalsoup import LinkNotFoundError
from message_service import Messenger, TwilioLiveSMSBackend


def handle_exceptions(exception_handler_func):
    def decorator(wrapped):
        def wrapper(*args, **kwargs):
            try:
                return wrapped(*args, **kwargs)
            except Exception as e:
                exception_handler_func(e)

        return wrapper

    return decorator


class EventLoop:
    delta_time = 10 * 60  # Check every ten minutes

    __scheduled_functions = []
    __exception_handler = None
    __set_up_functions = []
    __single_iter_scheduled_functions = []

    _should_break = False

    @classmethod
    def schedule_set_up(cls, func):
        cls.__set_up_functions.append(func)

    @classmethod
    def schedule_repeating(cls, func):
        cls.__scheduled_functions.append(func)

    @classmethod
    def schedule_once(cls, func, *args, **kwargs):
        """
        Schedules a func for execution in the next iteration of the loop if 
        the time elapsed exceeds the delay set

        :param func: func to call
        :param delay: time in seconds that should pass before the func is called again
        :param *args, **kwargs All other arguments are passed to the function to be called
        :return: None
        """
        cls.__single_iter_scheduled_functions.append({
            'time_scheduled': datetime.datetime.now(),
            'delay': kwargs.pop('delay', 0),
            'func': func,
            'args': args,
            'kwargs': kwargs
        })

    @classmethod
    def unschedule(cls, func):
        if func in cls.__scheduled_functions:
            cls.__scheduled_functions.remove(func)
            return True
        return False

    @classmethod
    def run_set_up_functions(cls):
        """
        Runs all the functions defined as set_up functions

        It is called before all scheduled functions
        """
        while len(cls.__set_up_functions):
            cls.__set_up_functions.pop()()

    @classmethod
    def should_break(cls):
        """ Determines whether the main loop should continue executing"""
        return cls._should_break

    @classmethod
    def schedule_bread(cls):
        cls._should_break = True

    @classmethod
    def set_global_exception_handler(cls, func):
        cls.__exception_handler = func

    @classmethod
    def _call_single_scheduled_functions(cls):
        for func_details in cls.__single_iter_scheduled_functions:
            elapsed_time = datetime.timedelta(seconds=func_details['delay'])
            if func_details['time_scheduled'] + elapsed_time < datetime.datetime.now():
                try:
                    args = func_details['args'] if func_details['args'] else ()
                    kwargs = func_details['kwargs'] if func_details['kwargs'] else {}
                    func_details['func'](*args, **kwargs)
                except Exception as exc:
                    if cls.__exception_handler:
                        cls.__exception_handler(exc)
                    elif not os.environ.get('DEBUG'):
                        raise
                finally:
                    cls.__single_iter_scheduled_functions.remove(func_details)

    @classmethod
    def run(cls):
        """
        The main loop

        Calls all functions scheduled and sleeps for the amount of time in
        seconds specified in delta_time attribute

        If an exception occurs during the execution of the loop the exception handler
        func is called to handle it if defined. Otherwise No action is taken

        Polls the should break func to determine whether the loop should close and execution stop

        :return:
        """
        cls.run_set_up_functions()
        while True:
            # call all functions that have been scheduled once if appropriate
            cls._call_single_scheduled_functions()

            # call all functions that have been scheduled to repeat
            for func in cls.__scheduled_functions:
                try:
                    func()
                except Exception as e:
                    if cls.__exception_handler:
                        cls.__exception_handler(e)
                    elif not os.environ.get('DEBUG'):
                        raise
            time.sleep(cls.delta_time)
            if cls.should_break():
                break


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
    """Main func that is run to check whether the room booking application link has been opened"""
    time_delay_before_click = 5
    browser = mechanicalsoup.StatefulBrowser()

    # log in to student portal
    browser.open('https://smis.uonbi.ac.ke')
    time.sleep(time_delay_before_click)

    browser.select_form()  # There is only one form on the page, the login form
    browser['regNo'] = os.environ['REG_NO']
    browser['smisPass'] = os.environ['SMIS_PASS']
    response = browser.submit_selected()
    if not response:
        raise Exception('Login Failed')

    # go the room booking page and check for a form on that page
    browser.follow_link('https://smis.uonbi.ac.ke/hamis/bookroom.php')
    time.sleep(time_delay_before_click)
    browser.open_relative('?session=in&amp;AcademicYear=2020/2021')
    try:
        browser.select_form()
    except LinkNotFoundError:
        pass
    else:
        sms_sender = Messenger(backend=TwilioLiveSMSBackend())
        message = sms_sender.send_message('+254705493474', 'Hello World')

        EventLoop.schedule_once(log_updated_message, message)


def exception_handler(e):
    """Logs all exceptions to an error log"""
    with open('logs/accommodation_checker.error.log', 'a') as f:
        f.write('[{}] [ main ] ERROR: \n'.format(
            datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')))
        traceback.print_exc(file=f)
        f.write('\n\n')


if __name__ == '__main__':
    EventLoop.set_global_exception_handler(exception_handler)
    EventLoop.schedule_set_up(set_up)
    EventLoop.schedule_repeating(check_room_booking_open)
    EventLoop.run()
