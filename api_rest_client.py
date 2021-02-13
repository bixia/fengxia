import sys
import traceback
from datetime import datetime
from enum import Enum
from multiprocessing.dummy import Pool
from queue import Queue, Empty
from types import TracebackType
from typing import Any, Callable, Optional, Union, Type

import requests

CALLBACK_TYPE = Callable[[dict, "Request"], Any]
ON_FAILED_TYPE = Callable[[int, "Request"], Any]
ON_ERROR_TYPE = Callable[[Type, Exception, TracebackType, "Request"], Any]


class RequestStatus(Enum):
    ready = 0
    success = 1
    failed = 2
    error = 3


class Request(object):
    #     request object for status check
    def __init__(
            self,
            method: str,
            path: str,
            params: dict,
            data: Union[dict, str, bytes],
            headers: dict,
            callback: CALLBACK_TYPE = None,
            on_failed: ON_FAILED_TYPE = None,
            on_error: ON_ERROR_TYPE = None,
            extra: Any = None,

    ):
        self.method: str = method
        self.path: str = path
        self.callback: CALLBACK_TYPE = callback
        self.params: dict = params
        self.data: Union[dict, str, bytes] = data
        self.headers: dict = headers

        self.on_failed: ON_FAILED_TYPE = on_failed
        self.on_error: ON_ERROR_TYPE = on_error
        self.extra: Any = extra
        self.response: requests.Response = None
        self.status: RequestStatus = RequestStatus.ready

    def __str__(self):
        if self.response is None:
            status_code = "terminated"
        else:
            status_code = self.response.status_code

        return (
            "request : {} {} {} because {}: \n"
            "headers: {}\n"
            "params: {}\n"
            "data: {}\n"
            "response:"
            "{}\n".format(
                self.method,
                self.path,
                self.status.name,
                status_code,
                self.headers,
                self.params,
                self.data,
                "" if self.response is None else self.response.text
            )
        )


class RestClient(object):
    # HTTP client for RESTFUL API
    def __init__(self):
        self.url_base: str = ""
        self._active: bool = False

        self._queue: Queue = Queue()
        self._pool: Pool = None

        self.proxies: dict = None

    def init(
            self,
            url_base: str,
            proxy_host: str = "",
            proxy_port: int = 0
    ) -> None:
        # API root address
        self.url_base: str = url_base

        if proxy_host and proxy_port:
            proxy = f"http://{proxy_host}:{proxy_port}"
            self.proxies = {"http": proxy, "https": proxy}

    def start(self, n: int = 3) -> None:
        if self._active:
            return

        self._active = True
        self._pool: Pool = Pool(n)
        self._pool.apply_async(self._run)

    def stop(self) -> None:
        self._active = False

    def join(self) -> None:
        self._queue.join()

    def add_request(
            self,
            method: str,
            path: str,
            callback: CALLBACK_TYPE,
            params: dict = None,
            data: Union[dict, str, bytes] = None,
            headers: dict = None,
            on_failed: ON_FAILED_TYPE = None,
            on_error: ON_ERROR_TYPE = None,
            extra: Any = None,
    ) -> Request:
        # add a new request
        request = Request(
            method,
            path,
            params,
            data,
            headers,
            callback,
            on_failed,
            on_error,
            extra
        )
        self._queue.put(request)
        return request

    def _run(self) -> None:
        try:
            session = requests.session()
            while self._active:
                try:
                    request = self._queue.get(timeout=1)
                    try:
                        self._process_request(request, session)
                    finally:
                        self._queue.task_done()
                except Empty:
                    pass
        except Exception:
            et, ev, tb = sys.exc_info()
            self.on_error(et, ev, tb)

    def sign(self, request: Request) -> Request:
        return request

    def on_failed(self, status_code: int, request: Request) -> None:
        sys.stderr.write(str(request))

    def on_error(
            self,
            exception_type: type,
            exception_value: Exception,
            tb,
            request: Optional[Request]
    ) -> None:
        sys.stderr.write(
            self.exception_detail(exception_type, exception_value, tb, request)
        )
        sys.excepthook(exception_type, exception_value, tb)

    def exception_detail(
            self,
            exception_type: type,
            exception_value: Exception,
            tb,
            request: Optional[Request]
    ) -> str:
        text = "[{}]: UnHandled RestClient Error:{}\n".format(
            datetime.now().isoformat(), exception_type
        )
        text += "request: {}\n".format(request)
        text += "Exception trace: \n"
        text += "".join(
            traceback.format_exception(exception_type, exception_value, tb)
        )
        return text

    def _process_request(
            self,
            request: Request,
            session: requests.Session
    ) -> None:
        # send request to server
        try:
            request = self.sign(request)
            url = self.make_full_url(request.path)

            response = session.request(
                request.method,
                url,
                headers=request.headers,
                params=request.params,
                data=request.data,
                proxies=self.proxies,
            )
            request.response = response
            status_code = response.status_code
            if status_code // 100 == 2:
                if status_code == 204:
                    json_body = None
                else:
                    json_body = response.json()

                request.callback(json_body, request)
                request.status = RequestStatus.success
            else:
                request.status = RequestStatus.failed
                if request.on_failed:
                    request.on_failed(status_code, request)
                else:
                    self.on_failed(status_code, request)
        except Exception:
            request.status = RequestStatus.error
            t, v, tb = sys.exc_info()
            if request.on_error:
                request.on_error(t, v, tb, request)
            else:
                self.on_error(t, v, tb, request)

    def make_full_url(self, path: str) -> str:
        url = self.url_base + path
        return url

    def request(
            self,
            method: str,
            path: str,
            params: dict = None,
            data: dict = None,
            headers: dict = None,
    ) -> requests.Response:
        request: Request = Request(
            method,
            path,
            params,
            data,
            headers
        )
        request = self.sign(request)

        url = self.make_full_url(request.path)

        response = requests.request(
            request.method,
            url,
            headers=request.headers,
            params=request.params,
            data=request.data,
            proxies=self.proxies,

        )
        return response
