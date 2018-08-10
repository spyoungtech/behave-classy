import functools

from behave.step_registry import StepRegistry
from behave.matchers import get_matcher
from behave.textutil import text as _text

class LocalRegistry(StepRegistry):
    _matcher = None
    def __init__(self, matcher=None):
        if matcher:
            self._matcher = matcher
        super(LocalRegistry, self).__init__()

    @property
    def matcher(self):
        if self._matcher:
            return self._matcher
        else:
            return get_matcher

    def get_matcher(self, func, step_text, matcher=None):
        if matcher is None:
            matcher = self.matcher
        return matcher(func, step_text)

    def add_step_definition(self, keyword, step_text, func, matcher=None):
        step_type = keyword.lower()
        step_text = _text(step_text)
        self.steps[step_type].append(self.get_matcher(func, step_text, matcher))

    def make_decorator(self, step_type):
        @staticmethod
        def decorator(step_text, matcher=None):
            def wrapper(func):
                self.add_step_definition(step_type, step_text, func, matcher)
                return func
            return wrapper
        return decorator



def step_impl_base(default_matcher=None):
    class LocalStepRegistry(object):
        _registry = LocalRegistry(matcher=default_matcher)
        _context = None

        @property
        def context(self):
            return self._context

        def register(self):
            """
            adds contained definitions to the global registry
            This function also is responsible for updating functions in the registry with functions
            defined in subclasses
            """
            from behave.runner import the_step_registry  # make sure we use same registry as normal definitions
            for step_type, steps in self._registry.steps.items():
                for match_obj in steps:
                    if hasattr(self, match_obj.func.__name__):
                        method = getattr(self, match_obj.func.__name__)
                        match_obj.func = self._step_context(method)
                    the_step_registry.steps[step_type].append(match_obj)

        @classmethod
        def _step_context(cls, method):
            from behave.runner import Context
            @functools.wraps(method)
            def newmethod(*args, **kwargs):
                if args:
                    context = args[0]
                    other_args = args[1:]
                    if isinstance(context, Context):
                        cls._context = context
                        args = other_args
                return method(*args, **kwargs)
            return newmethod



    for step_type in ("given", "when", "then", "step"):
        step_decorator = LocalStepRegistry._registry.make_decorator(step_type)
        setattr(LocalStepRegistry, step_type, step_decorator)
        setattr(LocalStepRegistry, step_type.title(), step_decorator)
    return LocalStepRegistry