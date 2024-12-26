#
#
# jj = {'asfdsf':'asfdsf','asdfdfs':'asfasdf'}
#
# print(jj)
# import json
# jjj = json.dumps(jj)
# print(jjj)






import json

obj = {'name': 'John', 'age': 30, 'city': 'New York', 'city1': ['New York','afasd']}

# for i in range(10):
#     print(json.dumps(obj, indent=i))



print(json.dumps(obj, indent=4))







