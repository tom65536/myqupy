"""Additional mypy checks for units.

Most libraries handle physical
quantities as run-time objects::
   
   >>> import pint
   >>> ureg = pint.UnitRegistry()
   >>> 3 * ureg.meter + 4 * ureg.cm
   <Quantity(3.04, 'meter')>
   
This mypy plugin moves the units
to type annotations. Thus the
runtime objects remain purely
numeric while the dimensional
analysis is carried out at
runtime::   
   
   >>> import pint
   >>> ureg = pint.UnitRegistry()
   >>>
   >>> x: Annotated[int, ureg.meter] = 3
   >>> y: Annotated[int, ureg.cm] = 4
   >>> x + y  # ERROR detected by mypy
   7
   >>> cm_to_m: Annotated[float, ureg.m/ureg.cm] = 0.01
   >>> x + y * cm_to_m  # OK 
   3.04
  
"""

from collections.abc import Callable
from typing import Optional, Protocol, TypeAlias, Union

from mypy.plugin import FunctionContext, Plugin
from mypy.types import Type

FunctionCheckType: TypeAlias = Optional[
   Callable[[FunctionContext], Type]
]

FUNCTION_CHECKERS: dict[str, FunctionCheckType] = {}


def function_checker(
   full_name: str,
   *more_names: str,
) -> Callable[[FunctionCheckType], FunctionCheckType]:
   """Decorator registering checker functions."""
   def _register(f: FunctionCheckType) -> FunctionCheckType:
      FUNCTION_CHECKERS[full_name] = f
      for name in more_names:
         FUNCTION_CHECKERS[name] = f
      return f
      
   return _register
   

class Unit(Protocol):
   """Abstract annotation for units."""
   
   def __mul__(self, other: 'Unit') -> 'Unit':
      """Multiply units."""
      raise NotImplementedError

   def __div__(self, other: 'Unit') -> 'Unit':
      """Divide units."""
      raise NotImplementedError

   def __eq__(self, other: Union['Unit', int]) -> bool:
      """Compare units for equality."""
      raise NotImplementedError


class QuantityPlugin(Plugin):
   """Check physical quantities.
   
   Check operations on ``Annotated`` types
   which have an annotation which
   implements the ``Unit`` protocol.
   """
   
   def get_function_hook(self, fullname: str) -> Optional[FunctionCheckType]:
      """Provide a type checking hook for the given function name."""
      return None # FUNCTION_CHECKERS.get(fullname, None)

@function_checker('list')
def check_add_function(ctx: FunctionContext) -> Type:
   """Check additive expressions."""
   return ctx.default_return_type
 
  
def plugin(_: str):
   """Return the plugin."""
   return QuantityPlugin
  