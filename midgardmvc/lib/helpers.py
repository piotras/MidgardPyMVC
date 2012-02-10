"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""

from pylons import url, request, response

from webhelpers.html import literal
from webhelpers.html.tags import *
from webhelpers.pylonslib.minify import stylesheet_link, javascript_link

from webhelpers.pylonslib import Flash as _Flash

import midgardmvc.lib.output.helpers.header as header

import logging
log = logging.getLogger(__name__)

from gi.repository import GObject, Midgard
from midgardmvc.lib.midgard.connection import instance as connection_instance

#from midgardmvc.lib.midgard.middleware import MIDGARD as midgard

flash = _Flash()

def flash_ok(message):
    flash(message, category='success')

def flash_info(message):
    flash(message, category='notice')

def flash_warning(message):
    flash(message, category='warning')
    
def flash_alert(message):
    flash(message, category='error')

class LegacyMidgardObject(dict):
  _m = None

  @property
  def _model(self):
    return self.__class__._model

  @_model.setter
  def _model(self, model):
    self._m = model

  def __init__(self, model):
    self.__class__._model = model
   
  def get_model(self):
    return self._m

  def __getattribute__(self, name):
    try:
      return dict.__dict__[name]
    except KeyError as e:
      print "GET ATTR " + name 
      try:
        return self.__class__._model.get_property(name)
      except AttributeError:
        if name in self:
          return self[name]
        raise
      
  def __setitem__(self, key, value):
    self._validate_key(key)
    self._model.set_property(key, value)
    __setattr_ = __setitem__
      
  def set_property(self, *args, **kwargs):
    return self._model.set_property(*args, **kwargs)
  
  #def get_property(self, *args, **kwargs):
  #  return self._model.get_property(*args, **kwargs)
                                                                                                                                                            
  def save(self, *args, **kwargs):
    return self._model.save(*args, **kwargs)
  
  def _validate_key(self, key):
    pass
    try:
      class IsIdentifier(object): __slots__ = key
    except TypeError:
      raise TypeError("invalid identifier: '%s'" % key)
    
    try:
      dict.__getattribute__(self, key)
    except AttributeError:
      pass
    else:
      raise TypeError("builtin dict attribute: '%s'" % key)

class midgard_legacy_query_builder():
  group = None
  qs = None
  constraints = 0
  user_group = None
  executed = False
  
  def __init__(self, name):
    storage = Midgard.QueryStorage(dbclass = name)
    self.qs = Midgard.QuerySelect(connection = connection_instance.connection, storage = storage)
    self.qs.toggle_read_only(False)

  def add_constraint(self, name, operator, value):
    tmp_group = None
    if self.user_group is not None:
      tmp_group = self.user_group

    if self.group is None:
      self.group = Midgard.QueryConstraintGroup(grouptype = "AND")
   
    if tmp_group is None:
      tmp_group = self.group

    tmp_group.add_constraint(
      Midgard.QueryConstraint(
        property = Midgard.QueryProperty(property = name),
        operator = operator,
        holder = Midgard.QueryValue.create_with_value(value)
      )
    )
    self.constraints = self.constraints + 1

  def begin_group(self, group_type):
    self.user_group =  Midgard.QueryConstraintGroup(grouptype = group_type)

  def end_group(self):
    if self.group is None:
      self.group = Midgard.QueryConstraintGroup(grouptype = "AND")
    self.group.add_constraint(self.user_group)
    self.user_group = None

  def add_order(self, name, order):
    self.qs.add_order(Midgard.QueryProperty(property = name), order)

  def set_offset(self, offset):
    self.qs.set_offset(offset)

  def set_limit(self, limit):
    self.qs.set_limit(limit)

  def get_query_select(self):
    return self.qs

  def execute(self):
    # workaround for one constraint in group
    if self.constraints == 1:
      self.add_constraint("guid", "<>", "")
    if self.group is not None:
      self.qs.set_constraint(self.group)
    self.qs.execute()
    self.executed = True
    objects = self.qs.list_objects()
    return objects
    #result = []
    #for o in objects:
    #  result.append(LegacyMidgardObject(o))
    #return result

  def count(self):
    if self.executed is False:
      self.execute()

    return  self.qs.get_results_count()
 

