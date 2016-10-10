import sys

from sqlalchemy import Table, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True)
	email = Column(String(100), nullable=False)
	service = Column(String(20), nullable=False)

class Category(Base):
	__tablename__ = 'category'
	id = Column(Integer, primary_key=True)
	name = Column(String(40), nullable=False)
	description = Column(Text)
	user_id = Column(Integer, ForeignKey('user.id'))
	created = Column(DateTime, default=datetime.datetime.utcnow)


class CategorySubItem(Base):
	__tablename__ = 'category_sub_item'
	id = Column(Integer, primary_key=True)
	name = Column(String(40), nullable=False)
	description = Column(Text)
	category_id = Column(Integer, ForeignKey('category.id'))
	user_id = Column(Integer, ForeignKey('user.id'))
	created = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)