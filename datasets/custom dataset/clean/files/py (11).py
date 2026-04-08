n = int(input("Enter n: "))
stack = [0] * n
top = -1
size = n

while True:
    print(f"1: Push\n2:Pop\n3:peep\n4:Display\n5:Exit")
    choice = int(input("Enter Choice: "))
    
    if choice == 1:
        if top == size - 1:
            print("Stack is Full!")
        else:
            top += 1 
            stack[top] = int(input("Enter Element to stack: "))
            print(f"Pushed: {stack[top]} to the Stack")
        print()
        
    elif choice == 2:
        if top == -1:
            print("Stack is Empty")
        else: 
            x = stack[top]
            print(f"Popped element: {x}")
            top -= 1
        print()
    
    elif choice == 3:
        if top == -1:
            print("Stack is empty!!!")
        else:
            print(f"element at the top: {stack[top]}")
        print()
        
    elif choice == 4:
        if top == -1:
            print("Stack is empty no elements to display")
        else:
            for i in range(top,-1,-1):
                print(stack[i])
        print()
        
    elif choice == 5:
        print("Thank You")
        print()
        break
    else:
        print("Invalid Choice")


        
             
        

 