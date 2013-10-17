"""
Classes for handling a HTTP request/response flow.
"""

from oauth2.compatibility import parse_qs

class SiteAdapter(object):
    """
    Interact with a user.
    
    Display HTML or redirect the user agent to another page of your website
    where she can do something before being returned to the OAuth 2.0 server.
    """
    def authenticate(self, request, environ, scopes):
        """
        Authenticates a user and checks if she has authorized access.
        
        :param request: An instance of :class:`oauth2.web.Request`.
        :param environ: Environment variables of the request.
        :param scopes: A list of strings with each string being one requested
                       scope.
        :return: A value that is not ``None`` if the user was authenticated
                 successfully and allowed the access. This value will be
                 stored together with the generated access token.
        """
        pass
    
    def render_auth_page(self, request, response, environ):
        """
        Defines how to display a confirmation page to the user.

        :param request: An instance of :class:`oauth2.web.Request`.
        :param response: An instance of :class:`oauth2.web.Response`.
        :param environ: Environment variables of the request.
        :return: The response passed in a parameter.
                 It can contain HTML or issue a redirect.
        """
        pass
    
    def user_has_denied_access(self, request):
        """
        Checks if the user has denied access. This will lead to python-oauth2
        returning a "acess_denied" response to the requesting client app.

        :param request: An instance of :class:`oauth2.web.Request`.
        :return: Return ``True`` if the user has denied access.
        """
        pass

class Request(object):
    """
    Contains data of the current HTTP request.
    """
    def __init__(self, env):
        """
        :param env: Wsgi environment
        """
        self.method       = env["REQUEST_METHOD"]
        self.query_params = {}
        self.query_string = env["QUERY_STRING"]
        self.path         = env["PATH_INFO"]
        self.post_params  = {}
        
        for param,value in parse_qs(env["QUERY_STRING"]).items():
            self.query_params[param] = value[0]
        
        if (self.method == "POST"
            and env["CONTENT_TYPE"] == "application/x-www-form-urlencoded"):
            self.post_params = {}
            content = env['wsgi.input'].read(int(env['CONTENT_LENGTH']))
            post_params = parse_qs(content)
            
            for param,value in post_params.items():
                self.post_params[param] = value[0]
    
    def get_param(self, name, default=None):
        """
        Returns a param of a GET request identified by its name.
        """
        try:
            return self.query_params[name]
        except KeyError:
            return default
    
    def post_param(self, name, default=None):
        """
        Returns a param of a POST request identified by its name.
        """
        try:
            return self.post_params[name]
        except KeyError:
            return default

class Response(object):
    """
    Contains data returned to the requesting user agent.
    """
    def __init__(self):
        self.status_code = 200
        self._headers    = {"Content-type": "text/html"}
        self.body        = ""
    
    @property
    def headers(self):
        return self._headers
    
    def add_header(self, header, value):
        self._headers[header] = str(value)

class Wsgi(object):
    HTTP_CODES = {200: "200 OK",
                  301: "301 Moved Permanently",
                  302: "302 Found",
                  400: "400 Bad Request",
                  404: "404 Not Found"}
    
    def __init__(self, server, authorize_uri="/authorize", env_vars=None,
                 request_class=Request, token_uri="/token"):
        self.authorize_uri = authorize_uri
        self.env_vars      = env_vars
        self.request_class = request_class
        self.server        = server
        self.token_uri     = token_uri
        
        self.server.authorize_path = authorize_uri
        self.server.token_path     = token_uri
    
    def __call__(self, env, start_response):
        environ = {}
        
        if (env["PATH_INFO"] != self.authorize_uri
            and env["PATH_INFO"] != self.token_uri):
            start_response("404 Not Found",
                           [('Content-type', 'text/html')])
            return ["Not Found"]
        
        request = self.request_class(env)
        
        if isinstance(self.env_vars, list):
            for varname in self.env_vars:
                if varname in env:
                    environ[varname] = env[varname]
        
        response = self.server.dispatch(request, environ)
        
        start_response(self.HTTP_CODES[response.status_code],
                       response.headers.items())
        
        return [response.body]
