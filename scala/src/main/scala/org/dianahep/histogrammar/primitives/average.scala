// Copyright 2016 Jim Pivarski
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package org.dianahep

import org.dianahep.histogrammar.json._
import org.dianahep.histogrammar.util._

package histogrammar {
  //////////////////////////////////////////////////////////////// Average/Averaged/Averaging

  /** Accumulate the weighted mean of a given quantity.
    * 
    * Factory produces mutable [[org.dianahep.histogrammar.Averaging]] and immutable [[org.dianahep.histogrammar.Averaged]] objects.
    */
  object Average extends Factory {
    val name = "Average"
    val help = "Accumulate the weighted mean of a given quantity."
    val detailedHelp = """Average(quantity: UserFcn[DATUM, Double])"""

    /** Create an immutable [[org.dianahep.histogrammar.Averaged]] from arguments (instead of JSON).
      * 
      * @param entries Weighted number of entries (sum of all observed weights).
      * @param quantityName Optional name given to the quantity function, passed for bookkeeping.
      * @param mean Weighted mean of the quantity.
      */
    def ed(entries: Double, quantityName: Option[String], mean: Double) = new Averaged(entries, quantityName, mean)

    /** Create an empty, mutable [[org.dianahep.histogrammar.Averaging]].
      * 
      * @param quantity Numerical function to track.
      */
    def apply[DATUM](quantity: UserFcn[DATUM, Double]) = new Averaging(quantity, 0.0, 0.0)

    /** Synonym for `apply`. */
    def ing[DATUM](quantity: UserFcn[DATUM, Double]) = apply(quantity)

    /** Use [[org.dianahep.histogrammar.Averaged]] in Scala pattern-matching. */
    def unapply(x: Averaged) = Some(x.mean)
    /** Use [[org.dianahep.histogrammar.Averaging]] in Scala pattern-matching. */
    def unapply[DATUM](x: Averaging[DATUM]) = Some(x.mean)

    import KeySetComparisons._
    def fromJsonFragment(json: Json): Container[_] = json match {
      case JsonObject(pairs @ _*) if (pairs.keySet has Set("entries", "mean").maybe("name")) =>
        val get = pairs.toMap

        val entries = get("entries") match {
          case JsonNumber(x) => x
          case x => throw new JsonFormatException(x, name + ".entries")
        }

        val quantityName = get.getOrElse("name", JsonNull) match {
          case JsonString(x) => Some(x)
          case JsonNull => None
          case x => throw new JsonFormatException(x, name + ".name")
        }

        val mean = get("mean") match {
          case JsonNumber(x) => x
          case x => throw new JsonFormatException(x, name + ".mean")
        }

        new Averaged(entries, quantityName, mean)

      case _ => throw new JsonFormatException(json, name)
    }

    private[histogrammar] def plus(ca: Double, mua: Double, cb: Double, mub: Double) =
      (ca + cb, (ca*mua + cb*mub)/(ca + cb))
  }

  /** An accumulated weighted mean of a given quantity.
    * 
    * Use the factory [[org.dianahep.histogrammar.Average]] to construct an instance.
    * 
    * @param entries Weighted number of entries (sum of all observed weights).
    * @param quantityName Optional name given to the quantity function, passed for bookkeeping.
    * @param mean Weighted mean of the quantity.
    */
  class Averaged private[histogrammar](val entries: Double, val quantityName: Option[String], val mean: Double) extends Container[Averaged] {
    type Type = Averaged
    def factory = Average

    if (entries < 0.0)
      throw new ContainerException(s"entries ($entries) cannot be negative")

    def zero = new Averaged(0.0, quantityName, 0.0)
    def +(that: Averaged) =
      if (this.quantityName != that.quantityName)
        throw new ContainerException(s"cannot add ${getClass.getName} because quantityName differs (${this.quantityName} vs ${that.quantityName})")
      else {
        val (newentries, newmean) = Average.plus(this.entries, this.mean, that.entries, that.mean)
        new Averaged(newentries, this.quantityName, newmean)
      }

    def toJsonFragment = JsonObject(
      "entries" -> JsonFloat(entries),
      "mean" -> JsonFloat(mean)).
      maybe(JsonString("name") -> quantityName.map(JsonString(_)))

    override def toString() = s"Averaged[$mean]"
    override def equals(that: Any) = that match {
      case that: Averaged => this.entries === that.entries  &&  this.quantityName == that.quantityName  &&  this.mean === that.mean
      case _ => false
    }
    override def hashCode() = (entries, quantityName, mean).hashCode
  }

  /** Accumulating a weighted mean of a given quantity.
    * 
    * Use the factory [[org.dianahep.histogrammar.Average]] to construct an instance.
    * 
    * @param quantity Numerical function to track.
    * @param entries Weighted number of entries (sum of all weights).
    * @param mean Cumulative weighted mean (accrued with a numerically stable algorithm).
    */
  class Averaging[DATUM] private[histogrammar](val quantity: UserFcn[DATUM, Double], var entries: Double, var mean: Double) extends Container[Averaging[DATUM]] with AggregationOnData {
    type Type = Averaging[DATUM]
    type FixedType = Averaged
    type Datum = DATUM
    def factory = Average

    if (entries < 0.0)
      throw new ContainerException(s"entries ($entries) cannot be negative")

    def zero = new Averaging[DATUM](quantity, 0.0, 0.0)
    def +(that: Averaging[DATUM]) =
      if (this.quantity.name != that.quantity.name)
        throw new ContainerException(s"cannot add ${getClass.getName} because quantity name differs (${this.quantity.name} vs ${that.quantity.name})")
      else {
        val (newentries, newmean) = Average.plus(this.entries, this.mean, that.entries, that.mean)
        new Averaging(this.quantity, newentries, newmean)
      }

    def fill[SUB <: Datum](datum: SUB, weight: Double = 1.0) {
      entries += weight
      if (weight > 0.0) {
        val q = quantity(datum)

        val delta = q - mean
        val shift = delta * weight / entries
        mean += shift
      }
    }

    def toJsonFragment = JsonObject(
      "entries" -> JsonFloat(entries),
      "mean" -> JsonFloat(mean)).
      maybe(JsonString("name") -> quantity.name.map(JsonString(_)))

    override def toString() = s"Averaging[$mean]"
    override def equals(that: Any) = that match {
      case that: Averaging[DATUM] => this.quantity == that.quantity  &&  this.entries === that.entries  &&  this.mean === that.mean
      case _ => false
    }
    override def hashCode() = (quantity, entries, mean).hashCode
  }
}
