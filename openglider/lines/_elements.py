#! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from _functions import proj_force, proj_to_surface
from openglider.vector import normalize, norm
import numpy


class sag_matrix():

    def __init__(self, number_of_lines):
        self.size = number_of_lines * 2
        self.matrix = numpy.zeros([self.size, self.size])
        self.rhs = numpy.zeros(self.size)
        self.solution = numpy.zeros(self.size)

    def __str__(self):
        return(str(self.matrix) + "\n" + str(self.rhs))

    def _type_0_lower(self, line):
        i = line.number
        self.matrix[2 * i + 1, 2 * i + 1] = 1.

    def _type_1_lower(self, line, lower_line):
        i = line.number
        j = lower_line.number
        self.matrix[2 * i + 1, 2 * i + 1] = 1.
        self.matrix[2 * i + 1, 2 * j + 1] = -1.
        self.matrix[2 * i + 1, 2 * j] = -lower_line.ortho_length
        self.rhs[2 * i + 1] = -lower_line.ortho_pressure * \
            lower_line.ortho_length ** 2 / lower_line.ortho_force / 2

    def _type_1_upper(self, line, upper_lines):
        i = line.number
        self.matrix[2 * i, 2 * i] = 1
        infl_list = []
        vec = line._get_ortho_vec()
        for u in upper_lines:
            f_vec = u._get_ortho_vec()
            infl = line.ortho_force * numpy.dot(vec, f_vec)
            infl_list.append(infl)
        sum_infl = sum(infl_list)
        for k in range(len(upper_lines)):
            j = upper_lines[k].number
            self.matrix[2 * i, 2 * j] = -(infl_list[k] / sum_infl)
        self.rhs[2 * i] = line.ortho_pressure * \
            line.ortho_length / line.ortho_force

    def _type_2_upper(self, line):
        i = line.number
        self.matrix[2 * line.number, 2 * line.number] = line.ortho_length
        self.matrix[2 * line.number, 2 * line.number + 1] = 1.
        self.rhs[2 * i] = line.ortho_pressure * \
            line.ortho_length ** 2 / line.ortho_force / 2

    def solve_system(self):
        self.solution = numpy.linalg.solve(self.matrix, self.rhs)

    def get_sag_par(self, line_nr):
        return([
            self.solution[line_nr * 2],
            self.solution[line_nr * 2 + 1]])

    def _line_parameter(self):
        pass


class Line():

    def __init__(self, number):
        """Line Class:
        Note:
            -for easier use the nodes are now directly in the lines!!!
                if they are changed also the lines have to be recomputed
            -when you set some parameter of a node always use the node
                dict and don't forget to update the lines.
            -when you get parameters of nodes, you can the take them from
                the node dict or from the nodes stored in the line.
            """
        self.number = number
        self.type = None                # type of line
        self.speed = None
        self.v_inf = None

        self.lower_node_nr = None
        self.upper_node_nr = None

        self.lower_node = None
        self.upper_node = None

        self.init_length = None
        self.length = None              # length of line without sag
        self.length_tot = None          # total length of line
        self.ortho_length = None        # length of the projected line

        self.force = None
        self.ortho_force = None

        self.cw = None
        self.b = None
        self.ortho_pressure = None

        self.sag_par_1 = None
        self.sag_par_2 = None

        self.stretch_factor = None

    def _calc_pressure(self):
        self.ortho_pressure = self.cw * self.b * self.speed ** 2 / 2

    def _calc_length(self):
        self.length = norm(
            self.lower_node.vec - self.upper_node.vec)

    def _calc_ortho_length(self):
        self.ortho_length = norm(
            self.lower_node.vec_proj - self.upper_node.vec_proj)

    def calc_total_length(self):
        pass

    def _calc_ortho_force(self):
        self.ortho_force = self.force * self.ortho_length / self.length

    def _get_ortho_vec(self):
        return(normalize(self.upper_node.vec_proj - self.lower_node.vec_proj))

    def _get_vec(self):
        return(normalize(self.upper_node.vec - self.lower_node.vec))

    def get_line_coords(self, sag=True, numpoints=10):
        if sag:
            n = normalize(self.v_inf)
            out = []
            for i in range(numpoints):
                x = i / (numpoints - 1)
                out.append(self.get_pos(x) + n * self.get_sag(x))
        else:
            out = [self.lower_node.vec, self.upper_node.vec]
        return(out)

    def get_pos(self, x):
        """x,0,1"""
        return(self.lower_node.vec * (1. - x) + self.upper_node.vec * x)

    def get_sag(self, x):
        """x,0,1"""
        xi = x * self.ortho_length
        u = (- xi ** 2 / 2 * self.ortho_pressure /
             self.ortho_force + xi *
             self.sag_par_1 + self.sag_par_2)
        return(u)

    def calc_stretch_par(self):
        pass


class Node():

    def __init__(self, number):
        self.number = number
        self.type = None
        self.vec = numpy.array([None, None, None])
        self.vec_proj = numpy.array([None, None, None])
        self.force = numpy.array([None, None, None])

    def calc_force_infl(self, vec):
        v = numpy.array(vec)
        if None in self.force:
            print("force in node " + str(self.number) + " not set")
        elif None in self.vec:
            print("vec in node " + str(self.number) + " not set")
        elif self.type != 2:
            print("wrong node type, node " + str(self.number))
        else:
            return(proj_force(self.force, self.vec - v) *
                   normalize(self.vec - v))

    def calc_proj_vec(self, v_inf):
        if None in self.vec:
            print("node " + str(self.number) + "not set yet")
        else:
            self.vec_proj = proj_to_surface(self.vec, v_inf)


class LinePar():

    def __init__(self, name):
        self.type = name
        self.cw = 0.
        self.b = 0.
        self.strech_factor = 0.
