from crawler import Crawler
from database.database import init_db
import click

@click.command()
@click.option('--n_pages', default=50)
@click.option('--add_db', is_flag=True)
@click.option('--export_path_full')
@click.option('--url', default='https://ensai.fr/')
def main(n_pages,add_db,url,export_path_full):
    crawler = Crawler(urls=[url],n_pages=n_pages)
    crawler.run()
    if export_path_full:
        crawler.export(export_path_full)
    if add_db:
        init_db()
        crawler.update_db()


if __name__== '__main__':
    main()