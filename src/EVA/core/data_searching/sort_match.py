def sort_match(results: list[dict]) -> dict:
    """
    Finds top 6 most frequently occurring elements in the input list of dictionaries.

    Args:
        results: list of result dictionaries

    Returns:
        Dict of length 6, ordered by frequency. Dict key is element name, value is number of occurrences.
    """

    peaks = {}
    counts = {}

    # sorts all transitions by peaks and keeps track of which elements are found for each peak
    for line in results:
        # create dictionary key if energy has not been seen previously
        if not line["peak_centre"] in peaks.keys():
            peaks[line["peak_centre"]] = []

        # create dictionary key if element has not been seen previously
        if not line["element"] in counts.keys():
            counts[line["element"]] = 0

        if line["element"] not in peaks[line["peak_centre"]]:
            peaks[line["peak_centre"]].append(line["element"])
            # if this element has not previously been detected for this peak, increment peak count for that element
            counts[line["element"]] += 1

    # Sort counts starting with highest count
    counts = {k: v for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)}

    # Return top 8 results
    return dict(list(counts.items())[0:7])
