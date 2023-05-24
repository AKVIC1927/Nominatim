# SPDX-License-Identifier: GPL-3.0-or-later
#
# This file is part of Nominatim. (https://nominatim.org)
#
# Copyright (C) 2023 by the Nominatim developer community.
# For a full list of authors see the git log.
"""
Helper function for parsing parameters and and outputting data
specifically for the v1 version of the API.
"""

from nominatim.api.results import SearchResult, SearchResults, SourceTable

REVERSE_MAX_RANKS = [2, 2, 2,   # 0-2   Continent/Sea
                     4, 4,      # 3-4   Country
                     8,         # 5     State
                     10, 10,    # 6-7   Region
                     12, 12,    # 8-9   County
                     16, 17,    # 10-11 City
                     18,        # 12    Town
                     19,        # 13    Village/Suburb
                     22,        # 14    Hamlet/Neighbourhood
                     25,        # 15    Localities
                     26,        # 16    Major Streets
                     27,        # 17    Minor Streets
                     30         # 18    Building
                    ]


def zoom_to_rank(zoom: int) -> int:
    """ Convert a zoom parameter into a rank according to the v1 API spec.
    """
    return REVERSE_MAX_RANKS[max(0, min(18, zoom))]


def deduplicate_results(results: SearchResults, max_results: int) -> SearchResults:
    """ Remove results that look like duplicates.

        Two results are considered the same if they have the same OSM ID
        or if they have the same category, display name and rank.
    """
    osm_ids_done = set()
    classification_done = set()
    deduped = SearchResults()
    for result in results:
        if result.source_table == SourceTable.POSTCODE:
            assert result.names and 'ref' in result.names
            if any(_is_postcode_relation_for(r, result.names['ref']) for r in results):
                continue
        classification = (result.osm_object[0] if result.osm_object else None,
                          result.category,
                          result.display_name,
                          result.rank_address)
        if result.osm_object not in osm_ids_done \
           and classification not in classification_done:
            deduped.append(result)
        osm_ids_done.add(result.osm_object)
        classification_done.add(classification)
        if len(deduped) >= max_results:
            break

    return deduped


def _is_postcode_relation_for(result: SearchResult, postcode: str) -> bool:
    return result.source_table == SourceTable.PLACEX \
           and result.osm_object is not None \
           and result.osm_object[0] == 'R' \
           and result.category == ('boundary', 'postal_code') \
           and result.names is not None \
           and result.names.get('ref') == postcode
