def safe_patch(target, method_name: str, new_impl):
    """
    Safely monkey-patches a method while keeping the original
    stored exactly once using a private attribute.
    """
    original_attr = f"__original_{method_name}__"

    # Method does not exist -> skip
    if not hasattr(target, method_name):
        return

    # Already patched -> skip
    if hasattr(target, original_attr):
        return

    # Store original
    setattr(target, original_attr, getattr(target, method_name))

    # Replace with new
    setattr(target, method_name, new_impl)
