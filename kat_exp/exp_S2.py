from tqdm import tqdm
from utils import *
from prompts_kat import *
import pandas as pd

import json
json_file_path = '../cwe25.json'

df = pd.read_csv('vulC7_test.csv')

with open(json_file_path, 'r') as file:
    cwe25 = json.load(file)
    cwe_map = {item['id']: {'name': item['name'], 'description': item['description']} for item in cwe25}

#S2
for i in tqdm(range(df.shape[0])):
    res_before = inferSystemModel(promptS2(df.code_before.iloc[i], cwe_map.get(df['exp_cwe_id'].iloc[i][4:])['name']), "You are a helpful assistant.")
    res_after = inferSystemModel(promptS2(df.code_after.iloc[i], cwe_map.get(df['exp_cwe_id'].iloc[i][4:])['name']), "You are a helpful assistant.")
    
    df.at[i, 'res_before'] = res_before
    df.at[i, 'res_after'] = res_after

df.to_csv('kat_res/res_S2_llama3.csv', index=False)    