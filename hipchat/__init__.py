try:
    from urllib.parse import urljoin
    from urllib.parse import urlencode
    import urllib.request as urlrequest
except ImportError:
    from urlparse import urljoin
    from urllib import urlencode
    import urllib2 as urlrequest
import json
import requests
import os

API_URL_V1 = 'https://api.hipchat.com/v1/'
API_URL_V2 = 'https://api.hipchat.com/v2/'

FORMAT_DEFAULT = 'json'


class HipChat(object):
    def __init__(self, token=None, url=API_URL_V1, format=FORMAT_DEFAULT):
        self.url = url
        self.token = token
        self.format = format
        self.opener = urlrequest.build_opener(urlrequest.HTTPSHandler())

    class RequestWithMethod(urlrequest.Request):
        def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=False, http_method=None):
            urlrequest.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)
            if http_method:
                self.method = http_method

        def get_method(self):
            if self.method:
                return self.method
            return urlrequest.Request.get_method(self)

    def method(self, url, method="GET", parameters=None, timeout=None):
        method_url = urljoin(self.url, url)

        if method == "GET":
            if not parameters:
                parameters = dict()

            parameters['format'] = self.format
            parameters['auth_token'] = self.token

            query_string = urlencode(parameters)
            request_data = None
        else:
            query_parameters = dict()
            query_parameters['auth_token'] = self.token

            query_string = urlencode(query_parameters)

            if parameters:
                request_data = urlencode(parameters).encode('utf-8')
            else:
                request_data = None

        method_url = method_url + '?' + query_string

        req = self.RequestWithMethod(method_url, http_method=method, data=request_data)
        response = self.opener.open(req, None, timeout).read()

        return json.loads(response.decode('utf-8'))

    def send_file_room(self, room_id, message, file_path):

        if not os.path.isfile(file_path):
            raise ValueError("File '{0}' does not exist".format(file_path))
        if len(message) > 1000:
            raise ValueError('Message too long')

        url = "{0}/room/{1}/share/file".format(API_URL_V2, room_id)
        headers = {'Content-type': 'multipart/related; boundary=boundary123456',\
                   'Authorization': "Bearer " + self.token}
        msg = json.dumps({'message': message, 'from': 'Ceren Sahin'})
        payload = ("\n"
                   "--boundary123456\n"
                   "Content-Type: application/json; charset=UTF-8\n"
                   "Content-Disposition: attachment; name=\"metadata\"\n"
                   "\n"
                   "{0}\n"
                   "--boundary123456\n"
                   "Content-Disposition: attachment; name=\"file\"; filename=\"{1}\"\n"
                   "\n"
                   "{2}\n"
                   "--boundary123456--\n"
        ).format(msg, os.path.basename(file_path), open(file_path, 'rb').read())

        r = requests.post(url, headers=headers, data=payload)
        r.raise_for_status()

    def list_rooms(self):
        return self.method('rooms/list')

    def list_users(self):
        return self.method('users/list')

    def message_room(self, room_id='', message_from='', message='', message_format='text', color='', notify=False):
        parameters = dict()
        parameters['room_id'] = room_id
        parameters['from'] = message_from[:15]
        parameters['message'] = message
        parameters['message_format'] = message_format
        parameters['color'] = color

        if notify:
            parameters['notify'] = 1
        else:
            parameters['notify'] = 0

        return self.method('rooms/message', 'POST', parameters)

    def find_room(self, room_name=''):
        rooms = self.list_rooms()['rooms']
        for x in range(0, len(rooms)):
            if rooms[x]['name'] == room_name:
                return rooms[x]
        return None

    def find_user(self, user_name=''):
        users = self.list_users()['users']
        for x in range(0, len(users)):
            if users[x]['name'] == user_name:
                return users[x]
