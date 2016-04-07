package org.dianahep

import org.dianahep.histogrammar.json._

package histogrammar {
  //////////////////////////////////////////////////////////////// AbsoluteErr/AbsoluteErred/AbsoluteErring

  object AbsoluteErr extends Factory {
    val name = "AbsoluteErr"
    val help = "Accumulate a count and a weighted mean absolute error of a given quantity whose nominal value is zero."
    val detailedHelp = """AbsoluteErr(quantity: NumericalFcn[DATUM], selection: Selection[DATUM] = unweighted[DATUM])"""

    def container(count: Double, mae: Double) = new AbsoluteErred(count, mae)
    def apply[DATUM](quantity: NumericalFcn[DATUM], selection: Selection[DATUM] = unweighted[DATUM]) = new AbsoluteErring(quantity, selection, 0.0, 0.0)

    def unapply(x: AbsoluteErred) = Some((x.count, x.mae))
    def unapply(x: AbsoluteErring[_]) = Some((x.count, x.mae))

    def fromJsonFragment(json: Json): Container[_] = json match {
      case JsonObject(pairs @ _*) if (pairs.keySet == Set("count", "mae")) =>
        val get = pairs.toMap

        val count = get("count") match {
          case JsonNumber(x) => x
          case x => throw new JsonFormatException(x, name + ".count")
        }

        val mae = get("mae") match {
          case JsonNumber(x) => x
          case x => throw new JsonFormatException(x, name + ".mae")
        }

        new AbsoluteErred(count, mae)

      case _ => throw new JsonFormatException(json, name)
    }

    private[histogrammar] def plus(ca: Double, ma: Double, cb: Double, mb: Double) =
      (ca + cb, (ca*ma + cb*mb)/(ca + cb))
  }

  class AbsoluteErred(val count: Double, val mae: Double) extends Container[AbsoluteErred] {
    def factory = AbsoluteErr

    def +(that: AbsoluteErred) = {
      val (newcount, newmae) = AbsoluteErr.plus(this.count, this.mae, that.count, that.mae)
      new AbsoluteErred(newcount, newmae)
    }

    def toJsonFragment = JsonObject("count" -> JsonFloat(count), "mae" -> JsonFloat(mae))

    override def toString() = s"AbsoluteErred"
    override def equals(that: Any) = that match {
      case that: AbsoluteErred => this.count === that.count  &&  this.mae === that.mae
      case _ => false
    }
    override def hashCode() = (count, mae).hashCode
  }

  class AbsoluteErring[DATUM](val quantity: NumericalFcn[DATUM], val selection: Selection[DATUM], var count: Double, _mae: Double) extends Container[AbsoluteErring[DATUM]] with Aggregation[DATUM] {
    def factory = AbsoluteErr

    private var absoluteSum = count * _mae

    def mae =
      if (count == 0.0)
        _mae
      else
        absoluteSum / count

    def mae_(_mae: Double) {
      absoluteSum = count * _mae
    }

    def +(that: AbsoluteErring[DATUM]) = {
      val (newcount, newmae) = AbsoluteErr.plus(this.count, this.mae, that.count, that.mae)
      new AbsoluteErring[DATUM](this.quantity, this.selection, newcount, newmae)
    }

    def fillWeighted(x: Weighted[DATUM]) {
      val Weighted(datum, weight) = x

      val w = weight * selection(datum)
      if (w > 0.0) {
        val q = quantity(datum)
        absoluteSum += Math.abs(q)
        count += w
      }
    }

    def toJsonFragment = JsonObject("count" -> JsonFloat(count), "mae" -> JsonFloat(mae))

    override def toString() = s"AbsoluteErring"
    override def equals(that: Any) = that match {
      case that: AbsoluteErring[DATUM] => this.quantity == that.quantity  &&  this.selection == that.selection  &&  this.count === that.count  &&  this.mae === that.mae
      case _ => false
    }
    override def hashCode() = (quantity, selection, count, mae).hashCode
  }
}
