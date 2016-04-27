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

#ifndef HISTOGRAMMAR_HPP
#define HISTOGRAMMAR_HPP

#include <algorithm>
#include <math.h>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "json.hpp"

using json = nlohmann::json;

namespace histogrammar {
  //////////////////////////////////////////////////////////////// utilities

  template <typename DATUM>
  std::function<double(DATUM)> makeUnweighted() {
    return [](DATUM datum){return 1.0;};
  }

  //////////////////////////////////////////////////////////////// general definition of an container, its factory, and mix-in

  class Factory {
  public:
    virtual std::string name() = 0;
    // virtual int fromJsonFragment() = 0;   // FIXME
    // static int fromJson();                // FIXME
  };

  template <typename CONTAINER>
  class Container {
  public:
    virtual double entries() = 0;
    virtual std::unique_ptr<CONTAINER> zero() = 0;
    virtual std::unique_ptr<CONTAINER> plus(std::unique_ptr<CONTAINER> &that) = 0;
  };

  template <typename DATUM>
  class Aggregation {
  public:
    virtual void fill(DATUM datum, double weight = 1.0) = 0;
  };

  //////////////////////////////////////////////////////////////// Count/Counted/Counting

  class Counted;
  template <typename DATUM> class Counting;

  class Count : public Factory {
  public:
    std::string name() { return "Count"; }
    static std::unique_ptr<Counted> ed(double entries);
    template <typename DATUM>
    static std::unique_ptr<Counting<DATUM> > ing();
  };

  class Counted : public Container<Counted> {
    friend class Count;
  private:
    double entries_;
    Counted(double entries) : entries_(entries) { }
  public:
    double entries() { return entries_; }
    std::unique_ptr<Counted> zero() { return std::unique_ptr<Counted>(new Counted(0.0)); }
    std::unique_ptr<Counted> plus(std::unique_ptr<Counted> &that) {
      return std::unique_ptr<Counted>(new Counted(this->entries() + that->entries()));
    }
  };

  template <typename DATUM>
  class Counting : public Container<Counting<DATUM> >, public Aggregation<DATUM> {
    friend class Count;
  private:
    double entries_;
    Counting(double entries) : entries_(entries) { }
  public:
    double entries() { return entries_; }
    std::unique_ptr<Counting<DATUM> > zero() { return std::unique_ptr<Counting<DATUM> >(new Counting<DATUM>(0.0)); }
    std::unique_ptr<Counting<DATUM> > plus(std::unique_ptr<Counting<DATUM> > &that) {
      return std::unique_ptr<Counting<DATUM> >(new Counting<DATUM>(this->entries() + that->entries()));
    }
    void fill(DATUM datum, double weight = 1.0) {
      entries_ += weight;
    }
  };

  std::unique_ptr<Counted> Count::ed(double entries) { return std::unique_ptr<Counted>(new Counted(entries)); }

  template <typename DATUM>
  std::unique_ptr<Counting<DATUM> > Count::ing() { return std::unique_ptr<Counting<DATUM> >(new Counting<DATUM>(0.0)); }

  //////////////////////////////////////////////////////////////// Sum/Summed/Summing

  class Summed;
  template <typename DATUM> class Summing;

  class Sum : public Factory {
  public:
    std::string name() { return "Sum"; }
    static std::unique_ptr<Summed> ed(double entries, double sum);
    template <typename DATUM>
    static std::unique_ptr<Summing<DATUM> > ing(std::function<double(DATUM)> quantity, std::function<double(DATUM)> selection = makeUnweighted<DATUM>());
  };

  class Summed : public Container<Summed> {
    friend class Sum;
  private:
    double entries_;
    double sum_;
    Summed(double entries, double sum) : entries_(entries), sum_(sum) { }
  public:
    double entries() { return entries_; }
    double sum() { return sum_; }
    std::unique_ptr<Summed> zero() { return std::unique_ptr<Summed>(new Summed(0.0, 0.0)); }
    std::unique_ptr<Summed> plus(std::unique_ptr<Summed> &that) {
      return std::unique_ptr<Summed>(new Summed(this->entries() + that->entries(), this->sum() + that->sum()));
    }
  };

  template <typename DATUM>
  class Summing : public Container<Summing<DATUM> >, public Aggregation<DATUM> {
    friend class Sum;
  private:
    double entries_;
    double sum_;
    Summing(std::function<double(DATUM)> quantity, std::function<double(DATUM)> selection, double entries, double sum) : quantity(quantity), selection(selection), entries_(entries), sum_(sum) { }
  public:
    const std::function<double(DATUM)> quantity;
    const std::function<double(DATUM)> selection;
    double entries() { return entries_; }
    double sum() { return sum_; }
    std::unique_ptr<Summing<DATUM> > zero() { return std::unique_ptr<Summing<DATUM> >(new Summing<DATUM>(quantity, selection, 0.0, 0.0)); }
    std::unique_ptr<Summing<DATUM> > plus(std::unique_ptr<Summing<DATUM> > &that) {
      return std::unique_ptr<Summing<DATUM> >(new Summing<DATUM>(quantity, selection, this->entries() + that->entries(), this->sum() + that->sum()));
    }
    void fill(DATUM datum, double weight = 1.0) {
      double w = weight * selection(datum);
      if (w > 0.0) {
        double q = quantity(datum);
        entries_ += w;
        sum_ += q * w;
      }
    }
  };

  std::unique_ptr<Summed> Sum::ed(double entries, double sum) { return std::unique_ptr<Summed>(new Summed(entries, sum)); }

  template <typename DATUM>
  std::unique_ptr<Summing<DATUM> > Sum::ing(std::function<double(DATUM)> quantity, std::function<double(DATUM)> selection) { return std::unique_ptr<Summing<DATUM> >(new Summing<DATUM>(quantity, selection, 0.0, 0.0)); }

  //////////////////////////////////////////////////////////////// Bin/Binned/Binning

  // class Binned;
  // template <typename DATUM> class Binning;

  // class Bin : public Factory {
  // public:
  //   std::string name() { return "Bin"; }
  //   static std::unique_ptr<Binned> ed(double low, double high, double entries, std::vector<std::unique_ptr<> > values);
  //   template <typename DATUM>
  //   static std::unique_ptr<Binning<DATUM> > ing(std::function<double(DATUM)> quantity, std::function<double(DATUM)> selection = makeUnweighted<DATUM>());
  // };

  class BinMethods {
  public:
    virtual int num() = 0;
    virtual double low() = 0;
    virtual double high() = 0;

    int bin(double x) {
      if (under(x)  ||  over(x)  ||  nan(x))
        return -1;
      else
        return (int)floor(num() * (x - low()) / (high() - low()));
    }

    bool under(double x) {
      return !isnan(x)  &&  x < low();
    }
    bool over(double x) {
      return !isnan(x)  &&  x >= high();
    }
    bool nan(double x) {
      return isnan(x);
    }

    std::vector<int> indexes() {
      std::vector<int> out(num());
      std::iota(out.begin(), out.end(), 0);
      return out;   // should be NRVO-optimized, not a copy, right?
    }
    std::pair<double, double> range(int index) {
      return std::pair<double, double>((high() - low()) * index / num() + low(), (high() - low()) * (index + 1) / num() + low());
    }
  };

  template <typename V>
  class Binned : public Container<Binned<V> >, public BinMethods {
    friend class Bin;
  protected:
    double low_;
    double high_;
    double entries_;
    std::vector<std::unique_ptr<V> > values_;
    Binned(double low, double high, double entries, std::vector<std::unique_ptr<V> > values) : low_(low), high_(high), entries_(entries), values_(values) {
      static_assert(std::is_base_of<Container<V>, V>::value, "Binned values type must be a Container");
      if (low >= high)
        throw std::invalid_argument(std::string("low (") + std::to_string(low) + std::string(") must be less than high (") + std::to_string(high) + std::string(")"));
      if (values.size() < 1)
        throw std::invalid_argument(std::string("values must have at least one element"));
      if (entries < 0.0)
        throw std::invalid_argument(std::string("entries (") + std::to_string(entries) + std::string(") cannot be negative"));
    }
  public:
    int num() { return values_.size(); }
    double low() { return low_; }
    double high() { return high_; }
    double entries() { return entries_; }
    std::vector<std::unique_ptr<V> > values() { return values_; }

    std::unique_ptr<V> at(int index) { return values_(index); }

    std::unique_ptr<Binned<V> > zero() {
      return std::unique_ptr<Binned<V> >(new Binned<V>(low_, high_, entries_, std::transform(values_.begin(), values_.end(), [](std::unique_ptr<V> v){v->zero();})));
    }
    std::unique_ptr<Binned<V> > plus(std::unique_ptr<Binned<V> > &that) {
      if (this->low() != that->low())
        throw std::invalid_argument(std::string("cannot add Binned because low differs (") + std::to_string(this->low()) + std::string(" vs ") + std::string(that->low()) + std::string(")"));
      if (this->high() != that->high())
        throw std::invalid_argument(std::string("cannot add Binned because high differs (") + std::to_string(this->high()) + std::string(" vs ") + std::string(that->high()) + std::string(")"));
      if (this->num() != that->num())
        throw std::invalid_argument(std::string("cannot add Binned because number of values differs (") + std::to_string(this->num()) + std::string(" vs ") + std::string(that->num()) + std::string(")"));

      std::vector<std::unique_ptr<V> > newvalues(num());
      for (int i = 0;  i < num();  i++)
        newvalues[i] = this->at(i).plus(that->at(i));

      return std::unique_ptr<Binned<V> >(new Binned<V>(low_, high_, entries_, newvalues));
    }
  };

  template <typename DATUM, typename V>
  class Binning : public Container<Binning<DATUM, V> >, public Aggregation<DATUM>, public BinMethods {
    friend class Bin;
  private:
    double low_;
    double high_;
    double entries_;
    std::vector<std::unique_ptr<V> > values_;
    Binning(double low, double high, std::function<double(DATUM)> quantity, std::function<double(DATUM)> selection, double entries, std::vector<std::unique_ptr<V> > values) : low_(low), high_(high), quantity(quantity), selection(selection), values_(values) {
      static_assert(std::is_base_of<Container<V>, V>::value, "Binning values type must be a Container");
      static_assert(std::is_base_of<Aggregation<DATUM>, V>::value, "Binning values type must have Aggregation for this data type");
      if (low >= high)
        throw std::invalid_argument(std::string("low (") + std::to_string(low) + std::string(") must be less than high (") + std::to_string(high) + std::string(")"));
      if (values.size() < 1)
        throw std::invalid_argument(std::string("values must have at least one element"));
      if (entries < 0.0)
        throw std::invalid_argument(std::string("entries (") + std::to_string(entries) + std::string(") cannot be negative"));
    }
  public:
    const std::function<double(DATUM)> quantity;
    const std::function<double(DATUM)> selection;

    int num() { return values_.size(); }
    double low() { return low_; }
    double high() { return high_; }
    double entries() { return entries_; }
    std::vector<std::unique_ptr<V> > values() { return values_; }

    std::unique_ptr<V> at(int index) { return values_(index); }

    std::unique_ptr<Binning<DATUM, V> > zero() {
      return std::unique_ptr<Binning<DATUM, V> >(new Binning<DATUM, V>(low_, high_, entries_, std::transform(values_.begin(), values_.end(), [](std::unique_ptr<V> v){v->zero();})));
    }
    std::unique_ptr<Binning<DATUM, V> > plus(std::unique_ptr<Binning<DATUM, V> > &that) {
      if (this->low() != that->low())
        throw std::invalid_argument(std::string("cannot add Binned because low differs (") + std::to_string(this->low()) + std::string(" vs ") + std::string(that->low()) + std::string(")"));
      if (this->high() != that->high())
        throw std::invalid_argument(std::string("cannot add Binned because high differs (") + std::to_string(this->high()) + std::string(" vs ") + std::string(that->high()) + std::string(")"));
      if (this->num() != that->num())
        throw std::invalid_argument(std::string("cannot add Binned because number of values differs (") + std::to_string(this->num()) + std::string(" vs ") + std::string(that->num()) + std::string(")"));

      std::vector<std::unique_ptr<V> > newvalues(num());
      for (int i = 0;  i < num();  i++)
        newvalues[i] = this->at(i).plus(that->at(i));

      return std::unique_ptr<Binning<DATUM, V> >(new Binning<DATUM, V>(low_, high_, entries_, newvalues));
    }

    void fill(DATUM datum, double weight = 1.0) {
      double w = weight * selection(datum);
      if (w > 0.0) {
        double q = quantity(datum);

        entries_ += w;
        if (under(q))
          nullptr;
        else if (over(q))
          nullptr;
        else if (nan(q))
          nullptr;
        else
          values_[bin(q)]->fill(datum, w);
      }
    }
  };

  // std::unique_ptr<Binned> Bin::ed(double entries, double sum) { return std::unique_ptr<Binned>(new Binned(entries, sum)); }

  // template <typename DATUM>
  // std::unique_ptr<Binning<DATUM> > Bin::ing(std::function<double(DATUM)> quantity, std::function<double(DATUM)> selection) { return std::unique_ptr<Binning<DATUM> >(new Binning<DATUM>(quantity, selection)); }


}

#endif // HISTOGRAMMAR_HPP
