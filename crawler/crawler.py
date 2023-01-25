from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
import lxml
from sqlalchemy.orm import sessionmaker
from database.database import engine, WebPageDB
from htmldate import find_date
from datetime import datetime
from typing import List, Dict
import time
import socket
import requests
import copy
import os
import regex
from tqdm import tqdm

class TimoutRobotFileParser(RobotFileParser):
    def __init__(self, url='', timeout=60):
        super().__init__(url)
        self.timeout = timeout

    def read(self):
        """Reads the robots.txt URL and feeds it to the parser."""
        try:
            f = urlopen(self.url, timeout=self.timeout)
        except HTTPError as err:
            if err.code in (401, 403):
                self.disallow_all = True
            elif err.code >= 400:
                self.allow_all = True
        else:
            raw = f.read()
            self.parse(raw.decode("utf-8").splitlines())

class Crawler:

    def __init__(self, urls=[],n_pages : int = 50):
        self.visited_urls = []
        self.urls_to_visit : List = urls 
        self.can_fetch : Dict[str,bool] = {}
        self.known_sitemap : Dict[str,List] = {}
        self.n_pages = n_pages
        self.site_map_to_visit = []
        self.visited_site_map = []
        self.pbar = tqdm(total = self.n_pages)
    def get_site_map_urls(self,url):
        parse = urlparse(url)
        base_url = f"{parse.scheme}://{parse.netloc}"
        url_robot = base_url + "/robots.txt"
        if base_url in self.known_sitemap.keys() :
            all_sitemap = self.known_sitemap[base_url]
        else :
            try:
                robot = TimoutRobotFileParser(timeout=2)
                robot.set_url(url_robot)
                robot.read()
                all_sitemap = robot.site_maps()
                self.known_sitemap[base_url] = copy.deepcopy(all_sitemap)
            except (URLError,ValueError) :
                all_sitemap=None
        if all_sitemap:
            return all_sitemap
            

    def run_sitemap(self,url):
        all_sitemap = self.get_site_map_urls(url)
        if not all_sitemap:
            return
        for sitemap in all_sitemap :
            parse = urlparse(sitemap)
            if os.path.splitext(parse.path)[-1] == ".xml" and sitemap not in set(self.site_map_to_visit).union(set(self.visited_site_map)):
                self.site_map_to_visit.append(sitemap)
        while len(self.visited_urls) + len(self.urls_to_visit)+1<self.n_pages and self.site_map_to_visit:
            sitemap = self.site_map_to_visit.pop(0)
            self.crawl(sitemap,is_html=False)
            self.visited_site_map.append(sitemap)


    def download_url(self, url:str):
        time.sleep(5)
        try:
            x = requests.get(url,timeout=5)
            data = x.text
        except socket.timeout: 
            data = None
        return data

    def get_linked_urls_xml(self, xml):
        soup = BeautifulSoup(xml, 'xml')
        if soup.find('sitemapindex'):
            for link in soup.find_all('loc'):
                link = regex.findall("<loc>(.*?)</loc>",str(link))
                if link :
                    parse_link = urlparse(link[0])
                    if os.path.splitext(parse_link.path)[-1] == ".xml":
                        link = link[0]
                        if parse_link.path not in [urlparse(item).path for item in list(set(self.site_map_to_visit).union(set(self.visited_site_map)))]:
                            self.site_map_to_visit.append(link)
                            
            return
        paths = []
        for link in soup.find_all('loc'):
            link = regex.findall("<loc>(.*?)</loc>",str(link))
            if link :
                if  os.path.splitext(urlparse(link[0]).path)[-1] != ".xml":
                    link = link[0]
                    paths.append(link)
        return paths

    def get_linked_urls_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        paths = []
        for link in soup.find_all('a'):
            path = link.get('href')
            paths.append(path)
        return paths

    def add_url_to_visit(self, url):
        parse = urlparse(url)
        base_url = f"{parse.scheme}://{parse.netloc}"
        if base_url in self.can_fetch.keys() :
            allow = self.can_fetch[base_url]
        else :
            try:
                url_robot = base_url + "/robots.txt"
                robot = TimoutRobotFileParser(timeout=2)
                robot.set_url(url_robot)
                robot.read()
                allow = robot.can_fetch(useragent="*",url=url)
                self.can_fetch[base_url] = copy.deepcopy(allow)
            except (URLError,ValueError,socket.timeout) :
                allow=False
        if allow:
            self.urls_to_visit.append(url)

    def crawl(self, url, is_html=True):
        try : 
            text = self.download_url(url)
            if not text:
                return 
            all_links = self.get_linked_urls_html(text) if is_html else self.get_linked_urls_xml(text)
            if not all_links:
                return 
            for url in all_links:
                if len(self.visited_urls) + len(self.urls_to_visit)+1>=self.n_pages:
                    break
                else:
                    existing_url = list(set(self.urls_to_visit).union(set(self.visited_urls)).union(set(self.site_map_to_visit)).union(set(self.visited_site_map)))
                    if url not in existing_url:
                        self.add_url_to_visit(url)
                        self.pbar.update(1)
        except socket.timeout:
            pass

    def run(self):
        
        while len(self.visited_urls) + len(self.urls_to_visit)<self.n_pages and self.urls_to_visit:
            url = self.urls_to_visit.pop(0)
            self.run_sitemap(url)
            self.crawl(url)
            self.visited_urls.append(url)
            self.pbar.update(1)
        self.pbar.close()

    def find_date(self,url):
        try :
            date_str = find_date(url)
            date_creation = datetime.strptime(date_str,"%Y-%m-%d").date() if date_str else None
        except ValueError:
            date_creation = None
        return date_creation

    def update_db(self):
        print("update DB")
        Session = sessionmaker(bind=engine)
        session = Session()
        new_urls = {}
        for url in copy.deepcopy(list(set(self.urls_to_visit).union(set(self.visited_urls)))):
            new_urls[url] = WebPageDB(url=url, creation_date=self.find_date(url))

        for each in session.query(WebPageDB).filter(WebPageDB.url.in_(new_urls.keys())).all():
            session.merge(new_urls.pop(each.url))
        # Only add those posts which did not exist in the database 

        session.add_all(new_urls.values())

        # Now we commit our modifications (merges) and inserts (adds) to the database!
        session.commit()
    
    def export(self,path_to_file:str):
        try:
            with open(path_to_file,'w') as f :
                urls = list(set(self.urls_to_visit).union(set(self.visited_urls)))
                f.writelines(line + '\n' for line in urls)
        except (FileNotFoundError):
            print(f"Le chemin vers le fichier {path_to_file} n'est pas correct")