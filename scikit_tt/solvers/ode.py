#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scikit_tt.tensor_train as tt
import scikit_tt.utils as utl
from scikit_tt.solvers import sle
import numpy as np


def implicit_euler(operator, initial_value, initial_guess, step_sizes, repeats=1, tt_solver='als', threshold=1e-12,
                   max_rank=np.infty, micro_solver='solve', progress=True):
    """Implicit Euler method for linear differential equations in the TT format

    Parameters
    ----------
    operator: instance of TT class
        TT operator of the differential equation
    initial_value: instance of TT class
        initial value of the differential equation
    initial_guess: instance of TT class
        initial guess for the first step
    step_sizes: list of floats
        step sizes for the application of the implicit Euler method
    repeats: int, optional
        number of repeats of the (M)ALS in each iteration step, default is 1
    tt_solver: string, optional
        algorithm for solving the systems of linear equations in the TT format, default is 'als'
    threshold: float, optional
        threshold for reduced SVD decompositions, default is 1e-12
    max_rank: int, optional
        maximum rank of the solution, default is infinity
    micro_solver: string, optional
        algorithm for obtaining the solutions of the micro systems, can be 'solve' or 'lu', default is 'solve'
    progress: bool, optional
        whether to show the progress of the algorithm or not, default is True

    Returns
    -------
    solution: list of instances of the TT class
        numerical solution of the differential equation
    """

    # define solution
    solution = [initial_value]

    # define temporary tensor train
    tt_tmp = initial_guess

    # begin implicit Euler method
    # ---------------------------

    for i in range(len(step_sizes)):

        # solve system of linear equations for current time step
        if tt_solver == 'als':
            tt_tmp = sle.als(tt.eye(operator.row_dims) - step_sizes[i] * operator, tt_tmp, solution[i],
                             solver=micro_solver, repeats=repeats)
        if tt_solver == 'mals':
            tt_tmp = sle.mals(tt.eye(operator.row_dims) - step_sizes[i] * operator, tt_tmp, solution[i],
                              solver=micro_solver, threshold=threshold, repeats=repeats, max_rank=max_rank)

        # normalize solution
        tt_tmp = (1 / tt_tmp.norm(p=1)) * tt_tmp

        # append solution
        solution.append(tt_tmp.copy())

        # print progress
        if progress is True:
            utl.progress('Running implicit Euler method', 100 * i / (len(step_sizes) - 1))

    return solution


def errors_impl_euler(operator, solution, step_sizes):
    """Compute approximation errors of the implicit Euler method

    Parameters
    ----------
    operator: instance of TT class
        TT operator of the differential equation
    solution: list of instances of TT class
        approximate solution of the linear differential equation
    step_sizes: list of floats
        step sizes for the application of the implicit Euler method

    Returns
    -------
    errors: list of floats
        approximation errors
    """

    # define errors
    errors = []

    # compute relative approximation errors
    for i in range(len(solution) - 1):
        errors.append(
            ((tt.eye(operator.row_dims) - step_sizes[i] * operator) @ solution[i + 1] - solution[i]).norm() /
            solution[i].norm())

    return errors


def trapezoidal_rule(operator, initial_value, initial_guess, step_sizes, repeats=1, tt_solver='als', threshold=1e-12,
                     max_rank=np.infty, micro_solver='solve', progress=True):
    """Trapezoidal rule for linear differential equations in the TT format

    Parameters
    ----------
    operator: instance of TT class
        TT operator of the differential equation
    initial_value: instance of TT class
        initial value of the differential equation
    initial_guess: instance of TT class
        initial guess for the first step
    step_sizes: list of floats
        step sizes for the application of the trapezoidal rule
    repeats: int, optional
        number of repeats of the (M)ALS in each iteration step, default is 1
    tt_solver: string, optional
        algorithm for solving the systems of linear equations in the TT format, default is 'als'
    threshold: float, optional
        threshold for reduced SVD decompositions, default is 1e-12
    max_rank: int, optional
        maximum rank of the solution, default is infinity
    micro_solver: string, optional
        algorithm for obtaining the solutions of the micro systems, can be 'solve' or 'lu', default is 'solve'
    progress: bool, optional
        whether to show the progress of the algorithm or not, default is True

    Returns
    -------
    solution: list of instances of the TT class
        numerical solution of the differential equation
    """

    # define solution
    solution = [initial_value]

    # define temporary tensor train
    tt_tmp = initial_guess

    # begin trapezoidal rule
    # ----------------------

    for i in range(len(step_sizes)):

        # solve system of linear equations for current time step
        if tt_solver == 'als':
            tt_tmp = sle.als(tt.eye(operator.row_dims) - 0.5 * step_sizes[i] * operator, tt_tmp,
                             (tt.eye(operator.row_dims) + 0.5 * step_sizes[i] * operator) @ solution[i],
                             solver=micro_solver, repeats=repeats)
        if tt_solver == 'mals':
            tt_tmp = sle.mals(tt.eye(operator.row_dims) - 0.5 * step_sizes[i] * operator, tt_tmp,
                              (tt.eye(operator.row_dims) + 0.5 * step_sizes[i] * operator) @ solution[i],
                              solver=micro_solver, repeats=repeats, threshold=threshold, max_rank=max_rank)

        # normalize solution
        tt_tmp = (1 / tt_tmp.norm(p=1)) * tt_tmp

        # append solution
        solution.append(tt_tmp.copy())

        # print progress
        if progress is True:
            utl.progress('Running trapezoidal rule', 100 * i / (len(step_sizes) - 1))

    return solution


def errors_trapezoidal(operator, solution, step_sizes):
    """Compute approximation errors of the trapezoidal rule

    Parameters
    ----------
    operator: instance of TT class
        TT operator of the differential equation
    solution: list of instances of TT class
        approximate solution of the linear differential equation
    step_sizes: list of floats
        step sizes for the application of the implicit Euler method

    Returns
    -------
    errors: list of floats
        approximation errors
    """

    # define errors
    errors = []

    # compute relative approximation errors
    for i in range(len(solution) - 1):
        errors.append(((tt.eye(operator.row_dims) - 0.5 * step_sizes[i] * operator) @ solution[i + 1] -
                       (tt.eye(operator.row_dims) + 0.5 * step_sizes[i] * operator) @ solution[i]).norm() /
                      (tt.eye(operator.row_dims) + 0.5 * step_sizes[i] * operator) @ solution[i].norm())

    return errors


def adaptive_als(operator, initial_value, initial_guess, time_end, step_size_first=1e-10, repeats=1, solver='solve',
                 error_tol=1e-1, closeness_tol=0.5, step_size_min=1e-14, step_size_max=10, closeness_min=1e-3,
                 factor_max=2, factor_safe=0.9, second_method='two_step_Euler'):
    """Adaptive step size method

    Parameters
    ----------
    operator: instance of TT class
        TT operator of the differential equation
    initial_value: instance of TT class
        initial value of the differential equation
    initial_guess: instance of TT class
        initial guess for the first step
    time_end: float
        time point to which the ODE should be integrated
    step_size_first: float, optional
        first time step, default is 1e-10
    repeats: int, optional
        number of repeats of the ALS in each iteration step, default is 1
    solver: string, optional
        algorithm for obtaining the solutions of the micro systems, can be 'solve' or 'lu', default is 'solve'
    error_tol: float, optional
        tolerance for relative local error, default is 1e-1
    closeness_tol: float, optional
        tolerance for relative change in the closeness to the stationary distribution, default is 0.5
    step_size_min: float, optional
        minimum step size, default is 1e-14
    step_size_max: float, optional
        maximum step size, default is 10
    closeness_min: float, optional
        minimum closeness value, default is 1e-3
    factor_max: float, optional
        maximum factor for step size adaption, default is 2
    factor_safe: float, optional
        safety factor for step size adaption, default is 0.9
    second_method: string, optional
        which higher-order method should be used, can be 'two_step_Euler' or 'trapezoidal_rule', default is
        'two_step_Euler'

    Returns
    -------
    solution: list of instances of the TT class
        numerical solution of the differential equation
    """

    # define solution
    solution = [initial_value]

    # define variable for integration
    t_2 = []

    # set closeness variables
    closeness_pre = (operator @ initial_value).norm()

    # define tensor train for solving the systems of linear equations
    t_tmp = initial_guess

    # set time and step size
    time = 0
    step_size = step_size_first

    # begin integration
    # -----------------

    while (time < time_end) and (closeness_pre > closeness_min) and (step_size > step_size_min):

        # first method
        t_1 = sle.als(tt.eye(operator.row_dims) - step_size * operator, t_tmp.copy(), solution[-1], solver=solver,
                      repeats=repeats)
        t_1 = (1 / t_1.norm(p=1)) * t_1

        # second method
        if second_method == 'two_step_Euler':
            t_2 = sle.als(tt.eye(operator.row_dims) - 0.5 * step_size * operator, t_tmp.copy(), solution[-1],
                          solver=solver,
                          repeats=repeats)
            t_2 = sle.als(tt.eye(operator.row_dims) - 0.5 * step_size * operator, t_2.copy(), solution[-1],
                          solver=solver,
                          repeats=repeats)
        if second_method == 'trapezoidal_rule':
            t_2 = sle.als(tt.eye(operator.row_dims) - 0.5 * step_size * operator, t_tmp.copy(),
                          (tt.eye(operator.row_dims) + 0.5 * step_size * operator) @ solution[-1], solver=solver,
                          repeats=repeats)
        t_2 = (1 / t_2.norm(p=1)) * t_2

        # compute closeness to staionary distribution
        closeness = (operator @ t_1).norm()

        # compute relative local error and closeness change
        local_error = (t_1 - t_2).norm() / t_1.norm()
        closeness_difference = (closeness - closeness_pre) / closeness_pre

        # compute factors for step size adaption
        factor_local = error_tol / local_error
        factor_closeness = closeness_tol / np.abs(closeness_difference)

        # compute new step size
        step_size_new = np.amin([factor_max, factor_safe * factor_local, factor_safe * factor_closeness]) * step_size

        # accept or reject step
        if (factor_local > 1) and (factor_closeness > 1):
            time = time + step_size
            step_size = np.amin([step_size_new, time_end - time, step_size_max])
            solution.append(t_1.copy())
            t_tmp = t_1
            print('tau: ' + str("%.2e" % step_size) + ', closeness: ' + str("%.2e" % closeness))
            closeness_pre = closeness
        else:
            step_size = step_size_new

    return solution
