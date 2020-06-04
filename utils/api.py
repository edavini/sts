import requests
import json
from . import filler

VALID_HTTP_METHODS = {
    'GET':      ['url'],
    'PATCH':    ['url', 'data'],
    'PUT':      ['url', 'data'],
    'POST':     ['url', 'data'],
    'DELETE':   ['url'],
}


class APIConfig:
    """
    Support API Configuration Class
    Available data:
    * base_url: string | The base url of all calls to be done. Optional. Default is an empty string for easier concat
    """
    def __init__(self, base_url=''):
        self.base_url = base_url

    @classmethod
    def from_config(cls, config_object):
        base_url = config_object.get('baseUrl')
        return cls(base_url=base_url)


def call(step, responses, config: APIConfig):
    """
    Main API Caller
    :param step:
    :param responses:
    :param config:
    :return:
    """
    req = step.get('request')
    validate_request(req)

    method = req.get('method', None)
    url = filler.fill_regex(req['url'].replace('{{baseUrl}}', config.base_url), responses)
    payload = req.get('data', None)
    if payload is not None:
        payload_clean = filler.fill_regex(payload, responses)
        payload = json.loads(payload_clean)
    headers = None

    print('Calling {method} @ {url}'.format(method=method, url=url))
    response_raw = requests.request(method=method, url=url, json=payload, headers=headers)

    response_json = {}
    try:
        response_json = response_raw.json()
    except ValueError:
        print('Invalid json')
        # no JSON: nothing to do

    print('Response ({number}) {status}: {response}'.format(number=len(responses), status=response_raw.status_code, response=json.dumps(response_json)))
    response = build_response(step, response_raw, payload)
    return response


def mock(step, responses, config: APIConfig):
    ''' TODO'''
    return 0


def build_response(step, response_raw, payload):
    response = {
        "type": "HTTP",
        "name": step.get("name", "Unnamed Request"),
        "description": step.get("name", "Undescribed Request"),
        "headers": dict(response_raw.headers),
        "body": response_raw.text,
        "status": response_raw.status_code,
        "request": {
            "body": payload,
            "headers": dict(response_raw.request.headers),
            "method": response_raw.request.method,
            "url": response_raw.request.url
        }
    }
    try:
        response["json"] = response_raw.json()
    except json.JSONDecodeError:
        print('Unable to parse json response')
        response["json"] = None
    return response


# simple validation
def validate_request(req):
    name = req.get('name', 'UNNAMED REQUEST')
    method = req.get('method', None)
    if method is None:
        raise Exception('MISSING METHOD')
    if method not in VALID_HTTP_METHODS.keys():
        raise Exception('INVALID METHOD {method}'.format(method=method))

    configs = VALID_HTTP_METHODS.get(method)
    for config in configs:
        if req.get(config, None) is None:
            raise Exception('MISSING {config} FROM {name}'.format(config=config, name=name))

    return True


