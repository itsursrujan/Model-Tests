tuple = (10, 20, 30, 40 ,50)
"""
Tuples in Python - Comprehensive Documentation
OVERVIEW:
Tuples are immutable, ordered collections of elements in Python. Once created,
their contents cannot be modified, making them ideal for protecting data integrity.
KEY CHARACTERISTICS:
- Immutable: Cannot modify, add, or remove elements after creation
- Ordered: Elements maintain their position and can be accessed by index
- Heterogeneous: Can contain elements of different data types
- Iterable: Can be looped through
- Hashable: Can be used as dictionary keys (unlike lists)
BASIC OPERATIONS:
- Concatenation: Combine tuples using + operator
- Repetition: Repeat tuple contents using * operator
- Indexing: Access elements by position (0-based indexing)
- Slicing: Extract portions using slice notation [start:end:step]
TUPLE METHODS:
- count(value): Returns the number of occurrences of a value
- index(value): Returns the index of the first occurrence of a value
ADVANTAGES:
- Faster than lists due to immutability
- Can be used as dictionary keys
- Safer for data that shouldn't be modified
- Thread-safe operations
- Slightly lower memory overhead than lists
COMMON USE CASES:
- Function return values (multiple returns)
- Dictionary keys
- Protecting data structures passed between functions
- Unpacking values: a, b, c = (1, 2, 3)
- Fixed collections of related data
TUPLE UNPACKING:
tup = (1, 2, 3)
a, b, c = tup  # Unpack values
NESTED TUPLES:
nested = ((1, 2), (3, 4), (5, 6))
TYPE CHECKING:
isinstance(obj, tuple)  # Check if object is a tuple
"""
# tuple[0] = 100 // error, since tuples are immutable //

tup1 = (1, 2, 3, 4)
tup2 = (5, 6, 7, 8)
comb_tup = tup1 + tup2 # combines the tuple 1 and tuple 2
print(comb_tup) #(1, 2, 3, 4, 5, 6, 7, 8)

tuple_m = (1, 2, 3)
print(f"Tuple = {(tuple_m) * 3}") # (tuple_m * 3) multiplies the same tuple three times
# Indexing - Access elements by position
print(f"First element: {tuple[0]}")  # 10
print(f"Last element: {tuple[-1]}")  # 50

# Slicing - Extract portions of tuple
print(f"Slice [1:4]: {tuple[1:4]}")  # (20, 30, 40)
print(f"Slice [::2]: {tuple[::2]}")  # (10, 30, 50)

# Tuple methods
print(f"Count of 30: {tuple.count(30)}")  # 1
print(f"Index of 40: {tuple.index(40)}")  # 3

# Tuple unpacking
a, b, c, d, e = tuple
print(f"Unpacked: a={a}, b={b}, c={c}")  # a=10, b=20, c=30

# Length of tuple
print(f"Tuple length: {len(tuple)}")  # 5

# Check if element exists
print(f"20 in tuple: {20 in tuple}")  # True


