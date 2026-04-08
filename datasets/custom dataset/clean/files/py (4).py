list = ["A", "B", "C", "D", "E"]
list.pop()
print(f"pop(): {list}")
list.remove("C")
print(f"remove('C'): {list}")
list.append("E")
print(f"append('E'): {list}")
list.insert(2, "C")
print(f"insert(2,'C'): {list}")
list[0] = 1
print(f"list[0]: {list}")
print("-"*50)
L = [100, 200, 300, 400, 500, 600, 700]
print(L[0:-1])
print(L[0::2])
print(L[0:-1:2])
X = [900, 100, 500, 200, 600, 300, 400, 800, 700]
print(f"sorted(): {sorted(X)}\nX[unsorted]: {X}")
print(f"sum(X): {sum(X)}")
print("-"*50)
print("-"*50)
L1, L2 = [10, 20 ,30], [60, 50, 40]
L1.extend(L2)
print(L1)
print("Len: ",len(L1))

'''
1.pop() - removes the last element of the List
2.remove(value) - removes the specific element in the list
3.append(value) - inserts the element in the last 
4.insert(index, value) - inserts the element at a specific
5.sorted(List) - sorts the list in ascending order
6.reverse(List) - reverse the list in descending order
'''

'''
#12 Rotate a list to the left by 2 positions.
L = [10, 20, 30, 40, 50, 60] #30 40 50 60 10 20
n = len(L)
r = 8
r = r % n  # Handle cases where r >= n

temp = []

for i in range(r):
    temp.append(L[i])

for i in range(n - r):
    L[i] = L[i+r]     
  
for i in range(n - r,n):
    L[i] = temp[i - (n - r)]

print(L)

#13 Rotate a list to the right by 2 positions.
L = [10, 20, 30, 40, 50, 60] # 50 60 10 20 30 40
n = len(L)
r = 6
r = r % n # 8 % 6 = 2
temp = []
for i in range(n - r): # 6 - 2 = 4
    temp.append(L[i])

for i in range(n - r,n): # 2, 5
    L[i - (n - r)] = L[i]

for i in range(r, n):
    L[i] = temp[i - r]

print(L)
'''