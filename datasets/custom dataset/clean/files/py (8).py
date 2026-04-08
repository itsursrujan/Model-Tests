n = 100

print("Prime Numbers:")

def get_prime():
    for i in range(1,n):
        count = 0
        for j in range(1,n):
            if i % j == 0:
                count+=1
        
        if count == 2:
            print(f"{i} ")

get_prime()
