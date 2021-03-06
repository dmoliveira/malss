# -*- coding: utf-8 -*-

import os
import numpy as np
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from sklearn.cross_validation import StratifiedKFold, KFold
from sklearn.grid_search import GridSearchCV
from sklearn.learning_curve import learning_curve
from sklearn.svm import SVC, LinearSVC, SVR
from sklearn.metrics import classification_report, f1_score
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression, Ridge, SGDRegressor,\
    SGDClassifier

from algorithm import Algorithm
from data import Data


class MALSS(object):
    def __init__(self, X, y, task, shuffle=True, n_jobs=1, random_state=0,
                 verbose=True):
        """
        Set the given training data.

        Parameters
        ----------
        X : {numpy.ndarray, pandas.DataFrame}, shape = [n_samples, n_features]
            Training vector, where n_samples in the number of samples and
            n_features is the number of features.
        y : {numpy.ndarray, pandas.Series}, shape = [n_samples]
            Target values (class labels in classification, real numbers in
            regression)
        task : string
            Specifies the task of the analysis. It must be one of
            'classification', 'regression'.
        shuffle : boolean, optional (default=True)
            Whether to shuffle the data.
        n_jobs : integer, optional (default=1)
            The number of jobs to run in parallel. If -1, then the number of
            jobs is set to the number of cores.
        random_state : int seed, RandomState instance, or None (default=0)
            The seed of the pseudo random number generator
        verbos : bool, default: True
            Enable verbose output.
        """

        self.shuffle = shuffle
        self.data = Data(X, y, shuffle, random_state)
        self.task = task
        self.n_jobs = n_jobs
        self.random_state = random_state
        self.verbose = verbose
        self.algorithms = self.__choose_algorithm()
        if task == 'classification':
            self.scoring = 'f1'
            self.cv = StratifiedKFold(self.data.y, n_folds=5, shuffle=True,
                                      random_state=self.random_state)
        elif task == 'regression':
            self.scoring = 'r2'
            self.cv = KFold(self.data.X.shape[0], n_folds=5, shuffle=True,
                            random_state=self.random_state)
        else:
            raise ValueError('task:%s is not supported' % task)

    def __choose_algorithm(self):
        algorithms = []
        if self.task == 'classification':
            if self.data.X.shape[0] * self.data.X.shape[1] <= 1e+06:
                if self.data.X.shape[0] ** 2 * self.data.X.shape[1] <= 1e+09:
                    algorithms.append(
                        Algorithm(
                            SVC(random_state=self.random_state),
                            [{'kernel': ['rbf'],
                              'C': [10, 100, 1000, 10000],
                              'gamma': [1e-4, 1e-3, 1e-2, 1e-1]}],
                            'Support Vector Machine (RBF Kernel)'))
                algorithms.append(
                    Algorithm(
                        LinearSVC(random_state=self.random_state),
                        [{'C': [0.1, 1, 10, 100]}],
                        'Support Vector Machine (Linear Kernel)'))
                algorithms.append(
                    Algorithm(
                        LogisticRegression(random_state=self.random_state),
                        [{'penalty': ['l2', 'l1'],
                          'C': [0.1, 0.3, 1, 3, 10],
                          'class_weight': [None, 'auto']}],
                        'Logistic Regression'))
                algorithms.append(
                    Algorithm(
                        DecisionTreeClassifier(random_state=self.random_state),
                        [{'max_depth': [3, 5, 7, 9, 11]}],
                        'Decision Tree'))
                algorithms.append(
                    Algorithm(
                        KNeighborsClassifier(),
                        [{'n_neighbors': [2, 6, 10, 14, 18]}],
                        'k-Nearest Neighbors'))
            else:
                algorithms.append(
                    Algorithm(
                        SGDClassifier(
                            random_state=self.random_state,
                            n_jobs=self.n_jobs),
                        [{'loss': ['hinge', 'log'],
                          'penalty': ['l2', 'l1'],
                          'alpha': [1e-05, 3e-05, 1e-04, 3e-04, 1e-03],
                          'class_weight': [None, 'auto']}],
                        'SGD Classifier'))
        if self.task == 'regression':
            if self.data.X.shape[0] * self.data.X.shape[1] <= 1e+06:
                if self.data.X.shape[0] ** 2 * self.data.X.shape[1] <= 1e+09:
                    algorithms.append(
                        Algorithm(
                            SVR(random_state=self.random_state),
                            [{'kernel': ['rbf'],
                              'C': [10, 100, 1000, 10000],
                              'gamma': [1e-4, 1e-3, 1e-2, 1e-1]}],
                            'Support Vector Machine (RBF Kernel)'))
                algorithms.append(
                    Algorithm(
                        Ridge(),
                        [{'alpha':
                            [0.01, 0.1, 1, 10, 100]}],
                        'Ridge Regression'))
            else:
                algorithms.append(
                    Algorithm(
                        SGDRegressor(
                            random_state=self.random_state),
                        [{'penalty': ['l2', 'l1'],
                          'alpha': [1e-05, 3e-05, 1e-04, 3e-04, 1e-03]}],
                        'SGD Regressor'))
        return algorithms

    def execute(self):
        self.__tune_parameters()
        if self.task == 'classification':
            self.__report_classification_result()

    def __search_best_algorithm(self):
        self.best_score = float('-Inf')
        self.best_index = -1
        for i in xrange(len(self.algorithms)):
            if self.algorithms[i].best_score > self.best_score:
                self.best_score = self.algorithms[i].best_score
                self.best_index = i
        self.algorithms[self.best_index].is_best_algorithm = True

    def __tune_parameters(self):
        for i in xrange(len(self.algorithms)):
            estimator = self.algorithms[i].estimator
            parameters = self.algorithms[i].parameters
            sc = f1score if self.scoring == 'f1' else self.scoring
            clf = GridSearchCV(
                estimator, parameters, cv=self.cv, scoring=sc,
                n_jobs=self.n_jobs)
            clf.fit(self.data.X, self.data.y)
            self.algorithms[i].estimator = clf.best_estimator_
            self.algorithms[i].best_score = clf.best_score_
            self.algorithms[i].best_params = clf.best_params_
            self.algorithms[i].grid_scores = clf.grid_scores_

        self.__search_best_algorithm()

    def __report_classification_result(self):
        for i in xrange(len(self.algorithms)):
            est = self.algorithms[i].estimator
            self.algorithms[i].classification_report =\
                classification_report(self.data.y, est.predict(self.data.X))

    def __plot_learning_curve(self, dname=None):
        for alg in self.algorithms:
            estimator = alg.estimator
            train_sizes, train_scores, test_scores = learning_curve(
                estimator,
                self.data.X,
                self.data.y,
                cv=self.cv,
                n_jobs=self.n_jobs)
            train_scores_mean = np.mean(train_scores, axis=1)
            train_scores_std = np.std(train_scores, axis=1)
            test_scores_mean = np.mean(test_scores, axis=1)
            test_scores_std = np.std(test_scores, axis=1)

            plt.figure()
            plt.title(estimator.__class__.__name__)
            plt.xlabel("Training examples")
            plt.ylabel("Score")
            plt.grid()

            plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
                             train_scores_mean + train_scores_std, alpha=0.1,
                             color="r")
            plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
                             test_scores_mean + test_scores_std,
                             alpha=0.1, color="g")
            plt.plot(train_sizes, train_scores_mean, 'o-', color="r",
                     label="Training score")
            plt.plot(train_sizes, test_scores_mean, 'o-', color="g",
                     label="Cross-validation score")

            plt.legend(loc="lower right")
            if dname is not None and not os.path.exists(dname):
                os.mkdir(dname)
            if dname is not None:
                plt.savefig('%s/learning_curve_%s.png' %
                            (dname, estimator.__class__.__name__),
                            bbox_inches='tight', dpi=75)
            else:
                plt.savefig('learning_curve_%s.png' %
                            estimator.__class__.__name__,
                            bbox_inches='tight', dpi=75)
            plt.close()

    def make_report(self, dname='report'):
        """
        Make the report

        Parameters
        ----------
        dname : string (default="report")
            A string containing a path to a output directory.
        """

        if not os.path.exists(dname):
            os.mkdir(dname)

        self.__plot_learning_curve(dname)

        env = Environment(
            loader=FileSystemLoader(
                os.path.abspath(
                    os.path.dirname(__file__)) + '/template', encoding='utf8'))
        tmpl = env.get_template('report.html.tmp')

        html = tmpl.render(algorithms=self.algorithms,
                           scoring=self.scoring,
                           taks=self.task,
                           data=self.data,
                           verbose=self.verbose).encode('utf-8')
        fo = open(dname + '/report.html', 'w')
        fo.write(html)
        fo.close()

    def make_sample_code(self, fname='sample_code.py'):
        env = Environment(
            loader=FileSystemLoader(
                os.path.abspath(
                    os.path.dirname(__file__)) + '/template', encoding='utf8'))
        tmpl = env.get_template('sample_code.py.tmp')
        encoded = True if len(self.data.del_columns) > 0 else False
        html = tmpl.render(algorithm=self.algorithms[self.best_index],
                           encoded=encoded).encode('utf-8')
        fo = open(fname, 'w')
        fo.write(html)
        fo.close()


def f1score(estimator, X, y):
    return f1_score(y, estimator.predict(X), average=None).mean()


if __name__ == "__main__":
    pass
