import os
import pytest
from mydb import MyDB
from unittest.mock import call

def describe_MyDB():
    
    @pytest.fixture(autouse=True, scope="session")
    def verify_filesystem_is_not_touched():
        yield
        assert not os.path.isfile("mydatabase.db")

    def describe_init():
        def describe_when_the_database_file_exists():
            def it_assigns_the_fname_attribute(mocker):
                mocker.patch("os.path.isfile", return_value=True)
                db = MyDB("mydatabase.db")
                assert db.fname == "mydatabase.db"

        def describe_when_the_database_file_does_not_exist():
            def it_creates_an_empty_database(mocker):
                mock_isfile = mocker.patch("os.path.isfile", return_value=False)
                mock_open = mocker.patch("builtins.open", mocker.mock_open())
                mock_dump = mocker.patch("pickle.dump")

                db = MyDB("mydatabase.db")

                mock_isfile.assert_called_once_with("mydatabase.db")
                mock_open.assert_called_once_with("mydatabase.db", "wb")
                mock_dump.assert_called_once_with([], mock_open.return_value)

    def describe_loadStrings():
        def it_loads_and_returns_an_array_from_a_file(mocker):
            mocker.patch("os.path.isfile", return_value=True)
            mock_open = mocker.patch("builtins.open", mocker.mock_open())
            mock_load = mocker.patch("pickle.load", return_value=["1", "2", "3"])
            db = MyDB("mydatabase.db")

            arr = db.loadStrings()

            mock_open.assert_called_once_with("mydatabase.db", "rb")
            mock_load.assert_called_once_with(mock_open.return_value)
            assert arr == ["1", "2", "3"]
            
    def describe_saveStrings():
        def it_saves_an_array_to_a_file(mocker):
            mocker.patch("os.path.isfile", return_value=True)
            mock_open = mocker.patch("builtins.open", mocker.mock_open())
            mock_dump = mocker.patch("pickle.dump")
            db = MyDB("mydatabase.db")
            
            db.saveStrings(["x", "y"])

            mock_open.assert_called_once_with("mydatabase.db", "wb")
            mock_dump.assert_called_once_with(["x", "y"], mock_open.return_value)
    
    def describe_saveString():
        def it_appends_a_string_to_the_list_and_saves(mocker):
            mocker.patch("os.path.isfile", return_value=True)
            mock_open = mocker.patch("builtins.open", mocker.mock_open())
            mock_load = mocker.patch("pickle.load", return_value=["A", "B"]) 
            mock_dump = mocker.patch("pickle.dump")
            db = MyDB("mydatabase.db")

            db.saveString("C")

            mock_open.assert_has_calls([
                call("mydatabase.db", "rb"),
                call("mydatabase.db", "wb")
            ], any_order=True)
            mock_load.assert_called_once()
            mock_dump.assert_called_once_with(["A", "B", "C"], mock_open.return_value)