def merge_sort(units):
    if len(units) <= 1:
        return units

    mid = len(units) // 2

    left = merge_sort(units[:mid])
    right = merge_sort(units[mid:])

    return merge(left, right)


def merge(left, right):
    result = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):

        if left[i]["expiry_date"] <= right[j]["expiry_date"]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    return result