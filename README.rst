MAchine Learning Support System
###############################

``malss`` is a python module to facilitate system development using machine learning algorithms.

.. image:: https://travis-ci.org/canard0328/malss.svg?branch=master
    :target: https://travis-ci.org/canard0328/malss

Requirements
************

These are external packages which you will need to install before installing malss.

* python (>= 2.7, 3.x's are not supported)
* numpy (>= 1.6.1)
* scipy (>= 0.9)
* scikit-learn (>= 0.14)
* matplotlib (>= 1.3)
* pandas (>= 0.13)
* jinja2 (>= 2.7)

**Windows**

If there are no binary packages matching your Python version you might to try to install these dependencies from `Christoph Gohlke Unofficial Windows installers <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_.

Installation
************
::

  pip install malss

Example
*******

Classification::

  from malss import MALSS
  from sklearn.datasets import load_iris
  iris = load_iris()
  cls = MALSS(iris.data, iris.target, task='classification')
  cls.execute()
  cls.make_report('classification_result')
  cls.make_sample_code('classification_sample_code.py')

Regression::

  from malss import MALSS
  from sklearn.datasets import load_boston
  boston = load_boston()
  cls = MALSS(boston.data, boston.target, task='regression')
  cls.execute()
  cls.make_report('regression_result')
  cls.make_sample_code('regression_sample_code.py')
