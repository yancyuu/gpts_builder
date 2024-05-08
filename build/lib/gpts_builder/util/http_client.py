import requests
import httpx
import backoff

class HTTPClient:
    
    def __init__(self):
        # 创建一个持久的 AsyncClient 实例
        self.async_client = httpx.AsyncClient()
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        # 确保在类实例不再使用时关闭 client
        await self.async_client.aclose()

    def post(self, url, json=None, headers=None, timeout=60, max_retries=3):
        """
        执行同步的 HTTP POST请求，并支持自定义超时和重试次数。
        
        参数:
            url (str): 请求的 URL。
            json (dict, optional): 这是要发送的数据。默认为 None。
            timeout (int, optional): 请求超时时间（秒）。默认为 60 秒。
            max_retries (int, optional): 失败时的最大重试次数。默认为 3。
        
        返回:
            dict: 从服务器返回的 JSON 数据。
        
        异常:
            HTTPError: 如果响应状态码表示错误。
        """
        @backoff.on_exception(backoff.expo,
                              (requests.exceptions.RequestException, httpx.HTTPError),
                              max_tries=max_retries)
        def request_with_backoff():
            response = requests.post(url, json=json, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.json()

        return request_with_backoff()
    
    def get(self, url, params=None, headers=None, timeout=60, max_retries=3):
        """
        执行同步的 HTTP GET请求，并支持自定义超时和重试次数。
        
        参数:
            url (str): 请求的 URL。
            params (dict, optional): 要发送的数据。默认为 None。
            timeout (int, optional): 请求超时时间（秒）。默认为 60 秒。
            max_retries (int, optional): 失败时的最大重试次数。默认为 3。
        
        返回:
            dict: 从服务器返回的 JSON 数据。
        
        异常:
            HTTPError: 如果响应状态码表示错误。
        """
        @backoff.on_exception(backoff.expo,
                              (requests.exceptions.RequestException, httpx.HTTPError),
                              max_tries=max_retries)
        def request_with_backoff():
            response = requests.get(url, params=params, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.json()

        return request_with_backoff()

    async def post_async(self, url, json=None, headers=None, timeout=60, max_retries=3):
        """
        执行异步的 POST 请求，并支持自定义超时和重试次数。
        
        参数:
            url (str): 请求的 URL。
            json (dict, optional): 这是要发送的数据。默认为 None。
            timeout (int, optional): 请求超时时间（秒）。默认为 60 秒。
            max_retries (int, optional): 失败时的最大重试次数。默认为 3。
        
        返回:
            dict: 从服务器返回的 JSON 数据。
        
        异常:
            ValueError: 如果提供了不支持的 HTTP 方法。
        """
        @backoff.on_exception(backoff.expo,
                              httpx.HTTPError,
                              max_tries=max_retries)
        async def request_with_backoff():
            response = await self.async_client.post(url, json=json, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.json()

        return await request_with_backoff()
    
    async def get_async(self, url, params=None, headers=None, timeout=60, max_retries=3):
        """
        执行异步的 HTTP GET 或 POST 请求，并支持自定义超时和重试次数。
        
        参数:
            url (str): 请求的 URL。
            params (dict, optional): 这是要发送的数据。默认为 None。
            timeout (int, optional): 请求超时时间（秒）。默认为 60 秒。
            max_retries (int, optional): 失败时的最大重试次数。默认为 3。
        
        返回:
            dict: 从服务器返回的 JSON 数据。
        
        异常:
            HTTPError: 如果响应状态码表示错误。
            ValueError: 如果提供了不支持的 HTTP 方法。
        """
        @backoff.on_exception(backoff.expo,
                              httpx.HTTPError,
                              max_tries=max_retries)
        async def request_with_backoff():
            response = await self.async_client.get(url, params=params, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response.json()

        return await request_with_backoff()

http_client = HTTPClient()