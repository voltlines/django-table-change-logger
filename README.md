# Django Table Change Logger

### Quick Description
A python package which logs each change made to a Django model instance.

### How to set up?
1) Add ```tablechangelogger.apps.TableChangeLoggerConfig``` to your ```INSTALLED_APPS```
2) Run ```python manage.py migrate``` to initialize the model
3) Add ```TABLE_CHANGE_LOG_CONFIG``` to your settings.py file.

```python
TABLE_CHANGE_LOG_CONFIG={
    'drivers': {
        'yourapp.models.Drivers': {
            'fields': ['driver_id', 'driver_name']
        }
    },
    'cars': {
        'yourapp.models.Car': {
            'fields': ['license_plate', 'car_model']
        }
    }
}

```

The keys of ```TABLE_CHANGE_LOG_CONFIG``` indicate your app label, while the
nested mappings contain **relative project path of your model** mapped to a
dictionary containing **loggable fields of that respective model**.

### How it works?

- Obtains the TABLE_CHANGE_LOG_CONFIG from your respective settings file based
  on your environment.
- Initializes ```LOGGABLE_MODELS``` with the relative project paths of your
  models based on your configuration variable.
- Binds to pre_save signal of each loggable model
- For each field specified in the configuration variable, creates a record in
  the TableChangeLog model.

### The model structure

This package provides you a django model which tracks each change to a model 
instance specified in your configuration mapping. An example record is as
follows:

```
{
 'app_label': 'drivers',
 'created_at': datetime.datetime(2019, 2, 22, 9, 1, 14, 619568, tzinfo=<UTC>),
 'field_name': 'latest_speed',
 'field_value': '200',
 'id': 1,
 'instance_id': 1,
 'table_name': 'Driver'}

```
