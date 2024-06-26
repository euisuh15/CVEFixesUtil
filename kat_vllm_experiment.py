import subprocess
import time
import argparse
import os
import json
from utils import *
from prompts_kat import *
import pandas as pd
import torch


def expS1(df, cwe_map, model, prefix=""):
    prompts_before = [
        promptS1(
            df.func_before.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]
    prompts_after = [
        promptS1(
            df.func_after.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]

    prompts = prompts_before + prompts_after

    res10 = inferModelVllm(model[1], prompts)

    res_before = []
    res_after = []

    n = len(res10)
    res_df = pd.DataFrame(
        {
            "id": range(n // 2),
            "res_before": res10[: n // 2],
            "res_after": res10[n // 2 :],
        }
    )

    res_df.to_csv(f"kat_res/{prefix}res_S1_{model[0]}.csv", index=False)


def expS2(df, cwe_map, model, prefix=""):
    prompts_before = [
        promptS2(
            df.func_before.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]
    prompts_after = [
        promptS2(
            df.func_after.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]

    prompts = prompts_before + prompts_after

    sys = "You are a helpful assistant."

    res10 = inferSystemModelVllm(model[1], prompts, sys)

    res_before = []
    res_after = []

    n = len(res10)
    res_df = pd.DataFrame(
        {
            "id": range(n // 2),
            "res_before": res10[: n // 2],
            "res_after": res10[n // 2 :],
        }
    )

    res_df.to_csv(f"kat_res/{prefix}res_S2_{model[0]}.csv", index=False)


def expS3(df, cwe_map, model, prefix=""):
    prompts_before = [
        promptS3(
            df.func_before.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]
    prompts_after = [
        promptS3(
            df.func_after.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]

    prompts = prompts_before + prompts_after

    sys = "You are a code security expert."

    res10 = inferSystemModelVllm(model[1], prompts, sys)

    res_before = []
    res_after = []

    n = len(res10)
    n = len(res10)
    res_df = pd.DataFrame(
        {
            "id": range(n // 2),
            "res_before": res10[: n // 2],
            "res_after": res10[n // 2 :],
        }
    )

    res_df.to_csv(f"kat_res/{prefix}res_S3_{model[0]}.csv", index=False)


def expR1(df, cwe_map, model, prefix=""):
    prompts_before = [
        promptR1(
            df.func_before.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]
    prompts_after = [
        promptR1(
            df.func_after.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]

    prompts = prompts_before + prompts_after

    res10 = inferModelVllm(model[1], prompts)

    res_before = []
    res_after = []

    n = len(res10)
    res_df = pd.DataFrame(
        {
            "id": range(n // 2),
            "res_before": res10[: n // 2],
            "res_after": res10[n // 2 :],
        }
    )

    res_df.to_csv(f"kat_res/{prefix}res_R1_{model[0]}.csv", index=False)


def expR2(df, cwe_map, model, prefix=""):
    prompts_before = [
        promptR1(
            df.func_before.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]
    prompts_after = [
        promptR1(
            df.func_after.iloc[i], cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"]
        )
        for i in range(df.shape[0])
    ]

    prompts = prompts_before + prompts_after

    sys = [
        f"You are a code security expert who analyzes the given code for the security vulnerability known as {cwe_map.get(df['exp_cwe_id'].iloc[i//2][4:])['name']} following these four steps:\n1. First you describe the overview of the code\n2. Then based on the overview you identify the sub-components in code that could lead to {cwe_map.get(df['exp_cwe_id'].iloc[i//2][4:])['name']}\n3. After that you do a detailed analysis of the identified sub-components for the existence of the {cwe_map.get(df['exp_cwe_id'].iloc[i//2][4:])['name']}\n4. Based on the detailed analysis you decide and answer whether the {cwe_map.get(df['exp_cwe_id'].iloc[i//2][4:])['name']} is present in the given code or not"
        for i in range(df.shape[0] * 2)
    ]

    res10 = inferSystemModelVllm(model[1], prompts, sys)

    res_before = []
    res_after = []

    n = len(res10)
    res_df = pd.DataFrame(
        {
            "id": range(n // 2),
            "res_before": res10[: n // 2],
            "res_after": res10[n // 2 :],
        }
    )

    res_df.to_csv(f"kat_res/{prefix}res_R2_{model[0]}.csv", index=False)


def expD1(df, cwe_map, model, prefix=""):
    prompts_before = [
        promptD1(
            df.func_before.iloc[i],
            cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"],
            cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["description"],
        )
        for i in range(df.shape[0])
    ]
    prompts_after = [
        promptD1(
            df.func_after.iloc[i],
            cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"],
            cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["description"],
        )
        for i in range(df.shape[0])
    ]

    prompts = prompts_before + prompts_after

    res10 = inferModelVllm(model[1], prompts)

    res_before = []
    res_after = []

    n = len(res10)
    res_df = pd.DataFrame(
        {
            "id": range(n // 2),
            "res_before": res10[: n // 2],
            "res_after": res10[n // 2 :],
        }
    )

    res_df.to_csv(f"kat_res/{prefix}res_D1_{model[0]}.csv", index=False)


def expD2(df, cwe_map, model, prefix=""):
    prompts_before = [
        promptD2(
            df.func_before.iloc[i],
            cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"],
            cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["description"],
        )
        for i in range(df.shape[0])
    ]
    prompts_after = [
        promptD2(
            df.func_after.iloc[i],
            cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["name"],
            cwe_map.get(df["exp_cwe_id"].iloc[i][4:])["description"],
        )
        for i in range(df.shape[0])
    ]

    prompts = prompts_before + prompts_after

    sys = [
        f"You are a code security expert who analyzes the given code for the security vulnerability known as {cwe_map.get(df['exp_cwe_id'].iloc[i//2][4:])['name']}.\n\n{cwe_map.get(df['exp_cwe_id'].iloc[i//2][4:])['description']}"
        for i in range(df.shape[0] * 2)
    ]

    res10 = inferSystemModelVllm(model[1], prompts, sys)

    res_before = []
    res_after = []

    n = len(res10)
    res_df = pd.DataFrame(
        {
            "id": range(n // 2),
            "res_before": res10[: n // 2],
            "res_after": res10[n // 2 :],
        }
    )

    res_df.to_csv(f"kat_res/{prefix}res_D2_{model[0]}.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description="Process command line arguments.")

    parser.add_argument(
        "--cuda-visible-devices",
        dest="cuda_visible_devices",
        type=int,
        help="Index of the CUDA visible device",
    )
    parser.add_argument(
        "--experiment-name", dest="experiment_name", type=str, help="Experiment name"
    )
    parser.add_argument("--model", dest="model_name", type=str, help="Model name")
    parser.add_argument("--model-path", dest="model_path", type=str, help="Model path")
    parser.add_argument("--prefix", dest="prefix", type=str, help="Prefix")

    args = parser.parse_args()

    experiment_name = args.experiment_name
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.cuda_visible_devices)

    with open("assets/cwe25.json", "r") as file:
        cwe25 = json.load(file)
        cwe_map = {
            item["id"]: {"name": item["name"], "description": item["description"]}
            for item in cwe25
        }

    df = pd.read_csv("assets/vulC7_test.csv")

    model = (args.model_name, args.model_path)

    if experiment_name == "R1":
        expR1(df, cwe_map, model, args.prefix)
    elif experiment_name == "R2":
        expR2(df, cwe_map, model, args.prefix)

    elif experiment_name == "S1":
        expS1(df, cwe_map, model, args.prefix)
    elif experiment_name == "S2":
        expS2(df, cwe_map, model, args.prefix)
    elif experiment_name == "S3":
        expS3(df, cwe_map, model, args.prefix)

    elif experiment_name == "D1":
        expD1(df, cwe_map, model, args.prefix)
    elif experiment_name == "D2":
        expD2(df, cwe_map, model, args.prefix)

    print(f"Compmleted model inference for {args.model_name}")


if __name__ == "__main__":
    main()
