def compute_create_diff(instance):
    return {f.name: {"old": None, "new": getattr(instance, f.attname)} for f in instance._meta.fields}


def compute_delete_diff(instance):
    return {f.name: {"old": getattr(instance, f.attname), "new": None} for f in instance._meta.fields}


def compute_update_diff(old_instance, new_instance):
    diff = {}
    for f in new_instance._meta.fields:
        name = f.name
        # Use attname to avoid fetching related objects (triggers sync DB lookup in async)
        # and to ensure the value is serializable (ID instead of object)
        attname = f.attname
        old_val = getattr(old_instance, attname)
        new_val = getattr(new_instance, attname)
        if old_val != new_val:
            diff[name] = {"old": old_val, "new": new_val}
    return diff
