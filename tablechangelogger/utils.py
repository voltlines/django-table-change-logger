import json
import pickle

def get_model(instance):
    """Returns the model object from instance"""
    return instance._meta.model


def get_model_name(instance):
    """Returns model name from instance"""
    return instance._meta.model.__name__


def get_app_label(instance):
    """Returns app label from instance"""
    return instance._meta.app_label


def serialize_field(field):
    """Serializes a pickled field"""
    pickled_field = pickle.dumps(field)
    byte_field = list(pickled_field)
    dumped_field = json.dumps(byte_field)
    return dumped_field

def deserialize_field(field):
    """Deserializes a pickled field"""
    byte_field = bytes(json.loads(field))
    original_field = pickle.loads(byte_field)
    return original_field
