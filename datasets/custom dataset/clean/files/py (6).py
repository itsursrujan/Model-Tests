def palindrome():
    s = input("Enter STring:")
    l = len(s)
    flag = 0
    for i in range(l//2):
        if s[i] == s[l - 1 -i]:
            flag = 1
    
    if flag == 1: print("pALI")
    else:print('not pali')