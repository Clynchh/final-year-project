from datetime import date

start = date(2019, 12, 1)
end = date(2023, 5, 1)

current = start

while current <= end:
    month_name = current.strftime("%b")
    
    filename = f"{month_name} {current.year}.txt"

    with open(filename, "w"):
        pass 
 
    if current.month == 12:
        current = date(current.year + 1, 1, 1)
    else:
        current = date(current.year, current.month + 1, 1)
