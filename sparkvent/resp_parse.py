# HTTP response (JSON) parser
from url_gen import *
from http_req import *


class AbstractParser(object):
    BASE_ENDPOINT = '/applications'

    def __init__(self):
        self.http_requester = http_req()

    def get_url(self, app_type):
        raise NotImplementedError

    @staticmethod
    def factory(type):
        if type == "AppParser": return AppParser()
        if type == "JobParser": return JobParser()


class AppParser(AbstractParser):
    GET_APPID = '/applications'

    def __init__(self):
        super(AppParser, self).__init__()
        self.aID = []  # all application IDs

    def get_basic_app_info(self):
        request_url = self.get_url("app")
        app_info = self.http_requester.single_request(request_url)
        return app_info

    def get_url(self, app_type):
        if (app_type == "app"):
            return generate_url('142.150.208.177', self.GET_APPID, {})


class JobParser(AbstractParser):
    def __init__(self):
        super(JobParser, self).__init__()

    def get_all_jobs_from_app(self, app_id):
        endpoint = self.BASE_ENDPOINT + '/' + app_id + '/jobs'
        jobs_info = self.get_info(endpoint)
        return jobs_info

    def get_job_from_app(self, app_id, job_id):
        endpoint = self.BASE_ENDPOINT + '/' + app_id + '/jobs/' + job_id
        job_info = self.get_info(endpoint)
        return job_info

    def get_info(self, endpoint):
        request_url = generate_url('142.150.208.177', endpoint, {})
        info = self.http_requester.single_request(request_url)
        return info


class StageParser(AbstractParser):
    def __init__(self):
        super(StageParser, self).__init__()

    def get_url(self, app_type):
        pass


class ParserFactory(object):

    @staticmethod
    def get_parser(parser_type):
        if parser_type == "App":
            return AppParser()
        elif parser_type == "Job":
            return JobParser()
        elif parser_type == "Stage":
            return StageParser()
        else:
            return None

