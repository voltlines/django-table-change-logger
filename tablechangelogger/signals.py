import logging

from django.utils.module_loading import import_string
from django.db.models.signals import pre_save

from tablechangelogger.config import LOGGABLE_MODELS


logger = logging.getLogger(__name__)

PRE_SAVE_FUNCTION_TEMPLATE = """
from tablechangelogger.log_table_change import log_table_change

@log_table_change
def table_change_log_{model_name}(sender, instance, **kwargs):
    pass
"""  # noqa

PRE_SAVE_FUNCS = {}


for model_config in LOGGABLE_MODELS:
    # get loggable fields from the configuration mapping
    try:
        model_path = list(model_config.keys())[0]
        table_config = model_config.get(model_path)
        fields_list = table_config.get('fields')
        model_name = model_path.rsplit('.', 1)[1].lower()
        # format function with loggable fields and the model name
        pre_save_signal_code = PRE_SAVE_FUNCTION_TEMPLATE.format(
            fields=fields_list, model_name=model_name
        )
        exec(pre_save_signal_code, {}, PRE_SAVE_FUNCS)

        key = 'table_change_log_{}'.format(model_name)
        func = PRE_SAVE_FUNCS[key]

        sender = import_string(model_path)
        pre_save.connect(func, sender=sender)
    except Exception:
        logger.exception('Could not bind to the pre_save signal of {}'.format(
            model_name
        ))
