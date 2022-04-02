from dotenv import load_dotenv

from app.services.etl.article_etl import ArticleETL

load_dotenv(".env")


if __name__ == "__main__":
    ArticleETL().run()
