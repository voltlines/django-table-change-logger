def get_model(instance):
    """Returns the model object from instance"""
    return instance._meta.model


def get_model_name(instance):
    """Returns model name from instance"""
    return instance._meta.model.__name__


def get_app_label(instance):
    """Returns app label from instance"""
    return instance._meta.app_label
