from tools.catalog import list_learning_goals, get_learning_goal, search_learning_goals

print(list_learning_goals())                      # success + data
print(list_learning_goals(access_token="bad"))    # permission error
print(get_learning_goal("phonics-short-a"))       # success + object
print(get_learning_goal("nope"))                  # business error (not empty success)
print(search_learning_goals("zzzz"))              # success + goals=[]  ← valid empty
print(search_learning_goals("zzzz", access_token="bad"))  # permission error