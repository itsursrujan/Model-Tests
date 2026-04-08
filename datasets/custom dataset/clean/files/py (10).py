n = int(input("Enter n: "))
queue = [0] * n
front, rear = -1, -1
size = n

while True:
    print("\n1.Enqueue\n2.Dequeue\n3.Display\n4.Exit")
    choice = int(input("Enter Choice: "))

    if choice == 1:
        if rear == size - 1:
            print("Queue is Full!!!")
        else:
            if front == -1:   # first element
                front = 0
            rear += 1
            x = int(input("Enter Element: "))
            queue[rear] = x
            print(f"Enqueued '{x}' to the Queue")

    elif choice == 2:
        if front == -1 or front > rear:
            print("Queue is Empty!!!")
        else:
            x = queue[front]
            print(f"Dequeued '{x}' from the Queue")
            front += 1

            if front > rear:   # reset queue
                front = rear = -1

    elif choice == 3:
        if front == -1 or front > rear:
            print("Queue is Empty")
        else:
            print("Queue elements:")
            for i in range(front, rear + 1):
                print(queue[i], end=" ")
            print()

    elif choice == 4:
        print("Thank You")
        break

    else:
        print("Invalid Choice")