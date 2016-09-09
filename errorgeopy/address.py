# import usaddress
from fuzzywuzzy import process as fuzzyprocess

from errorgeopy import utils


def check_addresses_exist(func):
    '''
    Decorator for checking that the first argument of a function has an
    addresses property
    '''

    def inner(*args, **kwargs):
        if not args[0].addresses:
            return None
        else:
            return func(*args, **kwargs)

    return inner


class Address(object):
    @utils.check_location_type
    def __init__(self, addresses):
        self._addresses = addresses or None

    def __unicode__(self):
        return '\n'.join([str(a) for a in self.addresses])

    def __str__(self):
        return self.__unicode__()

    @property
    def addresses(self):
        return self._addresses if self._addresses else []

    @check_addresses_exist
    def dedupe(self, threshold=95):
        '''
        Returns a de-duplicated version of the candidate addresses, using
        fuzzywuzzy.proccess.dedupe.

        See https://github.com/seatgeek/fuzzywuzzy/blob/master/fuzzywuzzy/process.py#L222
        '''
        return fuzzyprocess.dedupe([str(a) for a in self.addresses], threshold)

    @check_addresses_exist
    def longest_common_substring(self):
        '''Returns the longest common substring of the reverse geocoded
        addresses. Note that if there is no common substring, a string of length
        zero is returned. If the longest common substring is whitespace, that is
        stripped, and a string of length zero is returned.'''
        return utils.long_substr([str(a) for a in self.addresses])

    @check_addresses_exist
    def longest_common_sequence(self, separator=' '):
        # return utils.longest_common_sentence([str(a) for a in self.addresses],
        #                                      separator)
        raise NotImplementedError

    @check_addresses_exist
    def regex(self):
        '''Returns a regular expression that matches all addresses'''
        raise NotImplementedError

    @check_addresses_exist
    def extract(self, expectation, limit=4):
        '''
        Following a reverse geocode against multipe providers, return results
        that best match an expected result.

        Return value is a list of tuples, where each tuple contains a geopy
        Location, and a matching score based on an extension of the Levenshtien
        (edit) distance between the :expectation: and the Location's address (a
        higher score is a better match). The algorithm is implemented by
        fuzzywuzzy, and you can read more here:
        http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/

        :param string expectation: An expectation of an address.

        :param int limit: The maximum number of match candidates to retrieve
        from fuzzywuzzy. The length of the returned array may be longer, if
        Locations encapsulated by self have identical addresses that are good
        matches for :expectation: (e.g. if two geocoders resolve to the same
        string address).
        '''
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
        # return [usaddress.parse(str(a)) for a in self.addresses]
        raise NotImplementedError

    @check_addresses_exist
    def tag(self, summarise=True):
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
