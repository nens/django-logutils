import logging
import time

from django.http import HttpRequest, HttpResponse

from django_logutils import middleware


def test_log_dict():
    request = HttpRequest()
    response = HttpResponse()
    log_dict = middleware.create_log_dict(request, response)
    assert len(log_dict) == 8

def test_empty_log_message():
    request = HttpRequest()
    response = HttpResponse()
    log_dict = middleware.create_log_dict(request, response)
    log_msg = middleware.create_log_message(log_dict)
    # assert that log_msg is an empty log message
    assert log_msg == 'None - None  200 0 (-1.00 seconds)'

def test_empty_logging_middleware_response():
    request = HttpRequest()
    response = HttpResponse()
    mw = middleware.LoggingMiddleware()
    mw.process_request(request)
    response = mw.process_response(request, response)
    assert response.status_code == 200

def test_logging_middleware_request_start_time():
    request = HttpRequest()
    mv = middleware.LoggingMiddleware()
    assert mv.start_time is None
    current_time = time.time()
    mv.process_request(request)
    # current_time and start_time should be not differ by more than 3 seconds
    assert mv.start_time - current_time < 3
    assert isinstance(mv.start_time, float)

def test_logging_middleware_with_empty_view(client, settings, caplog):
    settings.MIDDLEWARE_CLASSES = (
        'django_logutils.middleware.LoggingMiddleware',      
    )
    settings.ROOT_URLCONF = 'tests.middleware.urls'
    response = client.get('/empty/', {})
    assert len(response.content) == 0
    assert len(caplog.records()) == 1
    record = caplog.records()[0]
    assert '/empty/' in record.msg
    assert '127.0.0.1' in record.msg
    assert record.remote_address == '127.0.0.1'
    assert record.levelname == 'INFO'
    assert record.method == 'GET'
    assert record.filename == 'middleware.py'
    assert record.status == 200
    assert record.user_email == '-'
    assert record.url == '/empty/'

def test_HTTP_X_FORWARDED_FOR_header(client, settings, caplog):
    settings.MIDDLEWARE_CLASSES = (
        'django_logutils.middleware.LoggingMiddleware',      
    )
    settings.ROOT_URLCONF = 'tests.middleware.urls'
    settings.INTERNAL_IPS = ('127.0.0.1', )
    response = client.get('/empty/', {}, HTTP_X_FORWARDED_FOR='1.2.3.4')
    record = caplog.records()[0]
    assert record.remote_address == '1.2.3.4'

def test_HTTP_X_FORWARDED_FOR_header_without_INTERNAL_IPS(
        client, settings, caplog):
    settings.MIDDLEWARE_CLASSES = (
        'django_logutils.middleware.LoggingMiddleware',      
    )
    settings.ROOT_URLCONF = 'tests.middleware.urls'
    response = client.get('/empty/', {}, HTTP_X_FORWARDED_FOR='1.2.3.4')
    record = caplog.records()[0]
    assert record.remote_address == '127.0.0.1'

def test_debug_logging(client, settings, caplog):
    settings.MIDDLEWARE_CLASSES = (
        'django_logutils.middleware.LoggingMiddleware',      
    )
    settings.ROOT_URLCONF = 'tests.middleware.urls'
    settings.DEBUG = True
    response = client.get('/empty/')
    record = caplog.records()[0]
    assert hasattr(record, 'nr_queries')
    assert record.nr_queries == 0
    assert hasattr(record, 'sql_time')
    assert record.sql_time == 0

def test_no_debug_logging_missing_keys(client, settings, caplog):
    settings.MIDDLEWARE_CLASSES = (
        'django_logutils.middleware.LoggingMiddleware',      
    )
    settings.ROOT_URLCONF = 'tests.middleware.urls'
    settings.DEBUG = False
    response = client.get('/empty/')
    record = caplog.records()[0]
    assert not hasattr(record, 'nr_queries')
    assert not hasattr(record, 'sql_time')

def test_logging_middleware_with_non_empty_view(client, settings):
    settings.MIDDLEWARE_CLASSES = (
        'django_logutils.middleware.LoggingMiddleware',      
    )
    settings.ROOT_URLCONF = 'tests.middleware.urls'
    response = client.get('/non_empty/')
    assert len(response.content) == 5
