#!/usr/bin/env python

# Copyright 2021 daohu527 <daohu527@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import math

from imap.lib.transform import Transform
from imap.lib.common import Point3d
from imap.lib.odr_spiral import odr_spiral, odr_arc
import numpy as np


class Geometry:
  def __init__(self, s = None, x = None, y = None, hdg = None, length = None):
    self.s = s
    self.x = x
    self.y = y
    self.hdg = hdg
    self.length = length

  def parse_from(self, raw_geometry):
    self.s = float(raw_geometry.attrib.get('s'))
    self.x = float(raw_geometry.attrib.get('x'))
    self.y = float(raw_geometry.attrib.get('y'))
    self.hdg = float(raw_geometry.attrib.get('hdg'))
    self.length = float(raw_geometry.attrib.get('length'))

  def sampling(self, delta_s):
    sample_count = math.ceil(self.length / delta_s) + 1

    tf = Transform(self.x, self.y, 0, self.hdg, 0, 0)

    points = []
    for i in range(sample_count):
      s, t, h = min(i * delta_s, self.length), 0, 0
      x, y, z = tf.transform(s, t, h)

      absolute_s = self.s + s

      point3d = Point3d(x, y, z, absolute_s)
      point3d.set_rotate(self.hdg)
      points.append(point3d)
    return points

class Spiral(Geometry):
  def __init__(self, s = None, x = None, y = None, hdg = None, length = None, \
               curv_start = None, curv_end = None):
    super().__init__(s, x, y, hdg, length)
    self.curv_start = curv_start
    self.curv_end = curv_end

  def parse_from(self, raw_geometry):
    super().parse_from(raw_geometry)
    raw_spiral = raw_geometry.find('spiral')
    self.curv_start = float(raw_spiral.attrib.get('curvStart'))
    self.curv_end = float(raw_spiral.attrib.get('curvEnd'))

  def sampling(self, delta_s):
    sample_count = math.ceil(self.length / delta_s) + 1
    cdot = (self.curv_end - self.curv_start) / self.length

    tf = Transform(self.x, self.y, 0, self.hdg, 0, 0)

    points = []
    for i in range(sample_count):
      local_s = min(i * delta_s, self.length)
      s, t, theta = odr_spiral(local_s, cdot)
      x, y, z = tf.transform(s, t, 0.0)

      absolute_s = self.s + local_s

      point3d = Point3d(x, y, z, absolute_s)
      point3d.set_rotate(self.hdg + theta)
      points.append(point3d)
    return points


class Arc(Geometry):
  def __init__(self, s = None, x = None, y = None, hdg = None, length = None, \
               curvature = None):
    super().__init__(s, x, y, hdg, length)
    self.curvature = curvature

  def parse_from(self, raw_geometry):
    super().parse_from(raw_geometry)
    raw_arc = raw_geometry.find('arc')
    self.curvature = float(raw_arc.attrib.get('curvature'))

  def sampling(self, delta_s):
    sample_count = math.ceil(self.length / delta_s) + 1
    tf = Transform(self.x, self.y, 0, self.hdg, 0, 0)

    points = []
    for i in range(sample_count):
      local_s = min(i * delta_s, self.length)
      s, t, theta = odr_arc(local_s, self.curvature)
      x, y, z = tf.transform(s, t, 0.0)

      # get elevation
      absolute_s = self.s + local_s

      point3d = Point3d(x, y, z, absolute_s)
      point3d.set_rotate(self.hdg + theta)
      points.append(point3d)
    return points


class Poly3(Geometry):
  def __init__(self, s = None, x = None, y = None, hdg = None, length = None, \
               a = None, b = None, c = None, d = None):
    super().__init__(s, x, y, hdg, length)
    self.a = a
    self.b = b
    self.c = c
    self.d = d
    self.start_position = np.array(x, y)

  def parse_from(self, raw_geometry):
    super().parse_from(raw_geometry)

    raw_poly3 = raw_geometry.find('poly3')
    self.a = float(raw_poly3.attrib.get('a'))
    self.b = float(raw_poly3.attrib.get('b'))
    self.c = float(raw_poly3.attrib.get('c'))
    self.d = float(raw_poly3.attrib.get('d'))
    self.start_position = np.array([float(raw_geometry.attrib.get('x')), float(raw_geometry.attrib.get('y'))])

  def sampling(self, delta_s):
    # sample_count = math.ceil(self.length / delta_s) + 1
    # Todo(zero): complete function
    # xl add
    pts = []
    for s_pos in self.calc_interpolates(0, self.length):
        pos, tangent = self.calc_position(s_pos)

        x = pos[0]
        y = pos[1]
        z = 0
        absolute_s = self.s + s_pos

        point3d = Point3d(x, y, z, absolute_s)
        point3d.set_rotate(tangent)
        pts.append(point3d)
    return pts

  # xl
  def calc_interpolates(self, pos_offset0, pos_offset1):
      vals = []
      p0 = pos_offset0
      p1 = pos_offset1
      if p1 > p0:
          vals = np.append(np.arange(p0, p1, self.interval), p1)
      return vals

  # xl
  def calc_position(self, s_pos):
      # Calculate new point in s_pos/t coordinate system
      coeffs = [self.a, self.b, self.c, self.d]

      t = np.polynomial.polynomial.polyval(s_pos, coeffs)

      # Rotate and translate
      srot = s_pos * np.cos(self.hdg) - t * np.sin(self.hdg)
      trot = s_pos * np.sin(self.hdg) + t * np.cos(self.hdg)

      # Derivate to get heading change
      dCoeffs = coeffs[1:] * np.array(np.arange(1, len(coeffs)))
      tangent = np.polynomial.polynomial.polyval(s_pos, dCoeffs)

      return self.start_position + np.array([srot, trot]), self.hdg + tangent


class ParamPoly3(Geometry):
  def __init__(self, s = None, x = None, y = None, hdg = None, length = None, \
               aU = None, bU = None, cU = None, dU = None, \
               aV = None, bV = None, cV = None, dV = None, pRange = None):
    super().__init__(s, x, y, hdg, length)
    self.aU = aU
    self.bU = bU
    self.cU = cU
    self.dU = dU
    self.aV = aV
    self.bV = bV
    self.cV = cV
    self.dV = dV
    self.pRange = pRange

  def parse_from(self, raw_geometry):
    super().parse_from(raw_geometry)
    raw_param_poly3 = raw_geometry.find('paramPoly3')

    self.aU = float(raw_param_poly3.attrib.get('aU'))
    self.bU = float(raw_param_poly3.attrib.get('bU'))
    self.cU = float(raw_param_poly3.attrib.get('cU'))
    self.dU = float(raw_param_poly3.attrib.get('dU'))
    self.aV = float(raw_param_poly3.attrib.get('aV'))
    self.bV = float(raw_param_poly3.attrib.get('bV'))
    self.cV = float(raw_param_poly3.attrib.get('cV'))
    self.dV = float(raw_param_poly3.attrib.get('dV'))
    self.pRange = raw_param_poly3.attrib.get('pRange')

  def sampling(self, delta_s):
    sample_count = math.ceil(self.length / delta_s) + 1
    # Todo(zero): complete function


class PlanView:
  def __init__(self):
    self.geometrys = []

  def add_geometry(self, geometry):
    self.geometrys.append(geometry)

  def parse_from(self, raw_plan_view):
    for raw_geometry in raw_plan_view.iter('geometry'):
      if raw_geometry[0].tag == 'line':
        geometry = Geometry()
      elif raw_geometry[0].tag == 'spiral':
        geometry = Spiral()
      elif raw_geometry[0].tag == 'arc':
        geometry = Arc()
      elif raw_geometry[0].tag == 'poly3':  # deprecated in OpenDrive 1.6.0
        geometry = Poly3()
      elif raw_geometry[0].tag == 'paramPoly3':
        geometry = ParamPoly3()
      else:
        # Todo(zero): raise an exception
        print("geometry type not support")

      geometry.parse_from(raw_geometry)
      self.add_geometry(geometry)
