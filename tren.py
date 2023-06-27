alist = list(map(int, input().split()))
count = 0
i = 0
while i + 1 < len(alist):
    if not (alist[i] + alist[i + 1]):

    i += 1
print(count)