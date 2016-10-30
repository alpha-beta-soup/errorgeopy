"""Contains the :code:`Address` class, representing a collection of reverse
geocoding results. Primarily, this functions as a container for a set of
:code:`errorgeopy.Location` objects after a successful reverse geocode, and
exposes methods that operate on this set of results, including:

- de-duplication
- extracting the results that best match a pre-expected outcome
- finding the longest common substring of candidate addresses

.. moduleauthor Richard Law <richard.m.law@gmail.com>
"""

# import usaddress
from fuzzywuzzy import process as fuzzyprocess

from errorgeopy.utils import (long_substr, check_location_type,
                              check_addresses_exist)

from functools import wraps


class Address(object):
    """Represents a collection of parsed reverse geocoder responses (parsed with
    geopy). Each member of the :code:`address` property (which is iterable) is a
    :code:`geopy.address` object. The raw respones can therefore be obtained
    with:

        >>> [a.raw for a in Address.addresses]

    :code:`errorgeopy` adds methods that operate on the collection of addresses
    that consider the set of addresses as a related set.

    Attributes:
        :code:`addresses` (:code:`list`): Collection of reverse geocoding
        responses from as many services that were capable of returning a
        response to a query.  Each member of the array is a
        :code:`geopy.location.Location` object.
    """

    @check_location_type
    def __init__(self, addresses):
        self._addresses = addresses or None

    def __unicode__(self):
        return '\n'.join([str(a) for a in self.addresses])

    def __str__(self):
        return self.__unicode__()

    @property
    def addresses(self):
        """A list of reverse geocoding results from all configured providers.
        The single central property of the Address object.

        Notes:
            Depending on configuration, a provider may return more than one
            result for a given query. All results from all providers are
            available in this property, in a *flat* (not nested) structure.
            The list may be empty if no provider could match an address.
        """
        return self._addresses if self._addresses else []

    @check_addresses_exist
    def dedupe(self, threshold=95):
        """dedupe(threshold=95)
        Produces a fuzzily de-duplicated version of the candidate addresses,
        using :code:`fuzzywuzzy.proccess.dedupe`.

        Note:
            See https://github.com/seatgeek/fuzzywuzzy/blob/master/fuzzywuzzy/process.py
            for detail on the deduplication algorithm implementation. This
            method does not modify the :code:`Address.addresses`. property.

        Kwargs:
            threshold (int): the numerical value (0,100) point at which you
            expect to find duplicates. Defaults to 95 out of 100, which is
            higher than the fuzzywuzzy default (70); this higher threshold is
            used by defauly since addresses are more sensitive to small changes
            (e.g. "250 Main Street" and "150 Main Street" have a small edit
            distance when considered as strings, but may have a reasonably large
            physical distance when considered as physical addresses).
        Returns:
            A list of :code:`geopy.location.Location` objects (essentially a
            filtered list of the original set).
        """
        return fuzzyprocess.dedupe([str(a) for a in self.addresses], threshold)

    @check_addresses_exist
    def longest_common_substring(self, dedupe=False):
        """longest_common_substring(dedupe=False)
        Returns the longest common substring of the reverse geocoded
        addresses. Note that if there is no common substring, a string of length
        zero is returned. If the longest common substring is whitespace, that is
        stripped, and a string of length zero is returned.

        Kwargs:
            dedupe (bool): whether to first perform a deduplication operation on
            the set of addresses. Defaults to False.

        Returns:
            str
        """
        addresses = self.addresses if not dedupe else self.dedupe()
        return long_substr([str(a) for a in addresses])

    @check_addresses_exist
    def longest_common_sequence(self, separator=' '):
        """longest_common_sequence(separator='')
        Returns the longest common sequence of the reverse geocoded
        addresses... or it would, if I had written this code.
        Raises:
            NotImplementedError
        """
        # return utils.longest_common_sequence([str(a) for a in self.addresses],
        #                                      separator)
        raise NotImplementedError

    @check_addresses_exist
    def regex(self):
        """regex()
        Returns a regular expression that matches all of the reverse geocoded
        addresses... well it would if I had written this code.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError

    @check_addresses_exist
    def extract(self, expectation, limit=4):
        """extract(extraction, limit=4)
        Returns the address or addresses within the set of the reverse
        geocoded addresses that best match an expected result. Uses fuzzywuzzy
        under the hood for matching.

        Args:
            expectation (str): The string indicating your expected result for a
            reverse geocoding operation. It should probably look like an
            address. Results are returned in the order that best meets this
            expected address.

        Kwargs:
            limit (int): The maximum number of match candidates to retrieve
            from fuzzywuzzy. The length of the returned array may be longer, if
            the set of addresses has identical addresses that are good matches
            for the expected address (i.e. if two geocoders resolve to the same
            string address).

        Returns:
            list. Return value is a list of tuples, where each tuple contains a
            geopy Location, and a matching score based on an extension of the
            Levenshtien distance between the expectation and the Location's
            address (a higher score is a better match). The algorithm is
            implemented by SeatGeek's fuzzywuzzy, and you can read more here:
            http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/
        """
        extractions = fuzzyprocess.extractBests(
            expectation, [str(a) for a in self.addresses],
            limit=limit)
        result = []
        for extraction in extractions:
            result.extend([(x, extraction[1]) for x in self.addresses
                           if str(x) == extraction[0]])
        return result

    @check_addresses_exist
    def parse(self):
        """parse()
        Raises:
            NotImplementedError
        """
        # return [usaddress.parse(str(a)) for a in self.addresses]
        raise NotImplementedError

    @check_addresses_exist
    def tag(self, summarise=True):
        """tag(summarise=True)
        Raises:
            NotImplementedError
        """
        # tagged_addresses = [usaddress.tag(str(a)) for a in self.addresses]
        # if not summarise:
        #     return tags
        # summarised_tags = OrderedDict()
        # for address in tagged_addresses[0]:
        #     for k, v in address.items():
        #         if k not in summarised_tags:
        #             summarised_tags[k] = set([v])
        #         else:
        #             summarised_tags[k] = summarised_tags[k].add(v)
        # return summarised_tags, set([a[1] for a in tagged_addresses])
        raise NotImplementedError
