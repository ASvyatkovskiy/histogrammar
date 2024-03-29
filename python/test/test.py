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

import math
import unittest

from histogrammar import *
from histogrammar.histogram import Histogram

class TestEverything(unittest.TestCase):
    simple = [3.4, 2.2, -1.8, 0.0, 7.3, -4.7, 1.6, 0.0, -3.0, -1.7]

    class Struct(object):
        def __init__(self, x, y, z, w):
            self.bool = x
            self.int = y
            self.double = z
            self.string = w
        def __repr__(self):
            return "Struct({}, {}, {}, {})".format(self.bool, self.int, self.double, self.string)

    struct = [
        Struct(True,  -2,  3.4, "one"),
        Struct(False, -1,  2.2, "two"),
        Struct(True,   0, -1.8, "three"),
        Struct(False,  1,  0.0, "four"),
        Struct(False,  2,  7.3, "five"),
        Struct(False,  3, -4.7, "six"),
        Struct(True,   4,  1.6, "seven"),
        Struct(True,   5,  0.0, "eight"),
        Struct(False,  6, -3.0, "nine"),
        Struct(True,   7, -1.7, "ten"),
        ]

    backward = list(reversed(struct))

    # straightforward mean and variance to complement the Tony Finch calculations used in the module

    @staticmethod
    def mean(x):
        if len(x) == 0:
            return 0.0
        else:
            return sum(x) / len(x)

    @staticmethod
    def meanWeighted(x, w):
        if not any(_ > 0.0 for _ in w):
            return 0.0
        else:
            return sum(xi * max(wi, 0.0) for xi, wi in zip(x, w)) / sum(_ for _ in w if _ > 0.0)

    @staticmethod
    def variance(x):
        if len(x) == 0:
            return 0.0
        else:
            return sum(math.pow(_, 2) for _ in x) / len(x) - math.pow(sum(x) / len(x), 2)

    @staticmethod
    def varianceWeighted(x, w):
        if not any(_ > 0.0 for _ in w):
            return 0.0
        else:
            return sum(xi**2 * max(wi, 0.0) for xi, wi in zip(x, w)) / sum(_ for _ in w if _ > 0.0) - math.pow(sum(xi * max(wi, 0.0) for xi, wi in zip(x, w)) / sum(_ for _ in w if _ > 0.0), 2)

    @staticmethod
    def mae(x):
        if len(x) == 0:
            return 0.0
        else:
            return sum(map(abs, x)) / len(x)

    @staticmethod
    def maeWeighted(x, w):
        if not any(_ > 0.0 for _ in w):
            return 0.0
        else:
            return sum(abs(xi) * max(wi, 0.0) for xi, wi in zip(x, w)) / sum(_ > 0.0 for _ in w)

    def checkJson(self, x):
        self.assertEqual(x.toJson(), Factory.fromJson(x.toJson()).toJson())

    ################################################################ Count

    def testCount(self):
        for i in xrange(11):
            left, right = self.simple[:i], self.simple[i:]

            leftCounting = Count()
            rightCounting = Count()

            for _ in left: leftCounting.fill(_)
            for _ in right: rightCounting.fill(_)

            self.assertEqual(leftCounting.entries, len(left))
            self.assertEqual(rightCounting.entries, len(right))

            finalResult = leftCounting + rightCounting

            self.assertEqual(finalResult.entries, len(self.simple))

            self.checkJson(leftCounting)

    ################################################################ Sum

    def testSum(self):
        for i in xrange(11):
            left, right = self.simple[:i], self.simple[i:]

            leftSumming = Sum(lambda x: x)
            rightSumming = Sum(lambda x: x)

            for _ in left: leftSumming.fill(_)
            for _ in right: rightSumming.fill(_)

            self.assertAlmostEqual(leftSumming.sum, sum(left))
            self.assertAlmostEqual(rightSumming.sum, sum(right))

            finalResult = leftSumming + rightSumming

            self.assertAlmostEqual(finalResult.sum, sum(self.simple))

            self.checkJson(leftSumming)
       
    def testSumWithFilter(self):
        for i in xrange(11):
            left, right = self.struct[:i], self.struct[i:]

            leftSumming = Sum(lambda x: x.double, lambda x: x.bool)
            rightSumming = Sum(lambda x: x.double, lambda x: x.bool)

            for _ in left: leftSumming.fill(_)
            for _ in right: rightSumming.fill(_)

            self.assertAlmostEqual(leftSumming.sum, sum(_.double for _ in left if _.bool))
            self.assertAlmostEqual(rightSumming.sum, sum(_.double for _ in right if _.bool))

            finalResult = leftSumming + rightSumming

            self.assertAlmostEqual(finalResult.sum, sum(_.double for _ in self.struct if _.bool))

            self.checkJson(leftSumming)

    def testSumWithWeightingFactor(self):
        for i in xrange(11):
            left, right = self.struct[:i], self.struct[i:]

            leftSumming = Sum(lambda x: x.double, lambda x: x.int)
            rightSumming = Sum(lambda x: x.double, lambda x: x.int)

            for _ in left: leftSumming.fill(_)
            for _ in right: rightSumming.fill(_)

            self.assertAlmostEqual(leftSumming.sum, sum(_.double * _.int for _ in left if _.int > 0))
            self.assertAlmostEqual(rightSumming.sum, sum(_.double * _.int for _ in right if _.int > 0))

            finalResult = leftSumming + rightSumming

            self.assertAlmostEqual(finalResult.sum, sum(_.double * _.int for _ in self.struct if _.int > 0))

            self.checkJson(leftSumming)

    def testSumStringFunctions(self):
        for i in xrange(11):
            left, right = self.simple[:i], self.simple[i:]

            leftSumming = Sum("datum + 1")
            rightSumming = Sum("datum + 1")

            for _ in left: leftSumming.fill(_)
            for _ in right: rightSumming.fill(_)

            self.assertAlmostEqual(leftSumming.sum, sum(left) + len(left))
            self.assertAlmostEqual(rightSumming.sum, sum(right) + len(right))

            finalResult = leftSumming + rightSumming

            self.assertAlmostEqual(finalResult.sum, sum(self.simple) + len(self.simple))

            self.checkJson(leftSumming)
       
    def testSumWithFilterStringFunctions(self):
        for i in xrange(11):
            left, right = self.struct[:i], self.struct[i:]

            leftSumming = Sum("double + 1", "not bool")
            rightSumming = Sum("double + 1", "not bool")

            for _ in left: leftSumming.fill(_)
            for _ in right: rightSumming.fill(_)

            self.assertAlmostEqual(leftSumming.sum, sum(_.double + 1 for _ in left if not _.bool))
            self.assertAlmostEqual(rightSumming.sum, sum(_.double + 1 for _ in right if not _.bool))

            finalResult = leftSumming + rightSumming

            self.assertAlmostEqual(finalResult.sum, sum(_.double + 1 for _ in self.struct if not _.bool))

            self.checkJson(leftSumming)

    def testSumWithWeightingFactorStringFunctions(self):
        for i in xrange(11):
            left, right = self.struct[:i], self.struct[i:]

            leftSumming = Sum("double * 2", "int")
            rightSumming = Sum("double * 2", "int")

            for _ in left: leftSumming.fill(_)
            for _ in right: rightSumming.fill(_)

            self.assertAlmostEqual(leftSumming.sum, sum(_.double * 2 * _.int for _ in left if _.int > 0))
            self.assertAlmostEqual(rightSumming.sum, sum(_.double * 2 * _.int for _ in right if _.int > 0))

            finalResult = leftSumming + rightSumming

            self.assertAlmostEqual(finalResult.sum, sum(_.double * 2 * _.int for _ in self.struct if _.int > 0))

            self.checkJson(leftSumming)

    ################################################################ Average

    def testAverage(self):
        for i in xrange(11):
            left, right = self.simple[:i], self.simple[i:]

            leftAveraging = Average(lambda x: x)
            rightAveraging = Average(lambda x: x)

            for _ in left: leftAveraging.fill(_)
            for _ in right: rightAveraging.fill(_)

            self.assertAlmostEqual(leftAveraging.mean, self.mean(left))
            self.assertAlmostEqual(rightAveraging.mean, self.mean(right))

            finalResult = leftAveraging + rightAveraging

            self.assertAlmostEqual(finalResult.mean, self.mean(self.simple))

            self.checkJson(leftAveraging)

    def testAverageWithFilter(self):
        for i in xrange(11):
            left, right = self.struct[:i], self.struct[i:]

            leftAveraging = Average(lambda x: x.double, lambda x: x.bool)
            rightAveraging = Average(lambda x: x.double, lambda x: x.bool)

            for _ in left: leftAveraging.fill(_)
            for _ in right: rightAveraging.fill(_)

            self.assertAlmostEqual(leftAveraging.mean, self.mean([_.double for _ in left if _.bool]))
            self.assertAlmostEqual(rightAveraging.mean, self.mean([_.double for _ in right if _.bool]))

            finalResult = leftAveraging + rightAveraging

            self.assertAlmostEqual(finalResult.mean, self.mean([_.double for _ in self.struct if _.bool]))

            self.checkJson(leftAveraging)

    def testAverageWithWeightingFactor(self):
        for i in xrange(11):
            left, right = self.struct[:i], self.struct[i:]

            leftAveraging = Average(lambda x: x.double, lambda x: x.int)
            rightAveraging = Average(lambda x: x.double, lambda x: x.int)

            for _ in left: leftAveraging.fill(_)
            for _ in right: rightAveraging.fill(_)

            self.assertAlmostEqual(leftAveraging.mean, self.meanWeighted(map(lambda _: _.double, left), map(lambda _: _.int, left)))
            self.assertAlmostEqual(rightAveraging.mean, self.meanWeighted(map(lambda _: _.double, right), map(lambda _: _.int, right)))

            finalResult = leftAveraging + rightAveraging

            self.assertAlmostEqual(finalResult.mean, self.meanWeighted(map(lambda _: _.double, self.struct), map(lambda _: _.int, self.struct)))

            self.checkJson(leftAveraging)

    ################################################################ Deviate

    def testDeviate(self):
        for i in xrange(11):
            left, right = self.simple[:i], self.simple[i:]

            leftDeviating = Deviate(lambda x: x)
            rightDeviating = Deviate(lambda x: x)

            for _ in left: leftDeviating.fill(_)
            for _ in right: rightDeviating.fill(_)

            self.assertAlmostEqual(leftDeviating.variance, self.variance(left))
            self.assertAlmostEqual(rightDeviating.variance, self.variance(right))

            finalResult = leftDeviating + rightDeviating

            self.assertAlmostEqual(finalResult.variance, self.variance(self.simple))

            self.checkJson(leftDeviating)

    def testDeviateWithFilter(self):
        for i in xrange(11):
            left, right = self.struct[:i], self.struct[i:]

            leftDeviating = Deviate(lambda x: x.double, lambda x: x.bool)
            rightDeviating = Deviate(lambda x: x.double, lambda x: x.bool)

            for _ in left: leftDeviating.fill(_)
            for _ in right: rightDeviating.fill(_)

            self.assertAlmostEqual(leftDeviating.variance, self.variance([_.double for _ in left if _.bool]))
            self.assertAlmostEqual(rightDeviating.variance, self.variance([_.double for _ in right if _.bool]))

            finalResult = leftDeviating + rightDeviating

            self.assertAlmostEqual(finalResult.variance, self.variance([_.double for _ in self.struct if _.bool]))

            self.checkJson(leftDeviating)

    def testDeviateWithWeightingFactor(self):
        for i in xrange(11):
            left, right = self.struct[:i], self.struct[i:]

            leftDeviating = Deviate(lambda x: x.double, lambda x: x.int)
            rightDeviating = Deviate(lambda x: x.double, lambda x: x.int)

            for _ in left: leftDeviating.fill(_)
            for _ in right: rightDeviating.fill(_)

            self.assertAlmostEqual(leftDeviating.variance, self.varianceWeighted(map(lambda _: _.double, left), map(lambda _: _.int, left)))
            self.assertAlmostEqual(rightDeviating.variance, self.varianceWeighted(map(lambda _: _.double, right), map(lambda _: _.int, right)))

            finalResult = leftDeviating + rightDeviating

            self.assertAlmostEqual(finalResult.variance, self.varianceWeighted(map(lambda _: _.double, self.struct), map(lambda _: _.int, self.struct)))

            self.checkJson(leftDeviating)

    ################################################################ AbsoluteErr

    def testAbsoluteErr(self):
        for i in xrange(11):
            left, right = self.simple[:i], self.simple[i:]

            leftAbsoluteErring = AbsoluteErr(lambda x: x)
            rightAbsoluteErring = AbsoluteErr(lambda x: x)

            for _ in left: leftAbsoluteErring.fill(_)
            for _ in right: rightAbsoluteErring.fill(_)

            self.assertAlmostEqual(leftAbsoluteErring.mae, self.mae(left))
            self.assertAlmostEqual(rightAbsoluteErring.mae, self.mae(right))

            finalResult = leftAbsoluteErring + rightAbsoluteErring

            self.assertAlmostEqual(finalResult.mae, self.mae(self.simple))

            self.checkJson(leftAbsoluteErring)
        
    ################################################################ Minimize

    def testMinimize(self):
        for i in xrange(11):
            left, right = self.simple[:i], self.simple[i:]

            leftMinimizing = Minimize(lambda x: x)
            rightMinimizing = Minimize(lambda x: x)

            for _ in left: leftMinimizing.fill(_)
            for _ in right: rightMinimizing.fill(_)

            if len(left) > 0:
                self.assertAlmostEqual(leftMinimizing.min, min(left))
            else:
                self.assertTrue(math.isnan(leftMinimizing.min))

            if len(right) > 0:
                self.assertAlmostEqual(rightMinimizing.min, min(right))
            else:
                self.assertTrue(math.isnan(rightMinimizing.min))

            finalResult = leftMinimizing + rightMinimizing

            self.assertAlmostEqual(finalResult.min, min(self.simple))

            self.checkJson(leftMinimizing)

    ################################################################ Maximize

    def testMaximize(self):
        for i in xrange(11):
            left, right = self.simple[:i], self.simple[i:]

            leftMaximizing = Maximize(lambda x: x)
            rightMaximizing = Maximize(lambda x: x)

            for _ in left: leftMaximizing.fill(_)
            for _ in right: rightMaximizing.fill(_)

            if len(left) > 0:
                self.assertAlmostEqual(leftMaximizing.max, max(left))
            else:
                self.assertTrue(math.isnan(leftMaximizing.max))

            if len(right) > 0:
                self.assertAlmostEqual(rightMaximizing.max, max(right))
            else:
                self.assertTrue(math.isnan(rightMaximizing.max))

            finalResult = leftMaximizing + rightMaximizing

            self.assertAlmostEqual(finalResult.max, max(self.simple))

            self.checkJson(leftMaximizing)

    ################################################################ Quantile

    def testQuantile(self):
        answers = [
            [float("nan"), -0.481328271104, -0.481328271104],
            [3.4, -0.69120847042, -0.282087623378],
            [-0.675, -0.736543753016, -0.724235002413],
            [-0.58125, -0.958145383329, -0.84507676833],
            [0.13623046875, -1.53190059408, -0.864648168945],
            [0.302100585937, -0.819002197266, -0.258450805664],
            [-0.942007507324, -0.629296875, -0.816923254395],
            [0.269603994253, -0.753125, -0.0372147040231],
            [-0.628724939722, 0.24375, -0.454229951778],
            [-0.562639074418, -1.7, -0.676375166976],
            [-0.481328271104, float("nan"), -0.481328271104],
            [float("nan"), -0.329460938614, -0.329460938614],
            [3.4, -0.457521896462, -0.0717697068155],
            [-0.45, -0.511698266503, -0.499358613202],
            [-0.425, -0.706904919683, -0.622333443778],
            [0.27890625, -0.937865017361, -0.451156510417],
            [0.599765625, -0.65764453125, -0.028939453125],
            [-0.637327473958, -0.471875, -0.571146484375],
            [0.536730209662, -0.595833333333, 0.196961146763],
            [-0.423513681061, 0.4875, -0.241310944849],
            [-0.382340803288, -1.7, -0.514106722959],
            [-0.329460938614, float("nan"), -0.329460938614],
            [float("nan"), -0.168649887325, -0.168649887325],
            [3.4, -0.227037303799, 0.135666426581],
            [-0.225, -0.265185561995, -0.257148449596],
            [-0.23125, -0.386842979665, -0.340165085765],
            [0.42275390625, -0.477651570638, -0.117489379883],
            [0.889514648438, -0.394795166016, 0.247359741211],
            [-0.322354390462, -0.264453125, -0.299193884277],
            [0.798766766295, -0.344791666667, 0.455699236407],
            [-0.213212483191, 0.73125, -0.0243199865526],
            [-0.194267772368, -1.7, -0.344840995131],
            [-0.168649887325, float("nan"), -0.168649887325],
            ]

        line = 0
        for p in 0.25, 0.5, 0.75:
            for i in xrange(11):
                left, right = self.simple[:i], self.simple[i:]

                leftQuantiling = Quantile(p, lambda x: x)
                rightQuantiling = Quantile(p, lambda x: x)

                for _ in left: leftQuantiling.fill(_)
                for _ in right: rightQuantiling.fill(_)

                finalResult = leftQuantiling + rightQuantiling

                leftAnswer, rightAnswer, finalAnswer = answers[line]
                line += 1

                if math.isnan(leftAnswer):
                    self.assertTrue(math.isnan(leftQuantiling.estimate))
                else:
                    self.assertAlmostEqual(leftQuantiling.estimate, leftAnswer)

                if math.isnan(rightAnswer):
                    self.assertTrue(math.isnan(rightQuantiling.estimate))
                else:
                    self.assertAlmostEqual(rightQuantiling.estimate, rightAnswer)

                if math.isnan(finalAnswer):
                    self.assertTrue(math.isnan(finalResult.estimate))
                else:
                    self.assertAlmostEqual(finalResult.estimate, finalAnswer)

                self.checkJson(leftQuantiling)

    ################################################################ Bag

    def testBag(self):
        one = Bag(lambda x: x)
        for _ in self.simple: one.fill(_)
        self.assertEqual(one.values, {7.3: 1.0, 2.2: 1.0, -1.7: 1.0, -4.7: 1.0, 0.0: 2.0, -1.8: 1.0, -3.0: 1.0, 1.6: 1.0, 3.4: 1.0})

        two = Bag(lambda x: (x, x))
        for _ in self.simple: two.fill(_)
        self.assertEqual(two.values, {(7.3, 7.3): 1.0, (2.2, 2.2): 1.0, (-1.7, -1.7): 1.0, (-4.7, -4.7): 1.0, (0.0, 0.0): 2.0, (-1.8, -1.8): 1.0, (-3.0, -3.0): 1.0, (1.6, 1.6): 1.0, (3.4, 3.4): 1.0})

        three = Bag(lambda x: x.string[0])
        for _ in self.struct: three.fill(_)
        self.assertEqual(three.values, {"n": 1.0, "e": 1.0, "t": 3.0, "s": 2.0, "f": 2.0, "o": 1.0})

        self.checkJson(one)
        self.checkJson(two)
        self.checkJson(three)

    def testBagWithLimit(self):
        one = Limit(Bag(lambda x: x.string), 20)
        for _ in self.struct: one.fill(_)
        self.assertEqual(one.get.values, {"one": 1.0, "two": 1.0, "three": 1.0, "four": 1.0, "five": 1.0, "six": 1.0, "seven": 1.0, "eight": 1.0, "nine": 1.0, "ten": 1.0})

        two = Limit(Bag(lambda x: x.string), 9)
        for _ in self.struct: two.fill(_)
        self.assertTrue(two.saturated)

        self.checkJson(one)
        self.checkJson(two)

    ################################################################ Bin

    def testBin(self):
        one = Bin(5, -3.0, 7.0, lambda x: x)
        for _ in self.simple: one.fill(_)
        self.assertEqual(map(lambda _: _.entries, one.values), [3.0, 2.0, 2.0, 1.0, 0.0])
        self.assertEqual(one.underflow.entries, 1.0)
        self.assertEqual(one.overflow.entries, 1.0)
        self.assertEqual(one.nanflow.entries, 0.0)

        two = Bin(5, -3.0, 7.0, lambda x: x.double, lambda x: x.bool)
        for _ in self.struct: two.fill(_)

        self.assertEqual(map(lambda _: _.entries, two.values), [2.0, 1.0, 1.0, 1.0, 0.0])
        self.assertEqual(two.underflow.entries, 0.0)
        self.assertEqual(two.overflow.entries, 0.0)
        self.assertEqual(two.nanflow.entries, 0.0)

        self.checkJson(one)
        self.checkJson(two)

    def testHistogram(self):
        one = Histogram(5, -3.0, 7.0, lambda x: x)

        for _ in self.simple: one.fill(_)
        self.assertEqual(map(lambda _: _.entries, one.values), [3.0, 2.0, 2.0, 1.0, 0.0])
        self.assertEqual(one.underflow.entries, 1.0)
        self.assertEqual(one.overflow.entries, 1.0)
        self.assertEqual(one.nanflow.entries, 0.0)

        two = Histogram(5, -3.0, 7.0, lambda x: x.double, lambda x: x.bool)
        for _ in self.struct: two.fill(_)
        self.assertEqual(map(lambda _: _.entries, two.values), [2.0, 1.0, 1.0, 1.0, 0.0])
        self.assertEqual(two.underflow.entries, 0.0)
        self.assertEqual(two.overflow.entries, 0.0)
        self.assertEqual(two.nanflow.entries, 0.0)

        self.checkJson(one)
        self.checkJson(two)

    ################################################################ SparselyBin

    def testSparselyBin(self):
        one = SparselyBin(1.0, lambda x: x)
        for _ in self.simple: one.fill(_)
        self.assertEqual([(i, v.entries) for i, v in sorted(one.bins.items())], [(-5, 1.0), (-3, 1.0), (-2, 2.0), (0, 2.0), (1, 1.0), (2, 1.0), (3, 1.0), (7, 1.0)])

        self.assertEqual(one.numFilled, 8)
        self.assertEqual(one.num, 13)
        self.assertEqual(one.low, -5.0)
        self.assertEqual(one.high, 8.0)

        self.checkJson(one)

    ################################################################ CentrallyBin

    def testCentrallyBin(self):
        one = CentrallyBin([-3.0, -1.0, 0.0, 1.0, 3.0, 10.0], lambda x: x)
        self.assertEqual(one.center(1.5), 1.0)
        self.assertEqual(one.neighbors(1.0), (0.0, 3.0))
        self.assertEqual(one.neighbors(10.0), (3.0, None))
        self.assertEqual(one.range(-3.0), (float("-inf"), -2.0))
        self.assertEqual(one.range(-1.0), (-2.0, -0.5))
        self.assertEqual(one.range(0.0), (-0.5, 0.5))
        self.assertEqual(one.range(10.0), (6.5, float("inf")))

        for _ in self.simple: one.fill(_)

        self.assertEqual([(c, v.entries) for c, v in one.bins], [(-3.0,2.0), (-1.0,2.0), (0.0,2.0), (1.0,1.0), (3.0,2.0), (10.0,1.0)])

        self.assertEqual(one.pdfTimesEntries(-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0), [0.7407407407407407, 1.3333333333333333, 1.3333333333333333, 2.0, 0.6666666666666666, 0.4444444444444444, 0.4444444444444444, 0.4444444444444444, 0.4444444444444444, 0.4444444444444444, 1.2500000000000002, 0.0, 0.0, 0.0])
        self.assertEqual(one.cdfTimesEntries(-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0), [1.2592592592592593, 2.0, 3.333333333333333, 5.0, 6.333333333333333, 7.0, 7.444444444444445, 7.888888888888889, 8.333333333333334, 8.777777777777779, 9.625, 10.0, 10.0, 10.0])
        self.assertEqual(one.qfTimesEntries(-1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0), [-4.7, -4.7, -3.35, -2.0, -1.25, -0.5, 0.0, 0.5, 2.0, 4.25, 6.5, 7.3, 7.3])

        self.checkJson(one)

    ################################################################ AdaptivelyBin

    def testAdaptivelyBin(self):
        one = AdaptivelyBin(lambda x: x, num=5)

        for _ in self.simple: one.fill(_)

        self.assertEqual(map(lambda (x, c): (x, c.entries), one.bins), [(-3.85, 2.0), (-1.1666666666666667, 3.0), (0.8, 2.0), (2.8, 2.0), (7.3, 1.0)])

        self.checkJson(one)

    ################################################################ Fraction

    def testFraction(self):
        fracking = Fraction(lambda x: x > 0.0, Count())
        for _ in self.simple: fracking.fill(_)

        self.assertEqual(fracking.numerator.entries, 4.0)
        self.assertEqual(fracking.denominator.entries, 10.0)

        self.checkJson(fracking)

    def testFractionSum(self):
        fracking = Fraction(lambda x: x > 0.0, Sum(lambda x: x))
        for _ in self.simple: fracking.fill(_)

        self.assertAlmostEqual(fracking.numerator.sum, 14.5)
        self.assertAlmostEqual(fracking.denominator.sum, 3.3)

        self.checkJson(fracking)

    def testFractionHistogram(self):
        fracking = Fraction(lambda x: x > 0.0, Histogram(5, -3.0, 7.0, lambda x: x))
        for _ in self.simple: fracking.fill(_)

        self.assertEqual(fracking.numerator.numericalValues, [0.0, 0.0, 2.0, 1.0, 0.0])
        self.assertEqual(fracking.denominator.numericalValues, [3.0, 2.0, 2.0, 1.0, 0.0])

        self.checkJson(fracking)

    ################################################################ Stack

    def testStack(self):
        stacking = Stack(Count(), lambda x: x, 0.0, 2.0, 4.0, 6.0, 8.0)
        for _ in self.simple: stacking.fill(_)        

        self.assertEqual([(k, v.entries) for k, v in stacking.cuts], [(float("-inf"), 10.0), (0.0, 6.0), (2.0, 3.0), (4.0, 1.0), (6.0, 1.0), (8.0, 0.0)])

        self.checkJson(stacking)

    ################################################################ Partition

    def testPartition(self):
        partitioning = Partition(Count(), lambda x: x, 0.0, 2.0, 4.0, 6.0, 8.0)
        for _ in self.simple: partitioning.fill(_)

        self.assertEqual([(k, v.entries) for k, v in partitioning.cuts], [(float("-inf"), 4.0), (0.0, 3.0), (2.0, 2.0), (4.0, 0.0), (6.0, 1.0), (8.0, 0.0)])

        self.checkJson(partitioning)

    def testPartitionSum(self):
        partitioning = Partition(Sum(lambda x: x), lambda x: x, 0.0, 2.0, 4.0, 6.0, 8.0)
        for _ in self.simple: partitioning.fill(_)

        self.assertAlmostEqual(partitioning.cuts[0][1].sum, -11.2)
        self.assertAlmostEqual(partitioning.cuts[1][1].sum, 1.6)

        self.checkJson(partitioning)

    ################################################################ Categorize

    def testCategorize(self):
        categorizing = Categorize(lambda x: x.string[0])
        for _ in self.struct: categorizing.fill(_)

        self.assertEqual({k: v.entries for k, v in categorizing.pairsMap.items()}, {"n": 1.0, "e": 1.0, "t": 3.0, "s": 2.0, "f": 2.0, "o": 1.0})

        self.checkJson(categorizing)

    ################################################################ Label

    def testLabel(self):
        one = Histogram(5, -3.0, 7.0, lambda x: x)
        two = Histogram(10, 0.0, 10.0, lambda x: x)
        three = Histogram(5, -3.0, 7.0, lambda x: 2*x)

        labeling = Label(one=one, two=two, three=three)

        for _ in self.simple: labeling.fill(_)

        self.assertEqual(labeling("one").numericalValues, [3.0, 2.0, 2.0, 1.0, 0.0])
        self.assertEqual(labeling("two").numericalValues, [2.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEqual(labeling("three").numericalValues, [0.0, 2.0, 0.0, 2.0, 1.0])

        self.checkJson(labeling)

    def testLabelDifferentCuts(self):
        one = Histogram(10, -10, 10, lambda x: x, lambda x: x > 0)
        two = Histogram(10, -10, 10, lambda x: x, lambda x: x > 5)
        three = Histogram(10, -10, 10, lambda x: x, lambda x: x < 5)

        labeling = Label(one=one, two=two, three=three)

        for _ in self.simple: labeling.fill(_)

        self.assertEqual(labeling("one").numericalValues, [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 1.0, 0.0])
        self.assertEqual(labeling("two").numericalValues, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        self.assertEqual(labeling("three").numericalValues, [0.0, 0.0, 1.0, 1.0, 2.0, 3.0, 2.0, 0.0, 0.0, 0.0])

        self.checkJson(labeling)

    ################################################################ UntypedLabel

    def testUntypedLabel(self):
        one = Histogram(5, -3.0, 7.0, lambda x: x)
        two = Histogram(10, 0.0, 10.0, lambda x: x)
        three = Histogram(5, -3.0, 7.0, lambda x: 2*x)

        labeling = UntypedLabel(one=one, two=two, three=three)

        for _ in self.simple: labeling.fill(_)

        self.assertEqual(labeling("one").numericalValues, [3.0, 2.0, 2.0, 1.0, 0.0])
        self.assertEqual(labeling("two").numericalValues, [2.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEqual(labeling("three").numericalValues, [0.0, 2.0, 0.0, 2.0, 1.0])

        self.checkJson(labeling)

    def testUntypedLabelDifferenCuts(self):
        one = Histogram(10, -10, 10, lambda x: x, lambda x: x > 0)
        two = Histogram(10, -10, 10, lambda x: x, lambda x: x > 5)
        three = Histogram(10, -10, 10, lambda x: x, lambda x: x < 5)

        labeling = UntypedLabel(one=one, two=two, three=three)

        for _ in self.simple: labeling.fill(_)

        self.assertEqual(labeling("one").numericalValues, [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 1.0, 0.0])
        self.assertEqual(labeling("two").numericalValues, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        self.assertEqual(labeling("three").numericalValues, [0.0, 0.0, 1.0, 1.0, 2.0, 3.0, 2.0, 0.0, 0.0, 0.0])

        self.checkJson(labeling)
        
    def testUntypedLabelMultipleTypes(self):
        one = Histogram(5, -3.0, 7.0, lambda x: x)
        two = Sum(lambda x: 1.0)
        three = Deviate(lambda x: x + 100.0)

        mapping = UntypedLabel(one=one, two=two, three=three)

        for _ in self.simple: mapping.fill(_)

        self.assertEqual(mapping("one").numericalValues, [3.0, 2.0, 2.0, 1.0, 0.0])
        self.assertEqual(mapping("two").sum, 10.0)
        self.assertAlmostEqual(mapping("three").entries, 10.0)
        self.assertAlmostEqual(mapping("three").mean, 100.33)
        self.assertAlmostEqual(mapping("three").variance, 10.8381)

        self.checkJson(mapping)

    ################################################################ Index

    def testIndex(self):
        one = Histogram(5, -3.0, 7.0, lambda x: x)
        two = Histogram(10, 0.0, 10.0, lambda x: x)
        three = Histogram(5, -3.0, 7.0, lambda x: 2*x)

        indexing = Index(one, two, three)

        for _ in self.simple: indexing.fill(_)

        self.assertEqual(indexing(0).numericalValues, [3.0, 2.0, 2.0, 1.0, 0.0])
        self.assertEqual(indexing(1).numericalValues, [2.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0])
        self.assertEqual(indexing(2).numericalValues, [0.0, 2.0, 0.0, 2.0, 1.0])

        self.checkJson(indexing)

    def testIndexDifferentCuts(self):
        one = Histogram(10, -10, 10, lambda x: x, lambda x: x > 0)
        two = Histogram(10, -10, 10, lambda x: x, lambda x: x > 5)
        three = Histogram(10, -10, 10, lambda x: x, lambda x: x < 5)

        indexing = Index(one, two, three)

        for _ in self.simple: indexing.fill(_)

        self.assertEqual(indexing(0).numericalValues, [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 1.0, 0.0])
        self.assertEqual(indexing(1).numericalValues, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
        self.assertEqual(indexing(2).numericalValues, [0.0, 0.0, 1.0, 1.0, 2.0, 3.0, 2.0, 0.0, 0.0, 0.0])

        self.checkJson(indexing)

    ################################################################ Branch

    def testBranch(self):
        one = Histogram(5, -3.0, 7.0, lambda x: x)
        two = Count()
        three = Deviate(lambda x: x + 100.0)

        branching = Branch(one, two, three)

        for _ in self.simple: branching.fill(_)

        self.assertEqual(branching.i0.numericalValues, [3.0, 2.0, 2.0, 1.0, 0.0])
        self.assertEqual(branching.i0.underflow.entries, 1.0)
        self.assertEqual(branching.i0.overflow.entries, 1.0)
        self.assertEqual(branching.i0.nanflow.entries, 0.0)

        self.assertEqual(branching.i1.entries, 10.0)

        self.assertAlmostEqual(branching.i2.entries, 10.0)
        self.assertAlmostEqual(branching.i2.mean, 100.33)
        self.assertAlmostEqual(branching.i2.variance, 10.8381)

        self.checkJson(branching)
        
    ################################################################ Usability in fold/aggregate

    # def testAggregate(self):
    #     pass
