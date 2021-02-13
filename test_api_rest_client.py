import unittest
import warnings

from api_rest_client import *
from trader_constant import Exchange

REST_HOST = "https://1token.trade/api"


def on_test(data: dict, request: Request) -> None:
    print(data)
    print(request)


def on_failed(status_code: int, request: Request) -> None:
    msg = f"委托失败：{status_code}, 信息为：{request.response.text}"
    print(msg)


class MyTestCase(unittest.TestCase):
    def on_error(self, exception_type: type, exception_value: Exception, tb: TracebackType, request: Request) -> None:

        msg = f"触发异常，状态码:{exception_type}, 信息：{exception_value}"
        print(msg)
        sys.stderr.write(
            self.rest_client.exception_detail(exception_type, exception_value, tb, request)
        )

    def print_q(self):
        while not self.rest_client._queue.empty():
            try:
                e = self.rest_client._queue.get(block=True, timeout=1)
                print(e)
            except Empty:
                pass

    def setUp(self) -> None:
        warnings.simplefilter('ignore', ResourceWarning)
        self.request_status: RequestStatus = RequestStatus.ready
        self.rest_client: RestClient = RestClient()
        self.rest_client.init(url_base=REST_HOST, proxy_host="", proxy_port=0)
        self.rest_client.start(3)
        print(self.rest_client._active)

    def test_request_status(self):
        # print(self.request_status.name)
        # print(self.request_status.value)
        self.assertEqual(0, self.request_status.value)
        self.assertEqual('ready', self.request_status.name)

    def test_request(self):
        request = Request('Get', '/lqw', {'id': 1}, 'data', {'header': None}, None, None, None, None)
        expected = ['request : Get /lqw ready because terminated: ', "headers: {'header': None}", "params: {'id': 1}",
                    'data: data', 'response:', '']

        # print('\n'.join(expected))
        # print(str(request).split('\n'))
        self.assertEqual('\n'.join(expected), str(request))

    def test_request_start(self):
        req = self.rest_client.add_request(
            "GET",
            "/v1/basic/contracts?exchange={}".format(Exchange.HUOBI),
            callback=on_test,
            on_failed=on_failed
        )
        print(req)

    def tearDown(self) -> None:
        self.rest_client.stop()
        self.rest_client.join()


if __name__ == '__main__':
    unittest.main(verbosity=1)
