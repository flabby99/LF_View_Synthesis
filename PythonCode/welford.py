"""
This is adapted from wikipidea at
https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
it produces a mean and variance in one pass
"""


def update(existingAggregate, newValue):
    """
    # for a new value newValue, compute the new count, new mean, the new M2.
    # mean accumulates the mean of the entire dataset
    # M2 aggregates the squared distance from the mean
    # count aggregates the number of samples seen so far
    """
    (count, mean, M2) = existingAggregate
    count = count + 1
    delta = newValue - mean
    mean = mean + delta / count
    delta2 = newValue - mean
    M2 = M2 + delta * delta2

    return (count, mean, M2)

def finalize(existingAggregate):
    """
    # retrieve the mean, variance and sample variance from an aggregate
    """
    (count, mean, M2) = existingAggregate
    (mean, variance, sampleVariance) = (mean, M2/count, M2/(count - 1))
    if count < 2:
        return float('nan')
    else:
        return (mean, variance, sampleVariance)
