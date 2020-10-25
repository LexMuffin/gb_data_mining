from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models as models

engine = create_engine('sqlite:///gb_blog.db')
models.Base.metadata.create_all(bind=engine)
SessionMaker = sessionmaker(bind=engine)