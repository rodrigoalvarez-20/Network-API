from flask import make_response

def netapi_response(data, status):
    response = make_response(data, status)
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers['Access-Control-Allow-Origin'] = "*"
    return response
