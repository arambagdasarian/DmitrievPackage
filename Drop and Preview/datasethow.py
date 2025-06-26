import csv
import sys

csv.field_size_limit(sys.maxsize)

with open('output.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    row_count = sum(1 for _ in reader)

print(f"Total number of rows (including header): {row_count}")
