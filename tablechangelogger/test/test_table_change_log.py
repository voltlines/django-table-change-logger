import pytest
from mock import patch

from tablechangelogger.datastructures import Logged, Change
from tablechangelogger.log_table_change import (
    is_loggable
)


class MockClass(object):
    def __init__(self, _id, route_id, pickup_point):
        self.id = _id
        self.properties = ['route_id']
        self.fields = ['pickup_point']
        self.route_id = route_id
        self.pickup_point = pickup_point


def mock_tcl_data(app_label, table_name, _id, route_id, pickup_point):
    mock_instance = MockClass(_id=_id, route_id=route_id,
                              pickup_point=pickup_point)
    changes = {
        'route_id': Change(
            old_value=mock_instance.route_id,
            new_value=mock_instance.route_id)
    }
    data = {
        'app_label': app_label,
        'table_name': table_name,
        'instance_id': mock_instance.id,
        'field_names': mock_instance.properties,
        'log': Logged(changes=changes, created=True),
        'loggable_properties': mock_instance.properties,
        'mock_instance': mock_instance,
    }
    return data


@pytest.fixture(params=[True, False])
def mock_tcl_attributes(request):
    app_label = 'mocks'
    table_name = 'MockClass'
    _id = None if request.param else 1
    data = mock_tcl_data(app_label, table_name, _id, 1, '2,2')
    data['created'] = request.param
    return data


@patch('tablechangelogger.log_table_change.get_app_label')
@patch('tablechangelogger.log_table_change.get_model_name')
def test_is_loggable(mock1, mock2, mock_tcl_attributes):
    created = mock_tcl_attributes.get('created')
    mock_instance = mock_tcl_attributes.pop('mock_instance')
    mock1.return_value = mock_tcl_attributes.get('table_name')
    mock2.return_value = mock_tcl_attributes.get('app_label')
    loggable = is_loggable(mock_instance)
    assert loggable == (not created)
