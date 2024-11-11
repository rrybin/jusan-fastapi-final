from fastapi import FastAPI, Header, Response, status, Request
from typing import Union
from pydantic import BaseModel
import re
import prometheus_client
import time

app = FastAPI()
metrics_app = prometheus_client.make_asgi_app()
app.mount("/metrics", metrics_app)
http_requests_total = prometheus_client.Counter('http_requests_total', 'Number of HTTP requests received', ['method', 'endpoint'])
http_requests_milliseconds = prometheus_client.Histogram('http_requests_milliseconds', 'Duration of HTTP requests in milliseconds', ['method', 'endpoint'])
result = []

async def log_request_middleware(request: Request, call_next):
    request_start_time = time.monotonic()
    response = await call_next(request)
    request_duration = time.monotonic() - request_start_time
    http_requests_milliseconds.labels(request.method, request.url.path).observe(request_duration)
    # log_data = {
    #     "method": request.method,
    #     "path": request.url.path,
    #     "duration": request_duration
    # }
    # log.info(log_data)
    return response

app.middleware("http")(log_request_middleware)

class Elem(BaseModel):
    element: str

class expresion(BaseModel):
    expr: str

@app.get("/")
def read_root():
    http_requests_total.labels('GET', '/').inc
    #http_requests_milliseconds.labels('GET', '/').
    return {"Hello": "World"}


@app.get("/sum1n/{number}")
def sum1n(number):
    last_sum1n = prometheus_client.Gauge('last_sum1n', 'Value stores last result of sum1n')
    last_sum1n.set(number)
    http_requests_total.labels('GET', '/sum1n/').inc
    result = sum(i for i in range(int(number) + 1))
    return {"result": result}


# 0 1 1 2 3
@app.get("/fibo")
def fibo(n: int):
    last_fibo = prometheus_client.Gauge('last_fibo', 'Value stores last result of fibo')
    http_requests_total.labels('GET', '/fibo').inc
    count = 1
    n1, n2 = 0, 1
    while count < n - 1:
        fib = n1 + n2
        n1, n2 = n2, fib
        count += 1
    last_fibo.set(fib)
    return {"result": fib}


@app.post("/reverse")
def reverse(string: Union[str, None] = Header(default=None)):
    http_requests_total.labels('POST', '/reverse').inc
    return {"result": string[::-1]}


@app.put("/list")
def add_to_list(element: Elem):
    http_requests_total.labels('PUT', '/list').inc
    list_size = prometheus_client.Gauge('list_size', 'Value stores current list size')
    list_size.set(len(result))
    result.append(element.element)


@app.get("/list")
def otput_list():
    http_requests_total.labels('GET', '/list').inc
    return {"result:": result}


@app.post("/calculator", description="Sample: 1,+,1", status_code=200)
def calculator(expresion: expresion, response: Response):
    last_calculator = prometheus_client.Gauge('last_calculator', 'Value stores last result of calculator')
    errors_calculator_total = prometheus_client.Counter('errors_calculator_total', 'Number of errors in calculator')
    http_requests_total.labels('POST', '/calculator').inc
    templ = re.compile(r"^\d*,[\+\-\*\/],\d*$")
    if not templ.fullmatch(expresion.expr):
        response.status_code = status.HTTP_400_BAD_REQUEST
        errors_calculator_total.inc()
        return {"error:": "invalid"}
    rest = expresion.expr.split(sep=',')
    if rest[1] == "+":
        return {"result": int(rest[0]) + int(rest[2])}
        last_calculator.set(int(rest[0]) + int(rest[2]))
    elif rest[1] == "-":
        return {"result": int(rest[0]) - int(rest[2])}
        last_calculator.set(int(rest[0]) - int(rest[2]))
    elif rest[1] == "*":
        return {"result": int(rest[0]) * int(rest[2])}
        last_calculator.set(int(rest[0]) * int(rest[2]))
    elif rest[1] == "/":
        try:
            return {"result": int(rest[0]) / int(rest[2])}
            last_calculator.set(int(rest[0]) / int(rest[2]))
        except:
            response.status_code = status.HTTP_403_FORBIDDEN
            errors_calculator_total.inc()
            return {"result": "zerodiv"}
