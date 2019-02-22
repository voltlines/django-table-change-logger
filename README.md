# Django Table Change Logger

### Quick Description
A python package which logs each change made to a Django model instance.

### How to set up?
1) Add ```tablechangelogger``` to your ```INSTALLED_APPS```
2) Run ```python manage.py migrate``` to initialize the model
3) Add ```TABLE_CHANGE_LOG_CONFIG``` to your settings.py file.
4) Additionaly, you can add ```TABLE_CHANGE_LOG_ENABLED``` to enable/disable
table change logging. If not provided, the default value is True.

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

- Obtains the ```TABLE_CHANGE_LOG_CONFIG``` from your respective settings file based
  on your environment.
- Initializes ```LOGGABLE_MODELS``` with the relative project paths of your
  models based on your configuration variable.
- Binds to pre_save signal of each loggable model
- For each field specified in the configuration variable, creates a record in
  the ```TableChangesLog``` model in each instance update.

### Example

This section serves as a small example to demonstrate this package.
The example takes the configuration above into account.
Supposing you have a model called ```Driver``` and fields called ```latest_speed``` and ```driver_name``` and ```driver_id```:
    
```python
    driver = Driver.objects.last()
    driver.latest_speed = 5
    driver.save()  # tablechangelogger won't create a record since 'latest_speed' was not among the loggable fields

    driver.driver_name = 'John Doe'
    driver.save()  # a record with this driver is created

    # you can also use tablechangelogger.utils.get_model_name 
    model_name = driver._meta.model.__name__
    
    log = TableChangesLog.objects.filter(
        instance_id=driver.id, table_name=model_name)
    print(log.field_name, log.field_value)  # prints 'driver_name, John Doe'
```

### The model structure

This package provides you a django model which is called ```TableChangesLog```; which tracks each change to a model 
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
 'table_name': 'Driver'
 }

```
