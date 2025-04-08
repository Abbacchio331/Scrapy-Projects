import scrapy
from regex import findall, sub
import json


payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}
headers = {'Content-Type': 'application/json'}


class MyWorkDayJobsSpider(scrapy.Spider):
    name = 'myworkdayjobs_spider'
    start_urls = ['https://agilent.wd5.myworkdayjobs.com/en-US/Agilent_Student_Careers']
    jobs = []
    seen_jobs = 0
    job_count = 0

    def start_requests(self):
        for start_url in self.start_urls:
            yield scrapy.Request(url=start_url, callback=self.parse_main_page)

    def parse_main_page(self, response):
        tenant = findall(r'tenant\s*:\s*"\s*([^"]*?)\s*"', response.text)
        app_name = findall(r'appName\s*:\s*"\s*([^"]*?)\s*"', response.text)
        site_id = findall(r'siteId\s*:\s*"\s*([^"]*?)\s*"', response.text)
        if tenant and app_name and site_id:
            shortened_start_url = sub(r"(\A.*?\.com).*", r"\1", response.url)
            job_list_url = f"{shortened_start_url}/wday/{app_name[0]}/{tenant[0]}/{site_id[0]}/jobs"
            yield scrapy.Request(url=job_list_url, method='POST', body=json.dumps(payload), headers=headers, callback=self.parse_main_job_list)
        else:
            yield f"At least one of the following has not been found on {response.url}.\n- tenant\n- appName\n- siteId"

    def parse_main_job_list(self, response):
        data = json.loads(response.text)
        self.job_count = int(data['total'])
        jobs_external_paths = [sub(r"/jobs\s*\Z", data['jobPostings'][i]['externalPath'], response.url) for i in range(len(data['jobPostings']))]
        for job_external_path in jobs_external_paths:
            yield scrapy.Request(url=job_external_path, method='GET', headers=headers, callback=self.parse_individual_jobs)
        self.seen_jobs = 20
        while self.job_count > self.seen_jobs:
            next_page_payload = {"appliedFacets": {}, "limit": 20, "offset": self.seen_jobs, "searchText": ""}
            yield scrapy.Request(url=response.url, method='POST', body=json.dumps(next_page_payload), headers=headers, callback=self.parse_next_page)
        yield {
            "job_count": self.job_count,
            "data": self.jobs
        }

    def parse_individual_jobs(self, response):
        data = json.loads(response.text)
        self.jobs.append(data)

    def parse_next_page(self, response):
        data = json.loads(response.text)
        jobs_external_paths = [sub(r"/jobs\s*\Z", data['jobPostings'][i]['externalPath'], response.url) for i in range(len(data['jobPostings']))]
        for job_external_path in jobs_external_paths:
            yield scrapy.Request(url=job_external_path, method='GET', headers=headers, callback=self.parse_individual_jobs)
        self.seen_jobs += 20

    def closed(self, _):
        with open("output.json", "w+", encoding="utf-8") as f:
            json.dump({"job_count": len(self.jobs), "data": self.jobs}, f, ensure_ascii=False, indent=2)
