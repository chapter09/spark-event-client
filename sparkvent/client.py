import time
import redis
from multiprocessing import Process
from os import path
from config import Config

from http_req import *
from url_gen import *
from resp_parse import *


# need to make a thread to query periodically
class Client(object):

    def __init__(self, config_file):
        self.config = Config(path.abspath(config_file))
        self.url_gen = UrlGen()
        self.requester = HttpRequester()
        self.app_parser = AppParser(self.config.server)
        self.job_parser = JobParser(self.config.server)
        self.stage_parser = StageParser(self.config.server)
        self.exec_parser = ExecParser(self.config.server)

        # Get parser from config
        self.parser = ParserFactory.get_parser(self.config.type,
                                               self.config.server)

        self.parse_type = ''  # used to inform the parser of parsing type
        self.data = []

        redis_host, redis_port = self.config.redis.split(":")
        self.redis = redis.Redis(host=redis_host, port=redis_port)

    # get all available info (apps, jobs, stages)
    def get_all_info(self):
        data = []
        apps = self.get_all_applications()  # get all app ids
        for app in apps:
            entry = dict()
            entry['application'] = app
            entry['jobs'] = self.get_all_jobs_from_application(app['id'])
            entry['stages'] = self.get_all_stages_from_application(app['id'])
            data.append(entry)

        self.data.append(data)  # add to global data storage
        return data

    def get_executor_info(self):
        data = []
        apps = self.get_all_applications()  # get all app ids

        for app in apps:
            entry = dict()
            entry['application'] = app
            entry['executor'] = self.get_executor_details(app['id'])
            data.append(entry)

        return data

    ###########################################################################
    # methods for single aspect
    ###########################################################################

    def get_all_applications(self, option={}):
        rest_api = ''
        self.parse_type = 'appid'
        data = self._get_data(rest_api, self.app_parser, option)
        return data

    def get_all_jobs_from_application(self, app_id, status=''):
        rest_api = app_id + '/' + 'jobs'
        self.parse_type = 'jobid'

        # get the options
        if status: option = {'status' : status}
        else: option = {}

        data = self._get_data(rest_api, self.job_parser, option)
        # application.jobs = data
        return data

    def get_job_from_application(self, app_id, job_id):
        rest_api = app_id + '/' + 'jobs' + '/' + job_id
        self.parse_type = ''  # TODO: define a parse type
        data = self._get_data(rest_api, self.job_parser)
        return data

    def get_all_stages_from_application(self, app_id, status=''):
        rest_api = app_id + '/' + 'stages'
        self.parse_type = 'stageid'

        # get the options
        if status: option = {'status' : status}
        else: option = {}

        data = self._get_data(rest_api, self.stage_parser, option)
        return data

    def get_all_attempts_from_stage(self, app_id):
        pass

    def get_attempts_for_stage_from_application(self, app_id, stage_id):
        rest_api = app_id + '/' + 'stages' + '/' + stage_id
        self.parse_type = 'attemptid'

        data = self._get_data(rest_api, self.stage_parser)
        return data

    def get_attempt_detail_for_stage_from_stage(self, app_id, stage_id, attempt_id):
        rest_api = '/'.join([app_id, 'stages', stage_id, attempt_id])
        self.parse_type = 'attemptdetail'

        data = self._get_data(rest_api, self.stage_parser)
        return data

    def get_executor_details(self, app_id):
        rest_api = '/'.join([app_id, 'executors'])

        data = self._get_data(rest_api, self.exec_parser)

        return data

    def _get_data(self, rest_api, parser, option={}):
        url = self.url_gen.get_url(self.config.server, rest_api, option)
        json_response = self.requester.single_request(url)

        if option == {}:
            response = parser.parse_json(json_response, self.parse_type)
        elif option['type'] == 'redis':
            response = parser.get_redis_entry(json_response)
        else:
            response = parser.parse_json(json_response, self.parse_type)

        return response

    # Redis structure
    # key: app_id           value: "json"
    # key: app_id:job_id    value: "json"
    # key: app_id:stage_id  value: "json"
    # data = { "key1": "value", "key2": "value", ... }
    def store_info(self, data):

        self.redis.mset(data)
        result = self.redis.mget(data)
        print(result)

    def run_daemon(self):
        process = Process(target=self._daemon_process())
        process.start()
        process.join()

    def _daemon_process(self):
        while True:
            all_apps = self.get_all_applications({'type': 'redis'})
            self.store_info(all_apps)
            time.sleep(self.config.period)
