from datetime import datetime, time
from decimal import Decimal
from fabric import db

# import inflection
from fabric.modules.generic.loggers import error_logger


class GetDict:
    def as_dict(self):
        """
        Generating a dict that contains of table field(s) and its value(s)
        @return: Final dictionary variable contains a table row data.
        """
        final_dict = {}
        for column in self.__table__.columns:

            if type(getattr(self, column.name)) == datetime:
                setattr(self, column.name, getattr(self, column.name).strftime("%Y-%m-%d %H:%M:%S"))

            # final_dict[inflection.underscore(column.name)] = getattr(self, column.name)
            final_dict[column.name] = getattr(self, column.name)
        return final_dict


class SerializeSQLAResult:
    """
    Generating a dict from list of SQL Alchemy result, i.e. eg: <class 'sqlalchemy.util._collections.result'> objects. Finally returns the dict vars in a list.
    """
    # Object variable initialisation
    sqla_util_results = []

    def __init__(self, sqla_util_results):
        """
        Class constructor. Here sqla_util_results is the list contains <class 'sqlalchemy.util._collections.result'> objects
        @param sqla_util_results: list of <class 'sqlalchemy.util._collections.result'> objects/SQL Alchemy result
        """
        self.sqla_util_results = sqla_util_results

    @staticmethod
    def format_columns(dict_row, key, sqla_result):
        """
        @param dict_row: final dict varible
        @param key: key in the SQLA tuple.
        @param sqla_result: SQLA tuple result.
        @return: Formatted dict variable.
        """
        if not key.startswith('_') and key not in ['keys', 'index', 'count', 'metadata', 'query',
                                                   'query_class']:
            # Here the key is a valid column name
            if type(getattr(sqla_result, key)) is datetime:
                # If the column is of datetime object, convert to standard format string value.
                # Eg: 2012-02-23 18:23:33
                # dict_row[key] = getattr(sqla_util_result, key).strftime("%Y-%m-%d %H:%M:%S")
                # Updated
                dict_row[key] = getattr(sqla_result, key).strftime("%d-%m-%Y")
            elif type(getattr(sqla_result, key)) is time:
                # If the column field is time object, convert to standard format string value.
                # Eg: 8:03 AM
                dict_row[key] = getattr(sqla_result, key).strftime("%#I:%M %p")
            elif type(getattr(sqla_result, key)) is Decimal:
                # If the column field is decimal, convert it into a float
                dict_row[key] = float(getattr(sqla_result, key))
            else:
                dict_row[key] = getattr(sqla_result, key)
        return dict_row

    def serialize_one(self):
        """
        Generating a dict variable from a SQLA result tuple.
        @return: dict variable consisting of SQLA result.
        @rtype:
        """
        dict_row = {}
        for key in dir(self.sqla_util_results):
            self.format_columns(dict_row, key, self.sqla_util_results)

        return dict_row

    def serialize(self):
        """
        Generating the dictionary variable by looping through the list of <class 'sqlalchemy.util._collections.result'> objects
        @return: List of serialized SQLA result.
        """

        final_list = []
        for sqla_util_result in self.sqla_util_results:
            dict_row = {}
            for key in dir(sqla_util_result):
                self.format_columns(dict_row, key, sqla_util_result)

            # Return variable will be a list type.
            final_list.append(dict_row)
        return final_list


class CallSP:
    """
    This generic class helps to execute stored procedures and populates the result.
    """
    # Class variable for storing the given stored procedure query string.
    query = ''
    # Class variable for storing the result of the stored procedure execution.
    result = None

    def __init__(self, query):
        """
        Setting up the class variable query.
        @param query: query string need to be executed.
        """
        self.query = query

    def execute(self):
        """
        Executing the stored procedure from the given string.
        @return: current CallSP instance.
        """
        try:
            # Executing the stored procedure.
            self.result = db.session.execute(self.query)
        except Exception as e:
            error_logger().error(e)
        return self

    def fetchone(self):
        """
        This function acts as a dummy for the SQLA fetchone() function.
        @return: result of the stored procedure execution.
        """
        if self.result is not None:
            # Calling the SQLA fetchone() function only if the execution of the SP had performed successfully.
            item = self.result.fetchone()
            return_dict = {}
            keys = item.keys()
            values = item
            for key, value in zip(keys, values):
                return_dict[key] = value

            # Successfully populated the result. Returning the result as a dict variable.
            return return_dict

        return None

    def fetchall(self):
        """
        This function acts as a dummy for the SQLA fetchall() function.
        @return: result of the stored procedure execution.
        """
        if self.result is not None:
            # Calling the SQLA fetchall() function only if the execution of the SP had performed successfully.
            all_items = self.result.fetchall()
            return_list = []
            for item in all_items:
                keys = item.keys()
                values = item.values()
                dict_row = {}
                for key, value in zip(keys, values):
                    # Type conversion for serialization.
                    if type(value) is Decimal:
                        dict_row[key] = float(value)
                    elif type(value) is datetime:
                        dict_row[key] = value.strftime("%d-%m-%Y")
                    elif type(value) is time:
                        dict_row[key] = value.strftime("%#I:%M %p")
                    else:
                        dict_row[key] = value
                return_list.append(dict_row)
            # Successfully populated the result. Returning the result as a list variable.
            return return_list
        return None
