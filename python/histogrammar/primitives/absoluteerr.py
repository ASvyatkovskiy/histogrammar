#!/usr/bin/env python

# Copyright 2016 Jim Pivarski
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

from histogrammar.defs import *
from histogrammar.util import *

class AbsoluteErr(Factory, Container):
    @staticmethod
    def ed(entries, mae):
        if entries < 0.0:
            raise ContainerException("entries ($entries) cannot be negative")
        out = AbsoluteErr(None, None)
        out.entries = float(entries)
        out.absoluteSum = float(mae)*float(entries)
        return out

    @staticmethod
    def ing(quantity, selection=unweighted):
        return AbsoluteErr(quantity, selection)

    def __init__(self, quantity, selection=unweighted):
        self.quantity = serializable(quantity)
        self.selection = serializable(selection)
        self.entries = 0.0
        self.absoluteSum = 0.0
        super(AbsoluteErr, self).__init__()

    @property
    def mae(self):
        if self.entries == 0.0:
            return self.absoluteSum
        else:
            return self.absoluteSum/self.entries

    def zero(self): return AbsoluteErr(self.quantity, self.selection)

    def __add__(self, other):
        if isinstance(other, AbsoluteErr):
            out = AbsoluteErr(self.quantity, self.selection)
            out.entries = self.entries + other.entries
            out.absoluteSum = self.entries*self.mae + other.entries*other.mae
            return out
        else:
            raise ContainerException("cannot add {} and {}".format(self.name, other.name))

    def fill(self, datum, weight=1.0):
        if self.quantity is None or self.selection is None:
            raise RuntimeException("attempting to fill a container that has no fill rule")

        w = weight * self.selection(datum)
        if w > 0.0:
            q = self.quantity(datum)
            self.entries += w
            self.absoluteSum += abs(q)

    def toJsonFragment(self): return {
        "entries": floatToJson(self.entries),
        "mae": floatToJson(self.mae),
        }

    @staticmethod
    def fromJsonFragment(json):
        if isinstance(json, dict) and set(json.keys()) == set(["entries", "mae"]):
            if isinstance(json["entries"], (int, long, float)):
                entries = float(json["entries"])
            else:
                raise JsonFormatException(json["entries"], "AbsoluteErr.entries")

            if isinstance(json["mae"], (int, long, float)):
                mae = float(json["mae"])
            else:
                raise JsonFormatException(json["mae"], "AbsoluteErr.mae")

            return AbsoluteErr.ed(entries, mae)

        else:
            raise JsonFormatException(json, self.name)
        
    def __repr__(self):
        return "AbsoluteErr[{}]".format(self.mae)

    def __eq__(self, other):
        return isinstance(other, AbsoluteErr) and self.quantity == other.quantity and self.selection == other.selection and exact(self.entries, other.entries) and exact(self.mae, other.mae)

    def __hash__(self):
        return hash((self.quantity, self.selection, self.entries, self.mae))

Factory.register(AbsoluteErr)
