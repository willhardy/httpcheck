def help_messages(definition):
    """
    Returns a decorator that will apply help messages to all options in the CLI.

    It prevents missed and outdated help messages and allows options to be defined
    without the distraction of a long help message.
    """

    def validate_params(params):
        help_params = [p for p in params if hasattr(p, "help")]
        defined = set(definition)
        required = set([p.name for p in help_params])
        extra = defined - required
        missing = required - defined
        assert not extra, f"Additional help messages provided: {extra}"
        assert not missing, f"Help messages missing: {missing}"
        return help_params

    def add_help_messages(params):
        for p in params:
            p.help = definition[p.name]

    def add_show_default(params):
        for p in params:
            if not hasattr(p, "show_default"):
                continue
            if getattr(p, "is_flag", None):
                continue
            if p.default is None or p.default == "":
                continue
            p.show_default = True

    def decorator(fn):
        help_params = validate_params(fn.params)
        add_help_messages(help_params)
        add_show_default(help_params)
        return fn

    return decorator
