from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Set
from uuid import UUID

import sqlalchemy
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.sql.schema import Table

Base = declarative_base()

types = {
    str: sqlalchemy.String,
    int: sqlalchemy.Integer,
    float: sqlalchemy.Float,
    bool: sqlalchemy.Boolean,
    list: sqlalchemy.ARRAY,
    dict: sqlalchemy.JSON,
    datetime: sqlalchemy.DateTime,
    date: sqlalchemy.Date,
    time: sqlalchemy.Time,
    timedelta: sqlalchemy.Interval,
    UUID: sqlalchemy.UUID,
    Decimal: sqlalchemy.Numeric,
    bytes: sqlalchemy.LargeBinary,
    bytearray: sqlalchemy.LargeBinary,
    memoryview: sqlalchemy.LargeBinary,
    Enum: sqlalchemy.Enum,
    None: sqlalchemy.Null,
}


def convert_type(type_: type) -> type:
    if type_ in types:
        return types[type_]
    return type_


class Nothing:
    ...


_ = Nothing


class Entity:
    def __init__(
        self,
        default=Nothing,
        regexes: List = None,
        required: bool = False,
        unique: bool = False,
        output_function: callable = None,
        blank: bool = False,
        null: bool = False,
        type_: type = str,
    ):
        self.default = default
        self.regexes = regexes
        self.required = required
        self.unique = unique
        self.output_function = output_function
        self.blank = blank
        self.null = null
        self.type_ = type_

    def column(self):
        print(convert_type(self.type_))
        return Column(
            convert_type(self.type_),
            default=self.default,
            nullable=self.null,
            unique=self.unique,
        )


def find_type(value, anonation: type = Nothing, index: int = 7) -> type:
    if value is Nothing:
        if anonation is Nothing:
            raise NameError
        return anonation

    if len(value) == 0:
        if anonation is Nothing:
            raise NameError
        return anonation

    if len(value) < index:
        if anonation is Nothing:
            if value[0] is Nothing:
                raise NameError
            else:
                return type(value[0])
        return anonation
    return value[index]


class DBBase(Table):
    def __init__(self) -> None:
        pass

    @classmethod
    def models(cls) -> Set[DeclarativeMeta]:
        _models = set()
        for subclass in cls.__subclasses__():
            class_attrs = {"__tablename__": subclass.__name__.lower()}
            primary_key = Column(Integer, primary_key=True)
            annonations = subclass.__annotations__
            print(vars(subclass))
            for attr_name, attr_value in vars(subclass).items():
                if attr_name.startswith("__"):
                    continue
                annonation = annonations.get(attr_name, Nothing)
                if isinstance(attr_value, Entity):
                    class_attrs[attr_name] = attr_value.column()
                if not isinstance(attr_value, (tuple, list)):
                    if annonation is not Nothing:
                        class_attrs[attr_name] = Entity(
                            default=attr_value, type_=annonation
                        ).column()
                    else:
                        class_attrs[attr_name] = Entity(
                            type_=find_type(attr_value, anonation=annonation, index=7)
                        ).column()
                else:
                    print(attr_value)
                    class_attrs[attr_name] = Entity(
                        *attr_value,
                        type_=find_type(attr_value, anonation=annonation, index=7)
                    ).column()
            # if some thing is anonnated but not in the vars
            for annonation_name, annonation_value in annonations.items():
                if annonation_name not in vars(subclass):
                    class_attrs[annonation_name] = Entity(
                        type_=annonation_value
                    ).column()
            class_attrs["id"] = primary_key
            model = type(subclass.__name__, (Base,), class_attrs)
            _models.add(model)
        print(type(model))
        return _models

    @classmethod
    def create(
        cls,
        models: List = None,
        engine=create_engine("sqlite:///data.sqlite"),
        Session=sessionmaker,
    ):
        if models is None:
            models = cls.models()
        Base.metadata.create_all(engine)
        return Session(bind=engine)


class Tag(DBBase):
    name: str = ("", ["TYPES_REGEX"], None)


class Type(DBBase):
    name: str = ("", ["TYPES_REGEX"], None)


class Timestamp(DBBase):
    name: str = ("", ["TIMESTAMP_REGEX"], None)


class News(DBBase):
    title: str = ("", ["TITILE_REGEX"], None)
    summary: str = ("", ["SUMMARY_REGEX"], None)
    content: str = ("", ["CONTENT_REGEXES"], None)
    tags_id: int = (0, [], None)
    types_id: int = (0, [], None)
    timestamp_id: int = (0, [], None)
    url: str = ("", [], None)
    id: int = (0, [], None)
    source: str = ("entekhab", [], None)
    category: str = ("", [], None)
    image: str = ("", [], None)
    hello: str


DBBase.create()
