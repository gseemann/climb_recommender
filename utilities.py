import datetime
import matplotlib.pyplot as plt
import pandas as pd
from math import ceil, sqrt
import functools
import numpy as np
import collections
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor

def compose(*funcs):
    outer = funcs[:-1][::-1] # Python only provides left folds
    def composed_func(*args, **kwargs):
        inner = funcs[-1](*args, **kwargs)
        return functools.reduce(lambda val, func : func(val), outer, inner)
    return composed_func

# Aliases for filters
lfilter       = compose(list, filter)
lmap          = compose(list, map)
afilter       = compose(np.array, list, filter)
filternull    = functools.partial(filter, None)
filternullmap = compose(filternull, map)

def drop_col(df, col):
    df.drop(col, axis = 'columns', inplace = True)


# Super simple timer
#  Timing implemented as class methods
#  to avoid having to instantiate
class Timer:

    @classmethod
    def start(cls):
        cls.start_time = datetime.datetime.now()

    @classmethod
    def end(cls):
        delta = datetime.datetime.now() - cls.start_time
        sec = delta.seconds
        ms  = delta.microseconds // 1000
        print(f'{sec}.{ms} seconds elapsed')


class FeaturePlot:
    '''
        Manages a figure containing plots of many unrelated variables
        To use: this is an iterable that will yield (col_name, data, axis)
        for each variable it contains
    '''
    def __init__(self, *data):
        self.data     = pd.concat(data, axis = 'columns')
        self.columns  = self.data.columns
        self.num_cols = len(self.columns)
        self._make_figure()

    def clone(self):
        return FeaturePlot(self.data)

    def _make_figure(self):
        '''
           Makes the main figure
        '''

        # Compute the size and get fig, axes
        s = ceil(sqrt(self.num_cols))
        fig, axes = plt.subplots(s, s, figsize = (4*s, 4*s));
        axes = axes.ravel()

        # Delete excess axes
        to_delete = axes[self.num_cols:]
        for ax in to_delete:
            ax.remove()

        # Retain references
        self.fig  = fig
        self.axes = dict(zip(self.columns, axes))

        # Add titles
        for col, ax in self.axes.items():
            ax.set_title(col)

        self.grid_size = s

    def overlay(self, label, sharex = False, sharey = False):
        '''
            Adds a new layer of axes on top of an existing figure

            - Is a generator in similar style to self.__iter__ below.
            - A reference to the newly created axes is not maintained
                 by the class - the axes are intended to be single use.
                 If you want to access the axes later, either use the
                 matplotlib figure object or retain a reference
        '''
        for index, col in enumerate(self.columns):
            base_ax = self.axes[col]
            ax = self.fig.add_subplot(self.grid_size, self.grid_size, index + 1,
                                      sharex = base_ax if sharex else None,
                                      sharey = base_ax if sharey else None,
                                      label  = label,
                                      facecolor = 'none')

            for a in [ax, base_ax]:
                if not sharex:
                    a.tick_params(bottom = False,
                                  top = False,
                                  labelbottom = False,
                                  labeltop    = False)
                if not sharey:
                    a.tick_params(left = False,
                                  right = False,
                                  labelleft = False,
                                  labelright = False)


            yield col, self.data[col].values, ax

    def __iter__(self):
        for col in self.columns:
            yield col, self.data[col].values, self.axes[col]

def plot(fn, *args, **kwargs):
    if 'figsize' in kwargs:
        fig, ax = plt.subplots(figsize = kwargs['figsize'])
        del kwargs['figsize']
    else:
        fig, ax = plt.subplots()
    kwargs['ax'] = ax
    fn(*args, **kwargs)
    return fig

def drop_by_rule(df, bool_series):
    index = df[bool_series].index
    df.drop(index = index, inplace = True)

# Simple class to keep track of our model
class Model:

    def __init__(self, y, X_cat, X_cont, interactions = []):
        self.y = y
        self.X_cat = X_cat.copy()
        self.X_cont = X_cont.copy()
        self.interactions = interactions.copy()

    def formula(self, include_cat = True, include_cont = True,
                      include_interactions = True, dv = None,
                      order = ['cat', 'cont', 'interactions']):
        if not dv:
            dv = self.y
        xvars = collections.defaultdict(lambda : [])
        if include_cat:
            xvars['cat']          = self._wrap_cat()
        if include_cont:
            xvars['cont']         = self.X_cont
        if include_interactions:
            xvars['interactions'] = self._wrap_interactions()

        xvars = sum(map(lambda type_ : xvars[type_], order), [])

        return dv + ' ~ ' + ' + '.join(xvars)

    def remove_var(self, *vars_):
        for var in vars_:
            success = False
            for list_ in [self.X_cat, self.X_cont, self.interactions]:
                try:
                    list_.remove(var)
                    success = True
                except ValueError:
                    pass
            if not success:
                print(f'Variable {var} not previously in the model')

    def add_cat_var(self, var):
        self.X_cat.append(var)

    def add_cont_var(self, var):
        self.X_cont.append(var)

    def add_interaction(self, *vars_, sep = '*'):
        if len(vars_) == 1:
            self.interactions.append(vars_[0])
        else:
            self.interactions.append(sep.join(vars_))

    def set_baseline(self):
        self.baseline = self.y, self.X_cat.copy(), self.X_cont.copy(), self.interactions.copy()

    def reset_to_baseline(self):
        self.y, self.X_cat, self.X_cont, self.interactions = self.baseline

    def _wrap_cat(self):
        return lmap(lambda var : f'C({var})', self.X_cat)

    def _wrap_interactions(self):
        return lmap(self._wrap_interaction, self.interactions)

    def _split_interaction(self, var):
        if '*' in var:
            split_on = '*'
        elif ':' in var:
            split_on = ':'
        else:
            raise ValueError(f'Not sure how to find the interaction in {var}')

        vars_ = var.split(split_on)
        return vars_, split_on

    def _wrap_interaction(self, var):
        vars_, split_on = self._split_interaction(var)
        vars_ = map(lambda var : f'C({var})' if var in self.X_cat else var, vars_)
        return split_on.join(vars_)

    def get_continuous_interactions(self):
        def is_cont_interaction(interaction):
            vars_, _ = self._split_interaction(interaction)
            for var in vars_:
                if var in self.X_cat:
                    return None
            return interaction
        return filternullmap(is_cont_interaction, self.interactions)


    def clone_as_baseline(self):
        out = Model(self.y, self.X_cat, self.X_cont, self.interactions)
        out.set_baseline()
        return out

# Modified from the Seaborn Gallery
# https://seaborn.pydata.org/examples/many_pairwise_correlations.html
def correlation_matrix(data):
    # Compute the correlation matrix
    corr = data.corr()

    # Generate a mask for the upper triangle
    mask = np.zeros_like(corr, dtype=np.bool)
    mask[np.triu_indices_from(mask)] = True

    # Set up the matplotlib figure
    fig, ax = plt.subplots(figsize=(11, 9))

    # Generate a custom diverging colormap
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .5}, ax = ax)

    return fig

def vif_table(df_x):
    return pd.Series({
        var_name : variance_inflation_factor(df_x.dropna().values, i)
        for i, var_name in enumerate(df_x.columns)
    }).sort_values(ascending = False)
