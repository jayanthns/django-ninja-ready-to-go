def compute_create_diff(instance):
    return {f.name: {"old": None, "new": getattr(instance, f.name)} for f in instance._meta.fields}


def compute_update_diff(old_instance, new_instance):
    diff = {}
    for f in new_instance._meta.fields:
        name = f.name
        old_val = getattr(old_instance, name)
        new_val = getattr(new_instance, name)
        if old_val != new_val:
            diff[name] = {"old": old_val, "new": new_val}
    return diff


def compute_delete_diff(instance):
    return {f.name: {"old": getattr(instance, f.name), "new": None} for f in instance._meta.fields}
