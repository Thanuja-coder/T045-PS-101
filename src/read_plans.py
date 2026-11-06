import csv

with open('D:\\Capstone Project_10 seconds\\T045-PS-101\\data\\plans.csv','r',newline="")as file:
    reader=csv.DictReader(file)
    for row in reader:
        print(row)
